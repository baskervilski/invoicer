"""
Pydantic models for the invoicer application.

This module defines data models for clients, invoices, and other entities.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator


class ClientModel(BaseModel):
    """Pydantic model for client data"""

    id: str = Field(..., description="Unique client identifier")
    name: str = Field(..., description="Client name", min_length=1)
    email: EmailStr = Field(..., description="Client email address")
    company: str = Field(..., description="Company name", min_length=1)
    client_code: str = Field(
        ..., description="Client code for invoices", min_length=1, max_length=10
    )
    address: Optional[str] = Field(default="", description="Client address")
    phone: Optional[str] = Field(default="", description="Client phone number")
    notes: Optional[str] = Field(default="", description="Additional notes")
    created_date: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    last_invoice_date: Optional[datetime] = Field(
        default=None, description="Last invoice date"
    )
    total_invoices: int = Field(default=0, description="Total number of invoices", ge=0)
    total_amount: float = Field(
        default=0.0, description="Total invoiced amount", ge=0.0
    )

    @field_validator("client_code")
    def validate_client_code(cls, v):
        """Ensure client code is uppercase"""
        return v.upper()

    @field_validator("name", "company")
    def validate_names(cls, v):
        """Ensure names are not empty strings"""
        if not v.strip():
            raise ValueError("Name and company cannot be empty")
        return v.strip()

    class Config:
        """Pydantic configuration"""

        # Allow datetime objects to be serialized to ISO format
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}
        # Validate assignments
        validate_assignment = True


class ClientSummaryModel(BaseModel):
    """Simplified client model for listings and summaries"""

    id: str
    name: str
    email: EmailStr
    company: str
    client_code: str
    created_date: datetime
    last_invoice_date: Optional[datetime] = None
    total_invoices: int = 0
