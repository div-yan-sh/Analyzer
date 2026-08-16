import csv
import json
import base64
from datetime import datetime, timedelta
from io import StringIO, BytesIO
from flask import Blueprint, request, jsonify, session, Response
from database.db import db
from database.models import Expense, Budget, FinancialGoal, AIInsight, User, ReceiptScan
from routes.auth_routes import login_required
from services.gemini_service import (
    generate_ai_chat_response, 
    generate_ai_monthly_report, 
    scan_receipt_with_gemini, 
    parse_voice_expense_text
)

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

ai_bp = Blueprint('ai', __name__)

def get_user_data_context(user_id):
    """
    Assembles a safe context dictionary summarizing user expenses, budgets, 
    predictions, and goals, to feed to Gemini or local analytics.
    """
    user = User.query.get(user_id)
    now = datetime.now()
    start_date = datetime(now.year, now.month, 1).date()
    if now.month == 12:
        end_date = datetime(now.year + 1, 1, 1).date()
    else:
        end_date = datetime(now.year, now.month + 1, 1).date()

    expenses = Expense.query.filter_by(user_id=user_id).all()
    curr_month_expenses = [e for e in expenses if start_date <= e.expense_date < end_date]
    
    # Calculate category stats
    cats = {}
    for e in curr_month_expenses:
        cats[e.category] = cats.get(e.category, 0.0) + e.amount
    cats = {k: round(v, 2) for k, v in cats.items()}

    # Get budget
    overall_budget = Budget.query.filter_by(user_id=user_id, month=now.month, year=now.year, category=None).first()
    budget_val = overall_budget.amount if overall_budget else 0.0

    # Predictions & Daily average
    from ml.preprocessing import expenses_to_df, get_daily_average
    from ml.spending_prediction import predict_current_month_end
    
    df_all = expenses_to_df(expenses)
    df_curr = expenses_to_df(curr_month_expenses)
    
    daily_avg = get_daily_average(df_curr, days=now.day)
    pred, _, _ = predict_current_month_end(expenses, budget_val)

    # Goals
    goals = FinancialGoal.query.filter_by(user_id=user_id).all()
    active_goals = [
        {
            "title": g.title, 
            "target": g.target_amount, 
            "current": g.current_amount, 
            "deadline": g.deadline.strftime("%Y-%m-%d")
        } for g in goals if g.status == 'active'
    ]

    # Recent list
    recent_exp = [
        {
            "amount": e.amount, 
            "category": e.category, 
            "description": e.description, 
            "date": e.expense_date.strftime("%Y-%m-%d")
        } for e in curr_month_expenses[-10:]
    ]

    return {
        "student_name": user.name if user else "Student",
        "college": user.college if user else "",
        "course": user.course if user else "",
        "allowance": user.monthly_income_or_allowance if user else 0.0,
        "current_month_spent": sum(e.amount for e in curr_month_expenses),
        "current_budget": budget_val,
        "category_breakdown": cats,
        "daily_average": daily_avg,
        "predicted_spend": pred,
        "active_goals": active_goals,
        "recent_expenses": recent_exp
    }

# ----------------- AI Chat & Reports -----------------

@ai_bp.route('/api/ai/chat', methods=['POST'])
@login_required
def chat():
    user_id = session['user_id']
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    history = data.get('history', [])

    if not message:
        return jsonify({"error": "Message is required."}), 400

    context = get_user_data_context(user_id)
    response_text = generate_ai_chat_response(history, context, message)
    return jsonify({"response": response_text}), 200

@ai_bp.route('/api/ai/monthly-report', methods=['POST'])
@login_required
def get_monthly_report():
    user_id = session['user_id']
    context = get_user_data_context(user_id)
    report = generate_ai_monthly_report(context)

    try:
        insight = AIInsight(
            user_id=user_id,
            title=f"AI Report — {datetime.now().strftime('%B %Y')}",
            content=json.dumps(report),
            insight_type="prediction"
        )
        db.session.add(insight)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Failed to save AI report insight: {e}")

    return jsonify(report), 200

@ai_bp.route('/api/ai/download-report', methods=['GET'])
@login_required
def download_pdf_report():
    user_id = session['user_id']
    context = get_user_data_context(user_id)
    
    latest_report_insight = AIInsight.query.filter_by(
        user_id=user_id, 
        insight_type="prediction"
    ).order_by(AIInsight.created_at.desc()).first()

    if latest_report_insight:
        try:
            report_data = json.loads(latest_report_insight.content)
        except Exception:
            report_data = generate_ai_monthly_report(context)
    else:
        report_data = generate_ai_monthly_report(context)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=15
    )
    section_style = ParagraphStyle(
        'SecTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2563EB'),
        spaceBefore=10,
        spaceAfter=5
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#334155')
    )

    story.append(Paragraph(f"Student Expense Intelligence Report", title_style))
    story.append(Paragraph(f"<b>Student:</b> {context['student_name']} | <b>College:</b> {context['college']}", body_style))
    story.append(Paragraph(f"<b>Generated On:</b> {datetime.now().strftime('%B %d, %Y')}", body_style))
    story.append(Spacer(1, 15))

    table_data = [
        [Paragraph("<b>Financial Metric</b>", body_style), Paragraph("<b>Value</b>", body_style)],
        [Paragraph("Monthly Allowance", body_style), Paragraph(f"₹{context['allowance']:.2f}", body_style)],
        [Paragraph("Spent So Far", body_style), Paragraph(f"₹{context['current_month_spent']:.2f}", body_style)],
        [Paragraph("Set Budget Limit", body_style), Paragraph(f"₹{context['current_budget']:.2f}", body_style)],
        [Paragraph("Daily Average Spending", body_style), Paragraph(f"₹{context['daily_average']:.2f}", body_style)],
        [Paragraph("Projected End of Month", body_style), Paragraph(f"₹{context['predicted_spend']:.2f}", body_style)],
    ]
    t = Table(table_data, colWidths=[200, 200])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    story.append(Paragraph("AI Executive Summary", section_style))
    story.append(Paragraph(report_data.get('summary', 'No summary available.'), body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Key Observations", section_style))
    for obs in report_data.get('key_observations', []):
        story.append(Paragraph(f"• {obs}", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Financial Warnings", section_style))
    for warn in report_data.get('warnings', []):
        story.append(Paragraph(f"• <font color='red'>{warn}</font>", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Recommended Saving Actions", section_style))
    for rec in report_data.get('recommendations', []):
        story.append(Paragraph(f"• {rec}", body_style))

    doc.build(story)
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    filename = f"Student_Expense_Report_{datetime.now().strftime('%b_%Y')}.pdf"
    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

# ----------------- AI Smart Receipt Scanner Endpoint -----------------

@ai_bp.route('/api/ai/scan-receipt', methods=['POST'])
@login_required
def scan_receipt():
    """
    Accepts multipart/form-data with file or JSON with base64 data,
    processes with Gemini Multimodal Vision model, and returns extracted receipt fields.
    """
    user_id = session['user_id']
    image_bytes = None
    mime_type = "image/jpeg"

    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            image_bytes = file.read()
            mime_type = file.mimetype or "image/jpeg"
    elif request.is_json:
        data = request.get_json() or {}
        b64_data = data.get('image_base64', '')
        if b64_data:
            if ',' in b64_data:
                header, b64_data = b64_data.split(',', 1)
                if 'image/png' in header:
                    mime_type = 'image/png'
                elif 'image/webp' in header:
                    mime_type = 'image/webp'
            try:
                image_bytes = base64.b64decode(b64_data)
            except Exception:
                image_bytes = None

    # Process receipt with Gemini Vision OCR
    extracted_data = scan_receipt_with_gemini(image_bytes, mime_type)

    # Save to ReceiptScan history
    try:
        scan_record = ReceiptScan(
            user_id=user_id,
            merchant=extracted_data.get('merchant', 'Unknown Store'),
            total_amount=float(extracted_data.get('total_amount', 0.0)),
            category=extracted_data.get('category', 'Other'),
            date=datetime.strptime(extracted_data.get('date'), '%Y-%m-%d').date() if extracted_data.get('date') else datetime.now().date(),
            items_json=json.dumps(extracted_data.get('items', [])),
            raw_ocr=extracted_data.get('raw_summary', ''),
            confidence=float(extracted_data.get('confidence', 0.95))
        )
        db.session.add(scan_record)
        db.session.commit()
        extracted_data['scan_id'] = scan_record.id
    except Exception as e:
        db.session.rollback()
        print(f"Failed to record receipt scan: {e}")

    return jsonify({"success": True, "data": extracted_data}), 200

@ai_bp.route('/api/ai/sample-receipts', methods=['GET'])
@login_required
def sample_receipts():
    """Returns sample student receipts for quick testing."""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    samples = [
        {
            "id": "sample_canteen",
            "title": "College Canteen Lunch Slip",
            "merchant": "University Food Court",
            "total_amount": 185.00,
            "currency": "INR",
            "date": today,
            "category": "Food",
            "subcategory": "Lunch",
            "payment_method": "UPI",
            "is_essential": True,
            "items": [
                {"name": "Special Thali", "price": 120.00, "qty": 1},
                {"name": "Sweet Lassi", "price": 45.00, "qty": 1},
                {"name": "Extra Roti (2 pcs)", "price": 20.00, "qty": 1}
            ],
            "tax_amount": 0.0,
            "confidence": 0.98,
            "raw_summary": "Order #104 at University Food Court"
        },
        {
            "id": "sample_books",
            "title": "Campus Bookstore & Stationery",
            "merchant": "Academic Book Depot",
            "total_amount": 620.00,
            "currency": "INR",
            "date": yesterday,
            "category": "Education",
            "subcategory": "Textbooks & Notes",
            "payment_method": "Debit Card",
            "is_essential": True,
            "items": [
                {"name": "Algorithm Design Manual", "price": 450.00, "qty": 1},
                {"name": "Classmate Spiral Notebook (300p)", "price": 120.00, "qty": 1},
                {"name": "Gel Pens Set (5)", "price": 50.00, "qty": 1}
            ],
            "tax_amount": 0.0,
            "confidence": 0.99,
            "raw_summary": "Invoice #BK-8842 from Academic Book Depot"
        },
        {
            "id": "sample_hostel_pizza",
            "title": "Hostel Pizza Night with Friends",
            "merchant": "Domino's Pizza",
            "total_amount": 849.00,
            "currency": "INR",
            "date": yesterday,
            "category": "Food",
            "subcategory": "Fast Food & Dining",
            "payment_method": "UPI",
            "is_essential": False,
            "items": [
                {"name": "Farmhouse Medium Pizza", "price": 459.00, "qty": 1},
                {"name": "Stuffed Garlic Bread", "price": 159.00, "qty": 1},
                {"name": "Pepsi 750ml", "price": 60.00, "qty": 1},
                {"name": "Choco Lava Cake", "price": 110.00, "qty": 1}
            ],
            "tax_amount": 42.45,
            "confidence": 0.96,
            "raw_summary": "Domino's Tax Invoice #DOM-9104"
        }
    ]
    return jsonify(samples), 200

# ----------------- Voice Expense NLU Endpoint -----------------

@ai_bp.route('/api/ai/parse-voice', methods=['POST'])
@login_required
def parse_voice():
    """Accepts spoken voice transcription and returns structured expense fields."""
    data = request.get_json() or {}
    voice_text = data.get('text', '').strip()

    if not voice_text:
        return jsonify({"error": "Voice text is required."}), 400

    parsed_expense = parse_voice_expense_text(voice_text)
    return jsonify({"success": True, "expense": parsed_expense}), 200

# ----------------- Gamification & Financial Health Scorecard -----------------

@ai_bp.route('/api/ai/health-score', methods=['GET'])
@login_required
def get_health_score():
    """
    Computes a gamified 0-100 financial health scorecard with badges,
    breakdowns across savings rate, budget discipline, and expense consistency.
    """
    user_id = session['user_id']
    user = User.query.get(user_id)
    now = datetime.now()
    start_date = datetime(now.year, now.month, 1).date()

    expenses = Expense.query.filter_by(user_id=user_id).all()
    curr_month_expenses = [e for e in expenses if e.expense_date >= start_date]
    total_spent = sum(e.amount for e in curr_month_expenses)

    overall_budget = Budget.query.filter_by(user_id=user_id, month=now.month, year=now.year, category=None).first()
    budget_val = overall_budget.amount if overall_budget else (user.monthly_income_or_allowance if user else 0.0)

    # 1. Budget Adherence Score (0-35 points)
    if budget_val > 0:
        ratio = total_spent / budget_val
        if ratio <= 0.70:
            budget_score = 35
        elif ratio <= 0.90:
            budget_score = 30
        elif ratio <= 1.00:
            budget_score = 25
        elif ratio <= 1.15:
            budget_score = 15
        else:
            budget_score = 5
    else:
        budget_score = 20 # Default baseline

    # 2. Needs vs Wants Essential Ratio Score (0-25 points)
    essential_spent = sum(e.amount for e in curr_month_expenses if e.is_essential)
    if total_spent > 0:
        essential_pct = (essential_spent / total_spent) * 100
        if 50 <= essential_pct <= 75:
            needs_score = 25 # Golden 50/30/20 rule
        elif essential_pct > 75:
            needs_score = 20
        else:
            needs_score = 12
    else:
        needs_score = 20

    # 3. Tracking Consistency & Logs (0-20 points)
    log_count = len(curr_month_expenses)
    if log_count >= 15:
        tracking_score = 20
    elif log_count >= 7:
        tracking_score = 15
    elif log_count >= 1:
        tracking_score = 10
    else:
        tracking_score = 5

    # 4. Financial Goals Score (0-20 points)
    goals = FinancialGoal.query.filter_by(user_id=user_id).all()
    if goals:
        completed = [g for g in goals if g.status == 'completed' or g.current_amount >= g.target_amount]
        goals_score = min(20, int((len(completed) / len(goals)) * 20) + 10)
    else:
        goals_score = 10

    total_score = min(100, max(0, budget_score + needs_score + tracking_score + goals_score))

    # Badges evaluation
    badges = []
    if total_score >= 80:
        badges.append({"id": "master", "name": "Wealth Master", "icon": "fa-solid fa-crown", "color": "text-amber-500", "desc": "Top-tier student financial discipline!"})
    if budget_score >= 30:
        badges.append({"id": "guardian", "name": "Budget Guardian", "icon": "fa-solid fa-shield-halved", "color": "text-blue-500", "desc": "Spending strictly within monthly limits"})
    if tracking_score >= 15:
        badges.append({"id": "tracker", "name": "Streak Legend", "icon": "fa-solid fa-fire", "color": "text-rose-500", "desc": "Consistent daily expense logging"})
    if needs_score >= 20:
        badges.append({"id": "smart_saver", "name": "Smart Spender", "icon": "fa-solid fa-piggy-bank", "color": "text-emerald-500", "desc": "Optimal essential vs leisure balance"})

    # If no badges earned yet, provide beginner badge
    if not badges:
        badges.append({"id": "starter", "name": "Financial Scout", "icon": "fa-solid fa-compass", "color": "text-indigo-500", "desc": "Starting the smart budgeting journey"})

    return jsonify({
        "score": total_score,
        "grade": "A+" if total_score >= 85 else ("A" if total_score >= 75 else ("B" if total_score >= 60 else "C")),
        "breakdown": {
            "budget_discipline": {"score": budget_score, "max": 35},
            "necessity_ratio": {"score": needs_score, "max": 25},
            "tracking_consistency": {"score": tracking_score, "max": 20},
            "goals_progress": {"score": goals_score, "max": 20}
        },
        "badges": badges
    }), 200

# ----------------- Export Data -----------------

@ai_bp.route('/api/export', methods=['POST'])
@login_required
def export_data():
    user_id = session['user_id']
    data = request.get_json() or {}
    export_format = data.get('format', 'csv').lower()

    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.expense_date.desc()).all()

    if export_format == 'json':
        expenses_json = [e.to_dict() for e in expenses]
        response_data = json.dumps(expenses_json, indent=2)
        return Response(
            response_data,
            mimetype="application/json",
            headers={"Content-disposition": "attachment; filename=expenses_export.json"}
        )

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Date", "Category", "Subcategory", "Description", "Amount", "Payment Method", "Is Essential"])
    for e in expenses:
        cw.writerow([
            e.expense_date.strftime("%Y-%m-%d"),
            e.category,
            e.subcategory or "",
            e.description or "",
            e.amount,
            e.payment_method,
            "Yes" if e.is_essential else "No"
        ])
        
    response_data = si.getvalue()
    return Response(
        response_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=expenses_export.csv"}
    )
