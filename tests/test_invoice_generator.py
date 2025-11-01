"""
Unit tests for invoice generator - testing main functionality.
"""

from datetime import datetime
from pathlib import Path

from invoicer.config import InvoicerSettings
from invoicer.invoice_generator import (
    InvoiceGenerator,
    generate_invoice_number,
    create_invoice_data,
)
from invoicer.models import InvoiceModel


def test_generate_invoice_number_basic(mock_settings: InvoicerSettings):
    """Test that invoice numbers are generated correctly."""
    mock_settings.invoice_number_template = "INV-{year}{month:02d}-{client_code}"

    test_date = datetime(2024, 10, 15)
    result = generate_invoice_number(
        invoice_number_template=mock_settings.invoice_number_template,
        client_code="TST",
        invoice_date=test_date,
    )

    assert "INV-202410-TST" == result


def test_create_sample_invoice_data_basic(mock_settings: InvoicerSettings, sample_client):
    """Test that sample invoice data is created correctly."""

    days_worked = 10
    h_per_day = mock_settings.hours_per_day

    invoice = create_invoice_data(
        settings=mock_settings,
        client=sample_client,
        days_worked=days_worked,
    )

    assert isinstance(invoice, InvoiceModel)
    assert invoice.client_info.name == sample_client.name
    assert invoice.client_info.email == sample_client.email
    assert invoice.days_worked == days_worked

    # Check financial calculations
    expected_hourly_rate = mock_settings.hourly_rate
    expected_subtotal = days_worked * h_per_day * expected_hourly_rate
    expected_vat = expected_subtotal * mock_settings.vat_rate
    expected_total = expected_subtotal + expected_vat

    assert invoice.subtotal == expected_subtotal, (mock_settings, invoice.model_dump())
    assert invoice.tax_rate == mock_settings.vat_rate
    assert invoice.tax_amount == expected_vat
    assert invoice.total_amount == expected_total


def test_invoice_generator_initialization(mock_settings: InvoicerSettings):
    """Test that InvoiceGenerator can be initialized."""
    generator = InvoiceGenerator(settings=mock_settings)

    assert generator.page_size is not None
    assert generator.styles is not None


def test_create_invoice_returns_path(test_generator: InvoiceGenerator, sample_invoice):
    """Test that create_invoice returns a valid path."""

    result = test_generator.create_invoice(sample_invoice)

    assert isinstance(result, Path)
    assert str(result).endswith(".pdf")


def test_create_sample_invoice_with_defaults(mock_settings: InvoicerSettings, sample_client):
    """Test creating sample invoice with default parameters."""
    invoice = create_invoice_data(settings=mock_settings, client=sample_client)

    assert invoice.client_info.name == sample_client.name
    assert invoice.client_info.client_code == sample_client.client_code
    assert invoice.days_worked == 20
    assert invoice.subtotal > 0
    assert invoice.total_amount > 0


def test_create_sample_invoice_with_custom_date(mock_settings: InvoicerSettings, sample_client):
    """Test creating sample invoice with custom invoice date."""
    custom_date = datetime(2025, 11, 30, 23, 59, 59)

    invoice = create_invoice_data(
        settings=mock_settings,
        client=sample_client,
        days_worked=5,
        month_year="November 2025",
        invoice_date=custom_date,
    )

    assert invoice.invoice_date == custom_date
    assert invoice.client_info.name == sample_client.name
    assert invoice.days_worked == 5


def test_create_sample_invoice_without_custom_date(mock_settings: InvoicerSettings, sample_client):
    """Test creating sample invoice without custom date uses current time."""
    before_creation = datetime.now()

    invoice = create_invoice_data(
        settings=mock_settings,
        client=sample_client,
        days_worked=3,
    )

    after_creation = datetime.now()

    # Invoice date should be between before and after creation times
    assert before_creation <= invoice.invoice_date <= after_creation
