#!/usr/bin/env python3
"""
Client Management CLI Tool

This tool allows you to manage client data from the command line.
"""

import typer
from typing import Optional

from invoicer.utils import print_with_underline
from .client_manager import ClientManager
from .client_utils import create_client_interactive

app = typer.Typer(
    name="client-cli",
    help="Client Management CLI Tool - Manage client data from the command line",
    no_args_is_help=True,
)

# Create a sub-app for project management
project_app = typer.Typer(
    name="project",
    help="Project management commands",
    no_args_is_help=True,
)

# Add the project sub-app to the main client app
app.add_typer(project_app, name="project")


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
    
    # Show projects
    projects = client_manager.list_projects(client_id)
    if projects:
        print(f"\n📂 Projects ({len(projects)}):")
        for project in projects:
            print(f"  - {project.name} (ID: {project.id})")
            print(f"    Created: {project.created_date}")
    else:
        print("\n📂 Projects: None")


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


# Project management commands
@project_app.command("add")
def add_project(project_name: str, client_id: Optional[str] = typer.Argument(None, help="Client ID (if not provided, you'll be prompted to select)")):
    """Add a new project to an existing client"""
    client_manager = ClientManager()
    
    # If client_id not provided, let user select
    if client_id is None:
        from .main import select_client
        client = select_client()
        if not client:
            print("❌ No client selected. Project creation cancelled.")
            return
        client_id = client.id
    else:
        # Check if provided client exists
        client = client_manager.get_client(client_id)
        if not client:
            print(f"❌ Client with ID '{client_id}' not found.")
            return
    
    # Add project
    project_id = client_manager.add_project(client_id, project_name)
    
    if project_id:
        print(f"✅ Project '{project_name}' added to client '{client.name}'!")
        print(f"Project ID: {project_id}")
    else:
        print(f"❌ Failed to add project '{project_name}'.")


@project_app.command("list")
def list_projects(client_id: str):
    """List all projects for a client"""
    client_manager = ClientManager()
    
    # Check if client exists
    client = client_manager.get_client(client_id)
    if not client:
        print(f"❌ Client with ID '{client_id}' not found.")
        return
    
    projects = client_manager.list_projects(client_id)
    
    if not projects:
        print(f"📂 No projects found for client '{client.name}'.")
        return
    
    print_with_underline(f"\n📂 Projects for '{client.name}' ({len(projects)} found):")
    
    for project in projects:
        print(f"ID: {project.id}")
        print(f"Name: {project.name}")
        print(f"Created: {project.created_date}")
        print("-" * 40)


@project_app.command("show")
def show_project(project_id: str):
    """Show detailed project information"""
    client_manager = ClientManager()
    project = client_manager.get_project(project_id)
    
    if not project:
        print(f"❌ Project with ID '{project_id}' not found.")
        return
    
    # Get client info
    client = client_manager.get_client(project.client_id)
    client_name = client.name if client else "Unknown Client"
    
    print_with_underline(f"\n📂 Project Details: {project.name}")
    print(f"ID: {project.id}")
    print(f"Name: {project.name}")
    print(f"Client: {client_name} ({project.client_id})")
    print(f"Created: {project.created_date}")


@project_app.command("delete")
def delete_project(project_id: str):
    """Delete a project"""
    client_manager = ClientManager()
    project = client_manager.get_project(project_id)
    
    if not project:
        print(f"❌ Project with ID '{project_id}' not found.")
        return
    
    # Get client info for confirmation
    client = client_manager.get_client(project.client_id)
    client_name = client.name if client else "Unknown Client"
    
    print(f"⚠️  Are you sure you want to delete project '{project.name}' from client '{client_name}'?")
    confirm = input("This action cannot be undone. Type 'yes' to confirm: ").strip().lower()
    
    if confirm == "yes":
        if client_manager.delete_project(project_id):
            print(f"✅ Project '{project.name}' deleted successfully.")
        else:
            print(f"❌ Failed to delete project '{project.name}'.")
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
