"""
Shared client utilities for interactive client creation.
"""

from typing import Optional

from invoicer.utils import print_with_underline
from .client_manager import ClientManager
from .models import ClientModel


def create_client_interactive(client_manager: ClientManager) -> Optional[ClientModel]:
    """
    Interactive client creation with input validation.

    Args:
        client_manager: ClientManager instance to use for creating the client
        title: Title to display for the creation process

    Returns:
        Optional[ClientModel]: Created client model or None if cancelled/failed
    """
    title = "Create New Client"
    print_with_underline(title)

    try:
        # Required fields
        name = input("Client/Company name: ").strip()
        if not name:
            print("Client name is required.")
            return None

        email = input("Email address: ").strip()
        if not email:
            print("Email address is required.")
            return None

        # Optional fields with defaults
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

        # Ask for initial project name
        project_name = input("Initial project name: ").strip()
        if not project_name:
            print("Project name is required.")
            return None

        # Create client data
        client_data = {
            "name": name,
            "email": email,
            "company": company,
            "client_code": client_code,
            "address": address,
            "phone": phone,
            "notes": notes,
        }

        # Save client
        client_id = client_manager.add_client(client_data)
        
        # Add initial project
        project_id = client_manager.add_project(client_id, project_name)
        
        full_client_data = client_manager.get_client(client_id)

        print(f"\n✅ Client '{name}' created successfully!")
        print(f"✅ Project '{project_name}' added to client!")
        return full_client_data

    except Exception as e:
        print(f"Error creating client: {e}")
        return None


def get_client_creation_data(raise_errors: bool = False) -> Optional[dict]:
    """
    Collect client creation data without actually creating the client.
    Useful for testing or when you want to validate data before creation.

    Returns:
        Optional[dict]: Client data dictionary or None if cancelled/invalid
    """
    # Required fields
    name = input("Client/Company name: ").strip()
    if not name:
        print("Client name is required.")
        if raise_errors:
            raise ValueError("Client name is required.")
        return None

    email = input("Email address: ").strip()
    if not email:
        print("Email address is required.")
        if raise_errors:
            raise ValueError("Email address is required.")
        return None

    # Optional fields with defaults
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
    vat_number = input("VAT number (optional): ").strip()
    notes = input("Notes (optional): ").strip()

    # Ask for initial project name
    project_name = input("Initial project name: ").strip()
    if not project_name:
        print("Project name is required.")
        if raise_errors:
            raise ValueError("Project name is required.")
        return None

    return {
        "name": name,
        "email": email,
        "company": company,
        "client_code": client_code,
        "address": address,
        "phone": phone,
        "vat_number": vat_number,
        "notes": notes,
        "project_name": project_name,
    }
