#!/usr/bin/env python3
"""
Client Management CLI Tool

This tool allows you to manage client data from the command line.
"""

import sys
from .client_manager import ClientManager, create_sample_clients


def main():
    """Main CLI function"""
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()
    client_manager = ClientManager()

    if command == "list":
        list_clients(client_manager)
    elif command == "add":
        add_client_interactive(client_manager)
    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: python -m invoicer.client_cli search <query>")
            return
        search_clients(client_manager, " ".join(sys.argv[2:]))
    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: python -m invoicer.client_cli show <client_id>")
            return
        show_client(client_manager, sys.argv[2])
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Usage: python -m invoicer.client_cli delete <client_id>")
            return
        delete_client(client_manager, sys.argv[2])
    elif command == "init-samples":
        create_sample_clients(client_manager)
        print("✅ Sample clients created!")
    else:
        show_help()


def show_help():
    """Show help information"""
    print("Client Management CLI")
    print("====================")
    print("")
    print("Usage: python -m invoicer.client_cli <command> [args]")
    print("")
    print("Commands:")
    print("  list           List all clients")
    print("  add            Add a new client (interactive)")
    print("  search <query> Search clients by name, email, or company")
    print("  show <id>      Show detailed client information")
    print("  delete <id>    Delete a client")
    print("  init-samples   Create sample clients for testing")
    print("")


def list_clients(client_manager: ClientManager):
    """List all clients"""
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


def add_client_interactive(client_manager: ClientManager):
    """Add client interactively"""
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


def search_clients(client_manager: ClientManager, query: str):
    """Search clients"""
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


def show_client(client_manager: ClientManager, client_id: str):
    """Show detailed client information"""
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
    print(f"Total Invoices: {client.get('total_invoices', 0)}")
    print(f"Total Amount: ${client.get('total_amount', 0.0):.2f}")


def delete_client(client_manager: ClientManager, client_id: str):
    """Delete a client"""
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


if __name__ == "__main__":
    main()
