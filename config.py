import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_student_portal_key_123!")
    
    # On Vercel serverless environments, root is read-only so SQLite must live in /tmp
    if os.getenv("VERCEL"):
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:////tmp/expense.db")
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///expense.db")
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Google OAuth 2.0 Settings
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/api/auth/google/callback")
