"""
Configuration settings for the invoicer application using pydantic_settings.
"""

from pathlib import Path
from typing import List, Optional
from pydantic import Field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class InvoicerSettings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Company/Personal Information
    company_name: str = Field(default="Your Company Name", description="Company name")
    company_address: str = Field(
        default="Your Address\nCity, State ZIP\nCountry", description="Company address"
    )
    company_email: EmailStr = Field(
        default="your.email@example.com", description="Company email address"
    )
    company_phone: str = Field(
        default="+1 (555) 123-4567", description="Company phone number"
    )

    # Invoice Settings
    hourly_rate: float = Field(default=75.0, description="Hourly rate", gt=0)
    hours_per_day: float = Field(default=8.0, description="Hours per day", gt=0)
    currency: str = Field(default="EUR", description="Currency code")
    currency_symbol: str = Field(default="€", description="Currency symbol")
    vat_rate: float = Field(
        default=0.21, description="VAT rate (0.21 for 21%)", ge=0, le=1
    )
    invoice_number_template: str = Field(
        default="INV-{year}{month:02d}-{client_code}",
        description="Invoice number template",
    )

    # Microsoft Graph API Settings for email
    microsoft_client_id: Optional[str] = Field(
        default=None, description="Microsoft client ID"
    )
    microsoft_client_secret: Optional[str] = Field(
        default=None, description="Microsoft client secret"
    )
    microsoft_tenant_id: Optional[str] = Field(
        default=None, description="Microsoft tenant ID"
    )
    microsoft_redirect_uri: str = Field(
        default="http://localhost:8080/callback", description="Microsoft redirect URI"
    )

    # Microsoft Graph API Scopes
    microsoft_scopes: List[str] = Field(
        default=[
            "https://graph.microsoft.com/Mail.Send",
            "https://graph.microsoft.com/User.Read",
        ],
        description="Microsoft Graph API scopes",
    )

    # Directory Settings
    invoices_dir: Path = Field(
        default_factory=lambda: Path.cwd() / "invoices",
        description="Directory for storing invoices",
    )
    templates_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent / "templates",
        description="Directory for templates",
    )
    clients_dir: Path = Field(
        default_factory=lambda: Path.cwd() / "clients",
        description="Directory for storing client data",
    )

    def __init__(self, **kwargs):
        """Initialize settings and create directories."""
        super().__init__(**kwargs)
        self.create_directories()

    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.invoices_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        self.clients_dir.mkdir(exist_ok=True)


# Create a singleton instance of the settings
settings = InvoicerSettings()

# Export commonly used settings as module-level variables for backward compatibility
COMPANY_NAME = settings.company_name
COMPANY_ADDRESS = settings.company_address
COMPANY_EMAIL = settings.company_email
COMPANY_PHONE = settings.company_phone

HOURLY_RATE = settings.hourly_rate
HOURS_PER_DAY = settings.hours_per_day
CURRENCY = settings.currency
CURRENCY_SYMBOL = settings.currency_symbol
VAT_RATE = settings.vat_rate
INVOICE_NUMBER_TEMPLATE = settings.invoice_number_template

CLIENT_ID = settings.microsoft_client_id
CLIENT_SECRET = settings.microsoft_client_secret
TENANT_ID = settings.microsoft_tenant_id
REDIRECT_URI = settings.microsoft_redirect_uri
SCOPES = settings.microsoft_scopes

INVOICES_DIR = settings.invoices_dir
TEMPLATES_DIR = settings.templates_dir
CLIENTS_DIR = settings.clients_dir
