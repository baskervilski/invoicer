"""
Test cases for invoice duplicate checking functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from invoicer.main import check_invoice_exists, get_alternative_invoice_number
from invoicer.invoice_generator import generate_invoice_number
from invoicer.config import InvoicerSettings


@pytest.fixture
def temp_invoice_dir():
    """Create a temporary directory for invoice testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_settings(temp_invoice_dir):
    """Mock settings with temporary invoice directory."""
    return InvoicerSettings(
        microsoft_client_id="test_client_id",
        microsoft_client_secret="test_client_secret",
        microsoft_tenant_id="test_tenant_id",
        invoices_dir=temp_invoice_dir,
        company_name="Test Company",
        company_email="test@company.com",
        company_phone="+1-555-0123",
        hourly_rate=75.0,
        hours_per_day=8.0,
        currency_symbol="$",
        invoice_number_template="INV-{year}{month:02d}-{client_code}",
    )


def test_check_invoice_exists_file_not_found(mock_settings, temp_invoice_dir):
    """Test check_invoice_exists when invoice file doesn't exist."""
    with patch("invoicer.main.settings", mock_settings):
        exists = check_invoice_exists("TST", "INV-202511-TST", datetime(2025, 11, 1))
        assert not exists


def test_check_invoice_exists_file_found(mock_settings, temp_invoice_dir):
    """Test check_invoice_exists when invoice file exists."""
    # Create the directory structure
    year_dir = temp_invoice_dir / "2025"
    client_dir = year_dir / "TST"
    client_dir.mkdir(parents=True)

    # Create a test invoice file
    invoice_file = client_dir / "Invoice_INV-202511-TST.pdf"
    invoice_file.write_text("test invoice content")

    with patch("invoicer.main.settings", mock_settings):
        exists = check_invoice_exists("TST", "INV-202511-TST", datetime(2025, 11, 1))
        assert exists


def test_get_alternative_invoice_number_first_try(mock_settings, temp_invoice_dir):
    """Test getting alternative invoice number when first alternative is available."""
    # Create the directory structure with original invoice
    year_dir = temp_invoice_dir / "2025"
    client_dir = year_dir / "TST"
    client_dir.mkdir(parents=True)

    # Create original invoice file
    original_file = client_dir / "Invoice_INV-202511-TST.pdf"
    original_file.write_text("original invoice")

    with patch("invoicer.main.settings", mock_settings):
        alternative = get_alternative_invoice_number("TST", "INV-202511-TST", datetime(2025, 11, 1))
        assert alternative == "INV-202511-TST-001"


def test_get_alternative_invoice_number_multiple_conflicts(mock_settings, temp_invoice_dir):
    """Test getting alternative invoice number when multiple alternatives exist."""
    # Create the directory structure
    year_dir = temp_invoice_dir / "2025"
    client_dir = year_dir / "TST"
    client_dir.mkdir(parents=True)

    # Create original and first few alternatives
    files_to_create = [
        "Invoice_INV-202511-TST.pdf",
        "Invoice_INV-202511-TST-001.pdf",
        "Invoice_INV-202511-TST-002.pdf",
    ]

    for filename in files_to_create:
        (client_dir / filename).write_text("test content")

    with patch("invoicer.main.settings", mock_settings):
        alternative = get_alternative_invoice_number("TST", "INV-202511-TST", datetime(2025, 11, 1))
        assert alternative == "INV-202511-TST-003"


def test_generate_invoice_number_format(mock_settings):
    """Test that invoice numbers are generated in the expected format."""
    with patch("invoicer.main.settings", mock_settings):
        invoice_number = generate_invoice_number(mock_settings.invoice_number_template, "TST", datetime(2025, 11, 15))
        assert invoice_number == "INV-202511-TST"


def test_invoice_number_different_months(mock_settings):
    """Test that different months generate different invoice numbers."""
    with patch("invoicer.main.settings", mock_settings):
        nov_number = generate_invoice_number(mock_settings.invoice_number_template, "TST", datetime(2025, 11, 1))
        dec_number = generate_invoice_number(mock_settings.invoice_number_template, "TST", datetime(2025, 12, 1))

        assert nov_number == "INV-202511-TST"
        assert dec_number == "INV-202512-TST"
        assert nov_number != dec_number


def test_invoice_number_different_clients(mock_settings):
    """Test that different clients generate different invoice numbers."""
    test_date = datetime(2025, 11, 1)

    with patch("invoicer.main.settings", mock_settings):
        client1_number = generate_invoice_number(mock_settings.invoice_number_template, "CLI1", test_date)
        client2_number = generate_invoice_number(mock_settings.invoice_number_template, "CLI2", test_date)

        assert client1_number == "INV-202511-CLI1"
        assert client2_number == "INV-202511-CLI2"
        assert client1_number != client2_number
