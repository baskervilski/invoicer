# Configuration settings for the invoicer application
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Company/Personal Information
COMPANY_NAME = os.getenv("COMPANY_NAME", "Your Company Name")
COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS", "Your Address\nCity, State ZIP\nCountry")
COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "your.email@example.com")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+1 (555) 123-4567")

# Invoice Settings
HOURLY_RATE = float(os.getenv("HOURLY_RATE", "75.0"))  # Default $75/hour
HOURS_PER_DAY = float(os.getenv("HOURS_PER_DAY", "8.0"))  # Default 8 hours/day
CURRENCY = os.getenv("CURRENCY", "USD")
CURRENCY_SYMBOL = os.getenv("CURRENCY_SYMBOL", "$")

# Microsoft Graph API Settings for email
CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
TENANT_ID = os.getenv("MICROSOFT_TENANT_ID")
REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8080/callback")

# Microsoft Graph API Scopes
SCOPES = [
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/User.Read",
]

# Directories
INVOICES_DIR = os.path.join(os.path.dirname(__file__), "invoices")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

# Create directories if they don't exist
os.makedirs(INVOICES_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
