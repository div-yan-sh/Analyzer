import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "spendintel_secure_default_session_secret_9988!")
    
    # On Vercel serverless environments, root is read-only so SQLite must live in /tmp
    if os.getenv("VERCEL"):
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:////tmp/expense.db")
        DEFAULT_REDIRECT_URI = "https://analyzer-xi-livid.vercel.app/api/auth/google/callback"
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///expense.db")
        DEFAULT_REDIRECT_URI = "http://127.0.0.1:5000/api/auth/google/callback"
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Google OAuth 2.0 Settings (loaded from environment variables)
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", DEFAULT_REDIRECT_URI)
