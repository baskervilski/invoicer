"""
Configuration settings for the invoicer application using pydantic_settings.
"""

from pathlib import Path
from typing import Annotated, Optional
from pydantic import Field, AfterValidator, BeforeValidator, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from .validators import validate_template, validate_currency_code

# Helper functions
def strip_whitespace(value: str) -> str:
    """Strip leading and trailing whitespace."""
    return value.strip()

def validate_non_empty_after_strip(value: str) -> str:
    """Validate that string is not empty after stripping whitespace."""
    if not value:
        raise ValueError("Field cannot be empty")
    return value

# ============================================================================
# Single-use field types for config.py
# ============================================================================

# Company information fields used only in config
CompanyNameField = Annotated[
    str,
    BeforeValidator(strip_whitespace),
    AfterValidator(validate_non_empty_after_strip),
    Field(
        default="Your Company Name",
        min_length=1,
        description="Company name for invoices and business correspondence",
    ),
]

CompanyAddressField = Annotated[
    str,
    Field(
        default="Your Address\nCity, State ZIP\nCountry",
        description="Company address for invoices",
    ),
]

CompanyEmailField = Annotated[
    EmailStr,
    Field(
        default="your.email@example.com",
        description="Company email address for invoices and correspondence",
    ),
]

# Invoice settings fields used only in config
CurrencyCodeField = Annotated[
    str,
    AfterValidator(lambda v: validate_currency_code(v)),
    Field(
        default="EUR",
        min_length=3,
        max_length=3,
        description="3-letter currency code (e.g., USD, EUR, GBP)",
    ),
]

VatRateField = Annotated[
    float,
    Field(
        default=0.21,
        ge=0,
        le=1,
        description="VAT rate as decimal (0.21 for 21%)",
    ),
]

# API fields used only in config
OptionalSecretField = Annotated[
    Optional[str],
    Field(default=None, description="Optional secret or credential"),
]

# Template and format fields used only in config
CurrencySymbolField = Annotated[
    str,
    Field(default="€", description="Currency symbol for display"),
]

InvoiceTemplateField = Annotated[
    str,
    AfterValidator(lambda v: v if validate_template(v) else (_ for _ in ()).throw(ValueError("Invalid template format"))),
    Field(
        default="INV-{year}{month:02d}-{client_code}",
        description="Invoice number template with variables: {year}, {month}, {day}, {client_code}, {invoice_number}",
    ),
]

# Directory fields used only in config
InvoicesDirectoryField = Annotated[
    Path,
    Field(
        default_factory=lambda: Path.cwd() / "invoices",
        description="Directory for storing invoices",
    ),
]

ClientsDirectoryField = Annotated[
    Path,
    Field(
        default_factory=lambda: Path.cwd() / "clients",
        description="Directory for storing client data",
    ),
]

TemplatesDirectoryField = Annotated[
    Path,
    Field(
        default_factory=lambda: Path(__file__).parent / "templates",
        description="Directory for invoice templates",
    ),
]

RedirectUriField = Annotated[
    str,
    Field(
        default="http://localhost:8080/callback",
        description="Redirect URI for OAuth authentication",
    ),
]

ScopesListField = Annotated[
    list[str],
    Field(
        default=[
            "https://graph.microsoft.com/Mail.Send",
            "https://graph.microsoft.com/User.Read",
        ],
        description="List of API scopes or permissions",
    ),
]


class InvoicerSettings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Company/Personal Information using field types
    company_name: CompanyNameField
    company_address: CompanyAddressField
    company_email: CompanyEmailField
    company_phone: Annotated[
        str,
        Field(
            default="+1 (555) 123-4567",
            description="Company phone number",
        ),
    ]
    company_vat: Annotated[
        str,
        Field(
            default="",
            description="Company VAT number (e.g., BE 1009.356.858)",
        ),
    ]


    # Invoice Settings using field types
    hourly_rate: Annotated[
        float,
        Field(default=75.0, gt=0, description="Hourly billing rate"),
    ]
    hours_per_day: Annotated[
        float,
        Field(default=8.0, gt=0, description="Standard hours per working day"),
    ]
    currency: CurrencyCodeField
    currency_symbol: CurrencySymbolField
    vat_rate: VatRateField
    invoice_number_template: InvoiceTemplateField

    # Microsoft Graph API Settings using field types
    microsoft_client_id: OptionalSecretField = None
    microsoft_client_secret: OptionalSecretField = None
    microsoft_tenant_id: OptionalSecretField = None
    microsoft_redirect_uri: RedirectUriField
    microsoft_scopes: ScopesListField

    # Directory Settings using field types
    invoices_dir: InvoicesDirectoryField
    templates_dir: TemplatesDirectoryField
    clients_dir: ClientsDirectoryField

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
COMPANY_VAT = settings.company_vat

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
