"""
Pydantic models for the invoicer application.

This module defines data models for clients, invoices, and other entities.
"""

from datetime import datetime
from typing import Optional
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    EmailStr,
    field_validator,
    field_serializer,
)


class ClientModel(BaseModel):
    """Pydantic model for client data"""

    id: str = Field(..., description="Unique client identifier")
    name: str = Field(..., description="Client/Company name", min_length=1)
    email: EmailStr = Field(..., description="Client email address")
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

    @field_validator("name")
    def validate_name(cls, v):
        """Ensure name is not empty string"""
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_serializer("created_date", "last_invoice_date")
    def serialize_datetime(self, v: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format"""
        return v.isoformat() if v else None

    model_config = ConfigDict(
        validate_assignment=True,
    )


class ClientSummaryModel(BaseModel):
    """Simplified client model for listings and summaries"""

    id: str
    name: str
    email: EmailStr
    client_code: str
    created_date: datetime
    last_invoice_date: Optional[datetime] = None
    total_invoices: int = 0


class InvoiceItemModel(BaseModel):
    """Pydantic model for individual invoice line items"""

    description: str = Field(
        ..., description="Service or item description", min_length=1
    )
    quantity: float = Field(..., description="Quantity (e.g., days, hours)", gt=0)
    unit_type: str = Field(default="days", description="Unit type (days, hours, items)")
    rate: float = Field(..., description="Rate per unit", gt=0)
    amount: float = Field(..., description="Total amount for this line item", ge=0)

    @field_validator("amount")
    def validate_amount_matches_calculation(cls, v, info):
        """Ensure amount matches quantity * rate"""
        values = info.data
        if "quantity" in values and "rate" in values:
            expected_amount = values["quantity"] * values["rate"]
            if (
                abs(v - expected_amount) > 0.01
            ):  # Allow for small floating point differences
                raise ValueError(
                    f"Amount {v} doesn't match quantity {values['quantity']} * rate {values['rate']} = {expected_amount}"
                )
        return round(v, 2)


class InvoiceClientInfoModel(BaseModel):
    """Client information embedded in invoice data"""

    name: str = Field(..., description="Client/Company name", min_length=1)
    email: EmailStr = Field(..., description="Client email address")
    client_code: str = Field(
        ..., description="Client code", min_length=1, max_length=10
    )
    address: Optional[str] = Field(default="", description="Client address")
    client_id: Optional[str] = Field(default=None, description="Client ID reference")


class InvoiceModel(BaseModel):
    """Pydantic model for invoice data"""

    invoice_number: str = Field(..., description="Unique invoice number", min_length=1)
    invoice_date: datetime = Field(
        default_factory=datetime.now, description="Invoice date"
    )
    due_date: str = Field(default="Net 30 days", description="Due date description")

    # Client information
    client_info: InvoiceClientInfoModel = Field(..., description="Client information")

    # Invoice items
    line_items: list[InvoiceItemModel] = Field(
        default_factory=list, description="Invoice line items"
    )

    # Legacy support for days-based invoicing
    days_worked: Optional[int] = Field(
        default=None, description="Days worked (legacy)", ge=0
    )
    project_description: Optional[str] = Field(
        default=None, description="Project description (legacy)"
    )
    period: Optional[str] = Field(default=None, description="Invoice period (legacy)")

    # Financial details
    subtotal: float = Field(..., description="Subtotal amount", ge=0)
    tax_rate: float = Field(
        default=0.0, description="Tax rate (0.0 to 1.0)", ge=0, le=1
    )
    tax_amount: float = Field(default=0.0, description="Tax amount", ge=0)
    total_amount: float = Field(..., description="Total amount due", ge=0)

    # Terms and notes
    payment_terms: str = Field(
        default="Payment is due within 30 days of invoice date. Late payments may incur additional charges.",
        description="Payment terms",
    )
    thank_you_note: Optional[str] = Field(
        default=None, description="Thank you note or additional message"
    )

    @field_validator("tax_amount")
    def validate_tax_amount(cls, v, info):
        """Ensure tax amount matches subtotal * tax_rate"""
        values = info.data
        if "subtotal" in values and "tax_rate" in values:
            expected_tax = values["subtotal"] * values["tax_rate"]
            if (
                abs(v - expected_tax) > 0.01
            ):  # Allow for small floating point differences
                raise ValueError(
                    f"Tax amount {v} doesn't match subtotal {values['subtotal']} * tax_rate {values['tax_rate']} = {expected_tax}"
                )
        return round(v, 2)

    @field_validator("total_amount")
    def validate_total_amount(cls, v, info):
        """Ensure total amount matches subtotal + tax_amount"""
        values = info.data
        if "subtotal" in values and "tax_amount" in values:
            expected_total = values["subtotal"] + values["tax_amount"]
            if (
                abs(v - expected_total) > 0.01
            ):  # Allow for small floating point differences
                raise ValueError(
                    f"Total amount {v} doesn't match subtotal {values['subtotal']} + tax_amount {values['tax_amount']} = {expected_total}"
                )
        return round(v, 2)

    @field_validator("subtotal")
    def validate_subtotal_matches_line_items(cls, v, info):
        """Ensure subtotal matches sum of line items (if line_items exist)"""
        values = info.data
        if "line_items" in values and values["line_items"]:
            expected_subtotal = sum(item.amount for item in values["line_items"])
            if (
                abs(v - expected_subtotal) > 0.01
            ):  # Allow for small floating point differences
                raise ValueError(
                    f"Subtotal {v} doesn't match sum of line items {expected_subtotal}"
                )
        return round(v, 2)

    @field_serializer("invoice_date")
    def serialize_datetime(self, v: datetime) -> str:
        """Serialize datetime fields to ISO format"""
        return v.isoformat()

    model_config = ConfigDict(
        validate_assignment=True,
    )


class InvoiceSummaryModel(BaseModel):
    """Simplified invoice model for listings and summaries"""

    invoice_number: str
    invoice_date: datetime
    client_name: str
    client_id: Optional[str] = None
    total_amount: float
    due_date: str
