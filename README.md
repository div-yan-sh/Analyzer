# Student Expense Intelligence Portal (SpendIntel)

SpendIntel is a fully functional, production-style college student expense manager, budgeting dashboard, analytics engine, and AI-powered financial assistant. It is built using Python, Flask, SQLite, Vanilla JavaScript, and Tailwind CSS.

---

## 1. Features

- **Daily Expense Logging & CRUD**: Track amounts, descriptions, categories, payment methods, dates, and essential vs. non-essential types.
- **Smart Category Classification**: Rule-based regex keyword matching for auto-categorization of items (e.g., matching "Uber" to Transport, "McDonalds" to Food), with an optional Gemini AI fallback.
- **Statistical Anomaly Detection**: Statistical Z-score outlier checker that flags unusual spending (e.g., spending ₹2,450 on dining out compared to the usual ₹150 canteen lunch).
- **Linear Spending Forecasts**: Forecasting month-end expenditure trends and category requirements using `scikit-learn` Linear Regression modeling.
- **Goal Milestones**: Define targets (e.g. buying a coding laptop), savings progress meters, and dynamic calculators showing recommended monthly savings values.
- **Smart Recommendations**: Custom localized recommendation cards alerting students on high non-essential ratios (wants > 40%), budget warnings, and savings allocations.
- **Gemini AI Financial Assistant**: Natural-language chatbot leveraging the Gemini API to analyze personal database logs, and provide executive monthly reports.
- **PDF Report Downloads**: Automated generation and streaming of PDF reports compiling metrics, observations, and recommendations using `reportlab`.
- **Data Portability**: Backup and export user transactions to CSV or JSON formats.
- **Light/Dark Mode**: High-fidelity dark navy fintech skin with adaptive theme switching.

---

## 2. Technology Stack

- **Frontend**: HTML5, Tailwind CSS (via CDN), Vanilla JavaScript, FontAwesome Icons, Chart.js for data visualization.
- **Backend**: Python 3, Flask, Flask-SQLAlchemy (ORM), Flask-CORS for cross-origin setups, and Werkzeug for password security hashing.
- **Database**: SQLite (file-based persistence at `instance/expense.db` for local execution).
- **AI Engine**: Google GenAI SDK (`google-genai`) querying `gemini-2.5-flash` model.
- **ML / Analysis**: `scikit-learn` (linear models), `pandas`, and `numpy` for data aggregation and Z-score calculations.

---

## 3. Directory Structure

```
student-expense-intelligence/
├── app.py                      # Flask Server Core & Frontend Page Router
├── config.py                   # Environment & Database Configurations
├── requirements.txt            # System Dependencies list
├── .env                        # Local Secret environment file (Ignored in Git)
├── .env.example                # Example configuration layout
├── .gitignore                  # Git commit exclusions
├── README.md                   # Setup and methodology explanations
│
├── database/
│   ├── db.py                   # SQLAlchemy DB Initialization
│   ├── models.py               # ORM Models (User, Expense, Budget, Goal, AIInsight)
│   └── seed.py                 # Ingestion Script (6 Months of Student data + Outliers)
│
├── routes/
│   ├── auth_routes.py          # Session auth, registration, and reset endpoints
│   ├── expense_routes.py       # Transaction CRUD, auto-classifier & anomaly triggers
│   ├── budget_routes.py        # Overall and category monthly budget limits
│   ├── analytics_routes.py     # Aggregated timelines and comparison endpoints
│   ├── goal_routes.py          # Savings goals progress metrics
│   └── ai_routes.py            # Gemini Chats, Monthly briefs, PDF and CSV exports
│
├── services/
│   ├── expense_analyzer.py     # Financial Health Score out of 100
│   ├── predictor.py            # Spending forecasts wrapper
│   ├── anomaly_detector.py     # Outlier checker wrapper
│   ├── recommendation_engine.py# Heuristic saving tips
│   └── gemini_service.py       # Google Gemini API connector with local fallback
│
├── ml/
│   ├── preprocessing.py        # Data conversions to pandas DataFrames
│   ├── spending_prediction.py  # LinearRegression estimators
│   ├── anomaly_detection.py    # Standard deviation Z-score checks
│   └── category_classifier.py  # Keyword regular expression definitions
│
├── templates/
│   ├── base.html               # Adaptive layout frame & theme controllers
│   ├── landing.html            # Marketing details page
│   ├── login.html              # Secure session validation page
│   ├── register.html           # Profile creation page
│   ├── dashboard.html          # Health scores, summary metrics, and quick log inputs
│   ├── expenses.html           # Advanced keyword query tables & paginations
│   ├── analytics.html          # Graphical charts (category distribution, MoM change)
│   ├── budget.html             # Budget meters and recommended daily limit details
│   ├── goals.html              # Savings card targets
│   ├── insights.html           # Anomalies list, tips grid, and monthly report brief
│   ├── ai_assistant.html       # AI Chat bot assistant console
│   └── profile.html            # Profile updates, password modification & system resets
│
└── static/
    ├── css/
    │   └── style.css           # Custom scrollbars, circular track offsets, shadows
    └── js/
        ├── auth.js             # Form submittals and credential validators
        ├── dashboard.js        # Card animations, notifications and recent logs
        ├── expenses.js         # Pagination, editing modals and deletion calls
        ├── analytics.js        # ChartJS configurations and trend line plots
        ├── budget.js           # Today's spent aggregates and daily guidelines
        ├── goals.js            # Milestones check boxes and targets CRUD
        ├── insights.js         # Z-score logs and AI report compilers
        └── ai-assistant.js     # Chat logs and query chip connections
```

---

## 4. Methodologies

### Category Classification
The portal utilizes keyword mapping via regular expression word boundary assertions in `ml/category_classifier.py`.
If the user logs an item containing `mcdonald` or `burger`, it is classified as `Food`. If it contains `uber` or `metro`, it resolves to `Transport`. If no keywords match, and the user has a configured Gemini API key, a fallback query is sent to Gemini to assign the best category. Otherwise, it defaults to `Other`.

### Spending Prediction
In `ml/spending_prediction.py`, we employ `scikit-learn`'s `LinearRegression` model:
- **Month-End Spend**: Fits a line where $X$ is the day of the month ($1 \dots \text{current\_day}$) and $Y$ is the cumulative spending up to that day. The model projects cumulative spending to the end of the month ($X = 28/30/31$).
- **Next Month Forecast**: Learns the trend of monthly totals over historical periods and predicts the total for the upcoming month.

### Anomaly Detection
In `ml/anomaly_detection.py`, we monitor category-specific distributions:
$$Z = \frac{x - \mu}{\sigma}$$
Where $x$ is the transaction amount, $\mu$ is the user's historical category average, and $\sigma$ is the standard deviation. A transaction is flagged as unusual if $Z > 2.5$. If there is insufficient data ($N < 5$), it flags transactions that exceed 3 times the category average.

### Financial Health Score
Points are calculated dynamically (0-100):
- **Budget Control (25 pts)**: Based on overall monthly budget utilization percentage.
- **Saving Rate (25 pts)**: Evaluated based on savings as a percentage of allowance.
- **Stability (20 pts)**: Penalizes spikes in spending compared to last month.
- **Expense Management (15 pts)**: Evaluated based on non-essential spending ratio.
- **Goal Progress (15 pts)**: Weighted progress of all active savings goals.

---

## 5. Installation & Setup

### Prerequisites
- Python 3.8 or higher installed on your system.

### Step 1: Create a Virtual Environment
Navigate to the project root and create a virtual environment:
```bash
python -m venv venv
```
Activate the environment:
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` and fill in your Gemini API key:
```bash
copy .env.example .env
```
Open `.env` and update the key:
```ini
GEMINI_API_KEY=your_actual_gemini_key_here
```
*Note: If no API key is specified, the application will fallback automatically to local rule-based recommendations and analytics.*

### Step 4: Seed Database Demo Data
Create database schemas and seed 6 months of historical student records (including intentional Z-score anomalies) by executing:
```bash
python database/seed.py
```

### Step 5: Run the Server
Launch the development server:
```bash
python app.py
```
Open your web browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## 6. Demo Credentials

If you seeded the database in Step 4, log in using:
- **Email**: `demo@student.edu`
- **Password**: `student123`
