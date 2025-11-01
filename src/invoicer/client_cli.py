#!/usr/bin/env python3
"""
Client Management CLI Tool

This tool allows you to manage client data from the command line.
"""

import typer

from invoicer.utils import print_with_underline
from .client_manager import ClientManager
from .client_utils import create_client_interactive

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

    print_with_underline(f"\n📋 All Clients ({len(clients)} found):")

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

    created_client = create_client_interactive(client_manager)

    if created_client:
        print(f"Client created with ID: {created_client.id}")
    else:
        print("Client creation cancelled or failed.")


@app.command()
def search(query: str):
    """Search clients by name, email, or company"""
    client_manager = ClientManager()
    results = client_manager.search_clients(query)

    if not results:
        print(f"No clients found matching '{query}'")
        return

    print_with_underline(f"\n🔍 Search Results for '{query}' ({len(results)} found):")

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

    print_with_underline(f"\n👤 Client Details: {client.name}")
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
def delete(client_ids: str):
    """Delete one or more clients (provide comma-separated list of IDs)"""
    client_manager = ClientManager()

    # Parse client IDs - handle both single ID and comma-separated list
    id_list = [id_str.strip() for id_str in client_ids.split(",") if id_str.strip()]

    if not id_list:
        print("❌ No client IDs provided.")
        return

    # Validate all client IDs exist and get client info
    clients_to_delete = []
    missing_ids = []

    for client_id in id_list:
        client = client_manager.get_client(client_id)
        if client:
            clients_to_delete.append(client)
        else:
            missing_ids.append(client_id)

    # Report missing clients
    if missing_ids:
        print(f"⚠️  Client(s) not found: {', '.join(missing_ids)}")
        if not clients_to_delete:
            return

    # Show clients to be deleted
    if len(clients_to_delete) == 1:
        print(
            f"⚠️  Are you sure you want to delete client '{clients_to_delete[0].name}'?"
        )
    else:
        print(f"⚠️  Are you sure you want to delete {len(clients_to_delete)} clients?")
        for client in clients_to_delete:
            print(f"   - {client.name} ({client.id})")

    confirm = (
        input("This action cannot be undone. Type 'yes' to confirm: ").strip().lower()
    )

    if confirm == "yes":
        successful_deletions = 0
        failed_deletions = []

        for client in clients_to_delete:
            if client_manager.delete_client(client.id):
                print(f"✅ Client '{client.name}' deleted successfully.")
                successful_deletions += 1
            else:
                print(f"❌ Failed to delete client '{client.name}'.")
                failed_deletions.append(client.name)

        # Summary
        print(f"\nSummary: {successful_deletions} client(s) deleted successfully.")
        if failed_deletions:
            print(f"Failed to delete: {', '.join(failed_deletions)}")
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
