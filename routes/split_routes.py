import urllib.parse
from flask import Blueprint, request, jsonify, session
from database.db import db
from database.models import GroupSplit, SplitMember, User
from routes.auth_routes import login_required

split_bp = Blueprint('split', __name__)

@split_bp.route('/api/splits', methods=['GET', 'POST'])
@login_required
def splits():
    user_id = session['user_id']
    user = User.query.get(user_id)

    if request.method == 'GET':
        splits = GroupSplit.query.filter_by(user_id=user_id).order_by(GroupSplit.created_at.desc()).all()
        return jsonify([s.to_dict() for s in splits]), 200

    if request.method == 'POST':
        data = request.get_json() or {}
        title = data.get('title', '').strip()
        total_amount = data.get('total_amount')
        paid_by = data.get('paid_by', user.name if user else 'You').strip()
        upi_id = data.get('upi_id', '').strip()
        members_data = data.get('members', []) # list of {"name": "Rohan", "share_amount": 150}

        if not title or total_amount is None:
            return jsonify({"error": "Title and total amount are required."}), 400

        try:
            total_amount = float(total_amount)
            if total_amount <= 0:
                return jsonify({"error": "Total amount must be greater than zero."}), 400
        except ValueError:
            return jsonify({"error": "Invalid total amount."}), 400

        try:
            new_split = GroupSplit(
                user_id=user_id,
                title=title,
                total_amount=total_amount,
                paid_by=paid_by,
                upi_id=upi_id
            )
            db.session.add(new_split)
            db.session.flush() # get new_split.id

            # If no member list provided, default to splitting with 2 roommates
            if not members_data:
                equal_share = round(total_amount / 2, 2)
                members_data = [
                    {"name": paid_by, "share_amount": equal_share, "has_paid": True},
                    {"name": "Roommate 1", "share_amount": round(total_amount - equal_share, 2), "has_paid": False}
                ]

            for m in members_data:
                m_name = m.get('name', 'Member').strip()
                m_share = float(m.get('share_amount', 0.0))
                m_paid = bool(m.get('has_paid', False) or (m_name.lower() == paid_by.lower()))
                
                member_obj = SplitMember(
                    split_id=new_split.id,
                    name=m_name,
                    share_amount=m_share,
                    has_paid=m_paid
                )
                db.session.add(member_obj)

            db.session.commit()
            return jsonify({"message": "Group split created successfully.", "split": new_split.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to create group split: {str(e)}"}), 500

@split_bp.route('/api/splits/<int:split_id>/member/<int:member_id>/toggle', methods=['POST'])
@login_required
def toggle_member_paid(split_id, member_id):
    user_id = session['user_id']
    split = GroupSplit.query.filter_by(id=split_id, user_id=user_id).first()
    if not split:
        return jsonify({"error": "Split not found."}), 404

    member = SplitMember.query.filter_by(id=member_id, split_id=split_id).first()
    if not member:
        return jsonify({"error": "Member not found."}), 404

    member.has_paid = not member.has_paid
    # If all members have paid, mark split as settled
    all_paid = all(m.has_paid for m in split.members)
    split.settled = all_paid

    try:
        db.session.commit()
        return jsonify({"message": "Payment status updated.", "split": split.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update status: {str(e)}"}), 500

@split_bp.route('/api/splits/<int:split_id>', methods=['DELETE'])
@login_required
def delete_split(split_id):
    user_id = session['user_id']
    split = GroupSplit.query.filter_by(id=split_id, user_id=user_id).first()
    if not split:
        return jsonify({"error": "Split not found."}), 404

    try:
        db.session.delete(split)
        db.session.commit()
        return jsonify({"message": "Split deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete split: {str(e)}"}), 500

@split_bp.route('/api/splits/upi-link', methods=['GET'])
@login_required
def generate_upi_link():
    """Generates standard UPI deep link and QR code target string."""
    upi_id = request.args.get('upi_id', '').strip()
    name = request.args.get('name', 'Student').strip()
    amount = request.args.get('amount', '0.00').strip()
    note = request.args.get('note', 'SpendIntel Split').strip()

    if not upi_id:
        return jsonify({"error": "UPI ID is required."}), 400

    params = {
        "pa": upi_id,
        "pn": name,
        "am": amount,
        "cu": "INR",
        "tn": note
    }
    upi_uri = f"upi://pay?{urllib.parse.urlencode(params)}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(upi_uri)}"

    return jsonify({
        "upi_uri": upi_uri,
        "qr_image_url": qr_url
    }), 200
