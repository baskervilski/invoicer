"""
Test PDF invoice generation functionality.
"""

from pathlib import Path
from invoicer.invoice_generator import InvoiceGenerator, create_invoice_data
from invoicer.models import ClientModel


def test_pdf_generation(test_generator: InvoiceGenerator, sample_client):
    """Test that PDF invoices can be generated successfully."""
    # Create sample invoice data using InvoiceModel
    invoice_data = create_invoice_data(
        settings=test_generator.settings,
        client=sample_client,
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


def test_pdf_generation_with_tax(test_generator: InvoiceGenerator, sample_client):
    """Test PDF generation with tax calculations."""
    # Create invoice data with tax
    invoice_data = create_invoice_data(
        settings=test_generator.settings,
        client=sample_client,
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


def test_pdf_generation_different_clients(
    test_generator: InvoiceGenerator,
    sample_client: ClientModel,
    sample_client_2: ClientModel,
    sample_client_1: ClientModel,
):
    """Test PDF generation for different client codes."""
    clients = [sample_client, sample_client_2, sample_client_1]

    for client in clients:
        invoice_data = create_invoice_data(
            settings=test_generator.settings,
            client=client,
            days_worked=8,
        )

        pdf_path = test_generator.create_invoice(invoice_data)

        assert pdf_path.exists()
        assert client.client_code in str(pdf_path)  # Client code should be in path
