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
        print(f"ID: {client.id}")
        print(f"Name: {client.name}")
        print(f"Email: {client.email}")
        print(f"Client Code: {client.client_code}")
        print(f"Total Invoices: {client.total_invoices}")
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

        # Client code - required field for invoice organization
        default_code = name[:3].upper()
        client_code = input(f"Client code (default: {default_code}): ").strip()
        if not client_code:
            client_code = default_code

        address = input("Address (optional): ").strip()
        phone = input("Phone (optional): ").strip()
        notes = input("Notes (optional): ").strip()

        client_data = {
            "name": name,
            "email": email,
            "company": company,
            "client_code": client_code,
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
        print(f"ID: {client.id}")
        print(f"Name: {client.name}")
        print(f"Email: {client.email}")
        print("-" * 40)


@app.command()
def show(client_id: str):
    """Show detailed client information"""
    client_manager = ClientManager()
    client = client_manager.get_client(client_id)

    if not client:
        print(f"Client with ID '{client_id}' not found.")
        return

    print(f"\n👤 Client Details: {client.name}")
    print("=" * 50)
    print(f"ID: {client.id}")
    print(f"Name: {client.name}")
    print(f"Email: {client.email}")
    print(f"Client Code: {client.client_code}")
    print(f"Phone: {client.phone}")
    print(f"Address: {client.address}")
    print(f"Notes: {client.notes}")
    print(f"Created: {client.created_date}")
    print(f"Last Invoice: {client.last_invoice_date or 'Never'}")
    print(f"Total Invoices: {client.total_invoices:,}")
    print(f"Total Amount: ${client.total_amount:,.2f}")


@app.command()
def delete(client_id: str):
    """Delete a client"""
    client_manager = ClientManager()
    client = client_manager.get_client(client_id)

    if not client:
        print(f"Client with ID '{client_id}' not found.")
        return

    print(f"⚠️  Are you sure you want to delete client '{client.name}'?")
    confirm = (
        input("This action cannot be undone. Type 'yes' to confirm: ").strip().lower()
    )

    if confirm == "yes":
        if client_manager.delete_client(client_id):
            print(f"✅ Client '{client.name}' deleted successfully.")
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
