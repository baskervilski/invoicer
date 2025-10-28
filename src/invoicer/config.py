# Configuration settings for the invoicer application
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Company/Personal Information
COMPANY_NAME = os.getenv("COMPANY_NAME", "Your Company Name")
COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS", "Your Address\nCity, State ZIP\nCountry")
COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "your.email@example.com")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+1 (555) 123-4567")

# Invoice Settings
HOURLY_RATE = float(os.getenv("HOURLY_RATE", "75.0"))  # Default €75/hour
HOURS_PER_DAY = float(os.getenv("HOURS_PER_DAY", "8.0"))  # Default 8 hours/day
CURRENCY = os.getenv("CURRENCY", "EUR")
CURRENCY_SYMBOL = os.getenv("CURRENCY_SYMBOL", "€")
INVOICE_NUMBER_TEMPLATE = os.getenv(
    "INVOICE_NUMBER_TEMPLATE", "INV-{year}{month:02d}-{client_code}"
)

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
# Use current working directory instead of module directory
INVOICES_DIR = Path.cwd() / "invoices"
TEMPLATES_DIR = Path(__file__).parent / "templates"  # Keep templates in module for now
CLIENTS_DIR = Path.cwd() / "clients"

# Create directories if they don't exist
INVOICES_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)
CLIENTS_DIR.mkdir(exist_ok=True)
