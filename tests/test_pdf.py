"""
Test PDF invoice generation functionality.
"""

from pathlib import Path
from invoicer.invoice_generator import InvoiceGenerator, create_sample_invoice_data


def test_pdf_generation(test_generator: InvoiceGenerator):
    """Test that PDF invoices can be generated successfully."""
    # Create sample invoice data using InvoiceModel
    invoice_data = create_sample_invoice_data(
        settings=test_generator.settings,
        client_name="Test Client Corp",
        client_email="test@example.com",
        client_code="TST",
        days_worked=10,
        month_year="October 2024",
    )

    # Verify we have valid InvoiceModel data
    assert invoice_data.client_info.name == "Test Client Corp"
    assert invoice_data.days_worked == 10
    assert invoice_data.invoice_number is not None
    assert invoice_data.subtotal > 0
    assert invoice_data.total_amount > 0

    # Generate PDF
    pdf_path = test_generator.create_invoice(invoice_data)

    # Verify PDF was created
    assert isinstance(pdf_path, Path)
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"

    # Verify file has content
    file_size = pdf_path.stat().st_size
    assert file_size > 1000  # Should be a reasonable size for a PDF


def test_pdf_generation_with_tax(test_generator: InvoiceGenerator):
    """Test PDF generation with tax calculations."""
    # Create invoice data with tax
    invoice_data = create_sample_invoice_data(
        settings=test_generator.settings,
        client_name="Tax Test Client",
        client_code="TAX",
        days_worked=5,
    )

    # Manually set tax for testing
    invoice_data.tax_rate = 0.08
    invoice_data.tax_amount = invoice_data.subtotal * 0.08
    invoice_data.total_amount = invoice_data.subtotal + invoice_data.tax_amount

    # Generate PDF
    pdf_path = test_generator.create_invoice(invoice_data)

    # Verify PDF was created
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"


def test_pdf_generation_different_clients(test_generator: InvoiceGenerator):
    """Test PDF generation for different client codes."""
    client_codes = ["ABC", "XYZ", "DEF"]

    for code in client_codes:
        invoice_data = create_sample_invoice_data(
            settings=test_generator.settings,
            client_name=f"Client {code}",
            client_code=code,
            days_worked=8,
        )

        pdf_path = test_generator.create_invoice(invoice_data)

        assert pdf_path.exists()
        assert code in str(pdf_path)  # Client code should be in path
