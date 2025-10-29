"""
Unit tests for invoicer models - testing main validation behaviors.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime

from invoicer.models import (
    ClientModel,
    InvoiceModel,
    InvoiceItemModel,
    InvoiceClientInfoModel,
)


def test_client_model_basic_creation():
    """Test that ClientModel can be created with valid data."""
    client = ClientModel(
        id="test_client",
        name="Test Company",
        email="test@company.com",
        client_code="TST",
    )

    assert client.name == "Test Company"
    assert client.email == "test@company.com"
    assert client.client_code == "TST"  # Should be uppercase
    assert client.total_invoices == 0
    assert client.total_amount == 0.0


def test_client_model_validation_failures():
    """Test that ClientModel rejects invalid data."""
    # Invalid email
    with pytest.raises(ValidationError):
        ClientModel(id="test", name="Test", email="invalid-email", client_code="TST")

    # Empty name
    with pytest.raises(ValidationError):
        ClientModel(id="test", name="", email="test@test.com", client_code="TST")


def test_invoice_item_calculation_validation():
    """Test that InvoiceItemModel validates amount calculations."""
    # Valid item
    item = InvoiceItemModel(
        description="Service", quantity=5.0, rate=100.0, amount=500.0
    )
    assert item.amount == 500.0

    # Invalid calculation
    with pytest.raises(ValidationError):
        InvoiceItemModel(
            description="Service",
            quantity=5.0,
            rate=100.0,
            amount=400.0,  # Wrong amount
        )


def test_invoice_model_financial_validation(sample_invoice):
    """Test that InvoiceModel validates financial calculations."""
    # Tax amount validation
    with pytest.raises(ValidationError):
        InvoiceModel(
            invoice_number="INV-001",
            client_info=sample_invoice.client_info,
            line_items=sample_invoice.line_items,
            subtotal=1000.0,
            tax_rate=0.10,
            tax_amount=50.0,  # Should be 100.0
            total_amount=1100.0,
        )

    # Total amount validation
    with pytest.raises(ValidationError):
        InvoiceModel(
            invoice_number="INV-001",
            client_info=sample_invoice.client_info,
            line_items=sample_invoice.line_items,
            subtotal=1000.0,
            tax_amount=100.0,
            total_amount=1000.0,  # Should be 1100.0
        )


def test_invoice_model_creates_successfully():
    """Test that InvoiceModel can be created with valid data."""
    client_info = InvoiceClientInfoModel(
        name="Test Client", email="client@test.com", client_code="TST"
    )

    invoice = InvoiceModel(
        invoice_number="INV-001",
        client_info=client_info,
        subtotal=1000.0,
        total_amount=1000.0,
    )

    assert invoice.invoice_number == "INV-001"
    assert invoice.client_info.name == "Test Client"
    assert invoice.subtotal == 1000.0
    assert invoice.total_amount == 1000.0
    assert isinstance(invoice.invoice_date, datetime)
