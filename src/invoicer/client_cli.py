#!/usr/bin/env python3
"""
Client Management CLI Tool

This tool allows you to manage client data from the command line.
"""

import typer
from .client_manager import ClientManager

app = typer.Typer(
    name="client-cli",
    help="Client Management CLI Tool - Manage client data from the command line",
    no_args_is_help=True,
)


@app.command("list")
def list_clients():
    """List all clients"""
    client_manager = ClientManager()
    clients = client_manager.list_clients()

    if not clients:
        print("No clients found. Use 'add' to create your first client.")
        return

    print(f"\n📋 All Clients ({len(clients)} found):")
    print("=" * 70)

    for client in clients:
        print(f"ID: {client['id']}")
        print(f"Name: {client['name']}")
        print(f"Email: {client['email']}")
        print(f"Company: {client.get('company', 'N/A')}")
        print(f"Total Invoices: {client.get('total_invoices', 0)}")
        print("-" * 50)


@app.command()
def add():
    """Add a new client (interactive)"""
    client_manager = ClientManager()
    print("\n📝 Add New Client")
    print("=" * 30)

    try:
        name = input("Client/Company name: ").strip()
        if not name:
            print("Client name is required.")
            return

        email = input("Email address: ").strip()
        if not email:
            print("Email address is required.")
            return

        company = input(f"Company name (default: {name}): ").strip()
        if not company:
            company = name

        address = input("Address (optional): ").strip()
        phone = input("Phone (optional): ").strip()
        notes = input("Notes (optional): ").strip()

        client_data = {
            "name": name,
            "email": email,
            "company": company,
            "address": address,
            "phone": phone,
            "notes": notes,
        }

        client_id = client_manager.add_client(client_data)
        print(f"\n✅ Client '{name}' created with ID: {client_id}")

    except Exception as e:
        print(f"Error creating client: {e}")


@app.command()
def search(query: str):
    """Search clients by name, email, or company"""
    client_manager = ClientManager()
    results = client_manager.search_clients(query)

    if not results:
        print(f"No clients found matching '{query}'")
        return

    print(f"\n🔍 Search Results for '{query}' ({len(results)} found):")
    print("=" * 60)

    for client in results:
        print(f"ID: {client['id']}")
        print(f"Name: {client['name']}")
        print(f"Email: {client['email']}")
        print(f"Company: {client.get('company', 'N/A')}")
        print("-" * 40)


@app.command()
def show(client_id: str):
    """Show detailed client information"""
    client_manager = ClientManager()
    client = client_manager.get_client(client_id)

    if not client:
        print(f"Client with ID '{client_id}' not found.")
        return

    print(f"\n👤 Client Details: {client['name']}")
    print("=" * 50)
    print(f"ID: {client['id']}")
    print(f"Name: {client['name']}")
    print(f"Email: {client['email']}")
    print(f"Company: {client.get('company', 'N/A')}")
    print(f"Phone: {client.get('phone', 'N/A')}")
    print(f"Address: {client.get('address', 'N/A')}")
    print(f"Notes: {client.get('notes', 'N/A')}")
    print(f"Created: {client.get('created_date', 'N/A')}")
    print(f"Last Invoice: {client.get('last_invoice_date', 'Never')}")
    print(f"Total Invoices: {client.get('total_invoices', 0):,}")
    print(f"Total Amount: ${client.get('total_amount', 0.0):,.2f}")


@app.command()
def delete(client_id: str):
    """Delete a client"""
    client_manager = ClientManager()
    client = client_manager.get_client(client_id)

    if not client:
        print(f"Client with ID '{client_id}' not found.")
        return

    print(f"⚠️  Are you sure you want to delete client '{client['name']}'?")
    confirm = (
        input("This action cannot be undone. Type 'yes' to confirm: ").strip().lower()
    )

    if confirm == "yes":
        if client_manager.delete_client(client_id):
            print(f"✅ Client '{client['name']}' deleted successfully.")
        else:
            print("❌ Failed to delete client.")
    else:
        print("Deletion cancelled.")


@app.command("init-samples")
def init_samples():
    """Create sample clients for testing"""
    from .client_manager import create_sample_clients

    client_manager = ClientManager()
    create_sample_clients(client_manager)
    print("✅ Sample clients created!")


if __name__ == "__main__":
    app()
