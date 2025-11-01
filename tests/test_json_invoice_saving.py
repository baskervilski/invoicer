"""
Test cases for JSON invoice saving functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json

from invoicer.invoice_generator import InvoiceGenerator
from invoicer.config import InvoicerSettings
from invoicer.models import InvoiceModel, InvoiceClientInfoModel


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
        company_address="123 Test St\nTest City, TS 12345",
        company_email="test@company.com",
        company_phone="+1-555-0123",
        hourly_rate=75.0,
        hours_per_day=8.0,
        currency_symbol="$",
        invoice_number_template="INV-{year}{month:02d}-{client_code}",
    )


def test_json_file_created_alongside_pdf(mock_settings, temp_invoice_dir):
    """Test that JSON file is created alongside PDF invoice."""
    generator = InvoiceGenerator(settings=mock_settings)
    
    # Create sample invoice data
    client_info = InvoiceClientInfoModel(
        name="Test Client",
        email="client@test.com",
        client_code="TST",
        address="456 Client Ave\nClient City, CC 54321",
        client_id="test_client"
    )
    
    invoice_data = InvoiceModel(
        invoice_number="INV-202511-TST",
        invoice_date=datetime(2025, 11, 1),
        client_info=client_info,
        line_items=[],
        subtotal=1000.0,
        tax_rate=0.21,
        tax_amount=210.0,
        total_amount=1210.0,
        payment_terms="Net 30 days",
    )
    
    # Generate invoice
    pdf_path = generator.create_invoice(invoice_data)
    
    # Check that PDF was created
    assert pdf_path.exists()
    assert pdf_path.name == "Invoice_INV-202511-TST.pdf"
    
    # Check that JSON was created alongside
    json_path = pdf_path.parent / "Invoice_INV-202511-TST.json"
    assert json_path.exists()
    
    # Verify JSON content
    json_content = json.loads(json_path.read_text())
    assert json_content["invoice_number"] == "INV-202511-TST"
    assert json_content["client_info"]["name"] == "Test Client"
    assert json_content["client_info"]["email"] == "client@test.com"
    assert json_content["total_amount"] == 1210.0


def test_json_contains_complete_invoice_data(mock_settings, temp_invoice_dir):
    """Test that JSON contains all invoice data fields."""
    generator = InvoiceGenerator(settings=mock_settings)
    
    client_info = InvoiceClientInfoModel(
        name="Complete Data Client",
        email="complete@test.com",
        client_code="COM",
        address="789 Complete St\nComplete City, CC 67890",
        client_id="complete_client"
    )
    
    invoice_data = InvoiceModel(
        invoice_number="INV-202511-COM",
        invoice_date=datetime(2025, 11, 15),
        client_info=client_info,
        line_items=[],
        days_worked=20,
        project_description="Test Project Work",
        period="November 2025",
        subtotal=2000.0,
        tax_rate=0.21,
        tax_amount=420.0,
        total_amount=2420.0,
        payment_terms="Net 30 days",
        thank_you_note="Thank you for your business!",
    )
    
    # Generate invoice
    pdf_path = generator.create_invoice(invoice_data)
    json_path = pdf_path.parent / "Invoice_INV-202511-COM.json"
    
    # Verify JSON contains all expected fields
    json_content = json.loads(json_path.read_text())
    
    # Check key fields are present
    expected_fields = [
        "invoice_number", "invoice_date", "client_info", "line_items",
        "days_worked", "project_description", "period", "subtotal",
        "tax_rate", "tax_amount", "total_amount", "payment_terms", "thank_you_note"
    ]
    
    for field in expected_fields:
        assert field in json_content, f"Field '{field}' missing from JSON"
    
    # Check specific values
    assert json_content["days_worked"] == 20
    assert json_content["project_description"] == "Test Project Work"
    assert json_content["period"] == "November 2025"
    assert json_content["thank_you_note"] == "Thank you for your business!"


def test_json_file_organization_matches_pdf(mock_settings, temp_invoice_dir):
    """Test that JSON files are organized in the same directory structure as PDFs."""
    generator = InvoiceGenerator(settings=mock_settings)
    
    client_info = InvoiceClientInfoModel(
        name="Organization Test Client",
        email="org@test.com",
        client_code="ORG",
        address="101 Organization Ave",
        client_id="org_client"
    )
    
    invoice_data = InvoiceModel(
        invoice_number="INV-202511-ORG",
        invoice_date=datetime(2025, 11, 20),
        client_info=client_info,
        line_items=[],
        subtotal=500.0,
        tax_rate=0.0,
        tax_amount=0.0,
        total_amount=500.0,
        payment_terms="Net 30 days",
    )
    
    # Generate invoice
    pdf_path = generator.create_invoice(invoice_data)
    json_path = pdf_path.parent / "Invoice_INV-202511-ORG.json"
    
    # Check directory structure: invoices/2025/ORG/
    expected_dir = temp_invoice_dir / "2025" / "ORG"
    assert pdf_path.parent == expected_dir
    assert json_path.parent == expected_dir
    
    # Check both files exist in the same directory
    assert pdf_path.exists()
    assert json_path.exists()
    assert pdf_path.parent == json_path.parent