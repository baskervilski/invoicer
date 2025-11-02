"""
Integration tests for invoicer - testing end-to-end workflows.
"""

from pathlib import Path
from invoicer.client_manager import ClientManager
from invoicer.invoice_generator import InvoiceGenerator, create_invoice_data
from invoicer.models import ClientModel


def test_full_client_to_invoice_workflow(temp_dir, test_generator: InvoiceGenerator, sample_client: ClientModel):
    """Test the complete workflow: create client -> generate invoice -> create PDF."""
    # Step 1: Create a client
    client_manager = ClientManager(clients_dir=temp_dir)

    client_id = client_manager.add_client(sample_client.model_dump())
    assert client_id is not None

    # Step 2: Create invoice data for this client
    invoice_data = create_invoice_data(
        settings=test_generator.settings,
        client=sample_client,
        days_worked=15,
    )

    # Link invoice to client
    invoice_data.client_info.client_id = client_id

    # Step 3: Generate PDF
    pdf_path = test_generator.create_invoice(invoice_data)

    # Verify everything worked
    assert isinstance(pdf_path, Path)
    assert pdf_path.exists()
    assert sample_client.client_code in str(pdf_path)  # Client code in path

    # Verify client still exists
    retrieved_client = client_manager.get_client(client_id)
    assert retrieved_client is not None
    assert retrieved_client.name == sample_client.name


def test_multiple_clients_multiple_invoices(
    temp_dir,
    test_generator: InvoiceGenerator,
    sample_client: ClientModel,
    sample_client_1: ClientModel,
    sample_client_2: ClientModel,
):
    """Test creating multiple clients and invoices."""
    client_manager = ClientManager(clients_dir=temp_dir)

    created_pdfs = []

    for client in [sample_client, sample_client_1, sample_client_2]:
        # Create client
        client_id = client_manager.add_client(client.model_dump())

        # Create invoice
        invoice_data = create_invoice_data(
            settings=test_generator.settings,
            client=client,
            days_worked=12,
        )
        invoice_data.client_info.client_id = client_id

        # Generate PDF
        pdf_path = test_generator.create_invoice(invoice_data)
        created_pdfs.append(pdf_path)

    # Verify all PDFs were created
    assert len(created_pdfs) == 3
    for pdf_path in created_pdfs:
        assert pdf_path.exists()

    # Verify all clients exist
    all_clients = client_manager.list_clients()
    assert len(all_clients) == 3

    client_names = [client.name for client in all_clients]
    for client in [sample_client, sample_client_1, sample_client_2]:
        assert client.name in client_names
