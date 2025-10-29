"""
Integration tests for invoicer - testing end-to-end workflows.
"""

from pathlib import Path
from invoicer.client_manager import ClientManager
from invoicer.invoice_generator import InvoiceGenerator, create_sample_invoice_data


def test_full_client_to_invoice_workflow(temp_dir, test_generator: InvoiceGenerator):
    """Test the complete workflow: create client -> generate invoice -> create PDF."""
    # Step 1: Create a client
    client_manager = ClientManager(clients_dir=temp_dir)

    client_data = {
        "name": "Integration Test Corp",
        "email": "integration@test.com",
        "client_code": "INT",
        "address": "123 Integration St\nTest City, TC 12345",
    }

    client_id = client_manager.add_client(client_data)
    assert client_id is not None

    # Step 2: Create invoice data for this client
    invoice_data = create_sample_invoice_data(
        settings=test_generator.settings,
        client_name=client_data["name"],
        client_email=client_data["email"],
        client_code=client_data["client_code"],
        days_worked=15,
    )

    # Link invoice to client
    invoice_data.client_info.client_id = client_id

    # Step 3: Generate PDF
    pdf_path = test_generator.create_invoice(invoice_data)

    # Verify everything worked
    assert isinstance(pdf_path, Path)
    assert pdf_path.exists()
    assert "INT" in str(pdf_path)  # Client code in path

    # Verify client still exists
    retrieved_client = client_manager.get_client(client_id)
    assert retrieved_client is not None
    assert retrieved_client.name == "Integration Test Corp"


def test_multiple_clients_multiple_invoices(temp_dir, test_generator: InvoiceGenerator):
    """Test creating multiple clients and invoices."""
    client_manager = ClientManager(clients_dir=temp_dir)

    clients_data = [
        {"name": "Client A", "email": "a@test.com", "client_code": "CLA"},
        {"name": "Client B", "email": "b@test.com", "client_code": "CLB"},
        {"name": "Client C", "email": "c@test.com", "client_code": "CLC"},
    ]

    created_pdfs = []

    for client_data in clients_data:
        # Create client
        client_id = client_manager.add_client(client_data)

        # Create invoice
        invoice_data = create_sample_invoice_data(
            settings=test_generator.settings,
            client_name=client_data["name"],
            client_email=client_data["email"],
            client_code=client_data["client_code"],
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
    assert "Client A" in client_names
    assert "Client B" in client_names
    assert "Client C" in client_names
