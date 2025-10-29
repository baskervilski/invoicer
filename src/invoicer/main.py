#!/usr/bin/env python3
"""
Invoice Generator and Email Sender

This application creates professional PDF invoices based on days worked
and sends them via Microsoft email.
"""

from pathlib import Path
import sys
from datetime import datetime
from typing import Optional

from invoicer.models import ClientModel, InvoiceModel

from .invoice_generator import InvoiceGenerator, create_sample_invoice_data
from .email_sender import EmailSender
from .client_manager import ClientManager, create_sample_clients
from .config import settings


def main():
    """Main application function"""
    print("=== Invoice Generator ===")
    print("Creates and sends professional PDF invoices\n")

    try:
        # Get invoice details from user
        invoice_data = get_invoice_details()

        if not invoice_data:
            print("Invoice creation cancelled.")
            return

        # Generate PDF invoice
        print("\n📄 Generating PDF invoice...")
        generator = InvoiceGenerator(settings=settings)
        pdf_path = generator.create_invoice(invoice_data)
        print(f"✅ Invoice created: {pdf_path}")

        # Record invoice creation in client database
        if invoice_data.client_info.client_id:
            # TODO: Update record_invoice to accept InvoiceModel instead of dict
            pass

        # Ask if user wants to send email
        send_email = input("\n📧 Send this invoice via email? (y/n): ").lower().strip()

        if send_email in ["y", "yes"]:
            send_invoice_email(invoice_data, pdf_path)
        else:
            print(f"Invoice saved to: {pdf_path}")
            print("You can send it manually when ready.")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def select_or_create_client() -> Optional[ClientModel]:
    """
    Allow user to select existing client or create new one

    Returns:
        Optional[ClientModel]: Client data or None if cancelled
    """
    client_manager = ClientManager()

    # Check if we have existing clients
    existing_clients = client_manager.list_clients()

    if not existing_clients:
        print("📝 No existing clients found. Let's create your first client!")
        return create_new_client(client_manager)

    # Show options
    print("\n👥 Client Selection")
    print("=" * 50)
    print("Choose an option:")
    print("1. Select from existing clients")
    print("2. Create new client")
    print("3. Search clients")

    while True:
        choice = input("\nEnter your choice (1-3): ").strip()

        if choice == "1":
            return select_existing_client(client_manager)
        elif choice == "2":
            return create_new_client(client_manager)
        elif choice == "3":
            return search_and_select_client(client_manager)
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def select_existing_client(client_manager: ClientManager) -> Optional[ClientModel]:
    """Select from existing clients"""
    clients = client_manager.list_clients()

    print(f"\n📋 Existing Clients ({len(clients)} found):")
    print("=" * 50)

    for i, client in enumerate(clients, 1):
        if client.last_invoice_date:
            last_invoice_str = client.last_invoice_date.strftime("%Y-%m-%d")
        else:
            last_invoice_str = "Never"

        print(f"{i:2d}. {client.name}")
        print(f"     Email: {client.email}")
        print(f"     Last Invoice: {last_invoice_str}")
        print(f"     Total Invoices: {client.total_invoices}")
        print()

    while True:
        try:
            choice = input(
                f"Select client (1-{len(clients)}) or 'b' to go back: "
            ).strip()

            if choice.lower() == "b":
                return select_or_create_client()

            client_index = int(choice) - 1
            if 0 <= client_index < len(clients):
                selected_client = clients[client_index]
                # Get full client data
                full_client_data = client_manager.get_client(selected_client.id)
                print(f"\n✅ Selected: {selected_client.name}")
                return full_client_data
            else:
                print("Invalid selection. Please try again.")

        except ValueError:
            print("Please enter a valid number or 'b' to go back.")


def search_and_select_client(client_manager: ClientManager) -> Optional[ClientModel]:
    """Search and select client"""
    query = input("🔍 Enter search term (name, email, or company): ").strip()
    if not query:
        return select_or_create_client()

    results = client_manager.search_clients(query)

    if not results:
        print(f"No clients found matching '{query}'")
        retry = input("Try another search? (y/n): ").strip().lower()
        if retry == "y":
            return search_and_select_client(client_manager)
        else:
            return select_or_create_client()

    print(f"\n🔍 Search Results for '{query}' ({len(results)} found):")
    print("=" * 50)

    for i, client in enumerate(results, 1):
        print(f"{i:2d}. {client.name} ({client.email})")

    while True:
        try:
            choice = input(
                f"\nSelect client (1-{len(results)}) or 'b' to go back: "
            ).strip()

            if choice.lower() == "b":
                return select_or_create_client()

            client_index = int(choice) - 1
            if 0 <= client_index < len(results):
                selected_client = results[client_index]
                full_client_data = client_manager.get_client(selected_client.id)
                print(f"\n✅ Selected: {selected_client.name}")
                return full_client_data
            else:
                print("Invalid selection. Please try again.")

        except ValueError:
            print("Please enter a valid number or 'b' to go back.")


def create_new_client(client_manager: ClientManager) -> Optional[ClientModel]:
    """Create a new client"""
    print("\n📝 Create New Client")
    print("=" * 50)

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

        # Optional fields
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
        full_client_data = client_manager.get_client(client_id)

        print(f"\n✅ Client '{name}' created successfully!")
        return full_client_data

    except Exception as e:
        print(f"Error creating client: {e}")
        return None


def get_invoice_details() -> Optional[InvoiceModel]:
    """
    Get invoice details from user input

    Returns:
        Optional[InvoiceModel]: Invoice data or None if cancelled
    """
    try:
        # First, select or create client
        client_data = select_or_create_client()
        if not client_data:
            return None

        print(f"\n📋 Creating invoice for: {client_data.name}")
        print("=" * 50)

        # Days worked
        while True:
            try:
                days_str = input("Number of days worked this month: ").strip()
                days_worked = int(days_str)
                if days_worked <= 0:
                    print("Days worked must be greater than 0.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number.")

        # Month/Year (optional)
        current_month = datetime.now().strftime("%B %Y")
        month_year = input(f"Month/Year (default: {current_month}): ").strip()
        if not month_year:
            month_year = current_month

        # Project description (optional)
        default_description = f"Consulting services for {month_year}"
        project_description = input(
            f"Project description (default: {default_description}): "
        ).strip()
        if not project_description:
            project_description = default_description

        # Calculate totals for display
        total_hours = days_worked * settings.hours_per_day
        subtotal = total_hours * settings.hourly_rate

        # Display summary
        print("\n📋 Invoice Summary:")
        print(f"   Client: {client_data.name}")
        print(f"   Email: {client_data.email}")
        print(f"   Period: {month_year}")
        print(f"   Days worked: {days_worked:,}")
        print(f"   Hours per day: {settings.hours_per_day:,.1f}")
        print(f"   Hourly rate: {settings.currency_symbol}{settings.hourly_rate:,.2f}")
        print(f"   Total hours: {total_hours:,.1f}")
        print(f"   Total amount: {settings.currency_symbol}{subtotal:,.2f}")

        # Confirm
        confirm = input("\nProceed with invoice creation? (y/n): ").lower().strip()
        if confirm not in ["y", "yes"]:
            return None

        # Create invoice data
        invoice_data = create_sample_invoice_data(
            settings=settings,
            client_name=client_data.name,
            client_email=client_data.email,
            client_code=client_data.client_code,
            days_worked=days_worked,
            month_year=month_year,
        )

        # Update the project description
        invoice_data.project_description = project_description

        # Set the client ID in the client_info
        invoice_data.client_info.client_id = client_data.id

        return invoice_data

    except Exception as e:
        print(f"Error getting invoice details: {e}")
        return None


def send_invoice_email(invoice_data: InvoiceModel, pdf_path: Path) -> bool:
    """
    Send invoice via email

    Args:
        invoice_data: InvoiceModel containing invoice information
        pdf_path: Path to the PDF invoice file

    Returns:
        bool: True if email sent successfully
    """
    try:
        print("\n📧 Preparing to send email...")

        # Initialize email sender
        email_sender = EmailSender()

        # Authenticate
        print("🔐 Authenticating with Microsoft...")
        if not email_sender.authenticate():
            print("❌ Authentication failed. Email not sent.")
            return False

        print("✅ Authentication successful!")

        # Prepare email content
        client_name = invoice_data.client_info.name
        client_email = invoice_data.client_info.email
        invoice_number = invoice_data.invoice_number
        month_year = invoice_data.period or datetime.now().strftime("%B %Y")

        # Use the total amount from the invoice model
        total_amount = invoice_data.total_amount

        subject = f"Invoice {invoice_number} - {month_year} Services"
        body = email_sender.create_invoice_email_body(
            client_name,
            invoice_number,
            f"{settings.currency_symbol}{total_amount:,.2f}",
            month_year,
        )

        # Send email
        print(f"📤 Sending invoice to {client_email}...")
        success = email_sender.send_email(client_email, subject, body, pdf_path)

        if success:
            print("✅ Invoice sent successfully!")
        else:
            print("❌ Failed to send invoice.")

        return success

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


def setup_environment():
    """
    Check and setup the environment
    """
    print("🔧 Checking environment setup...")

    # Check if .env file exists
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        create_env_file(env_file)

    # Check required configurations
    missing_configs = []

    if not settings.microsoft_client_id:
        missing_configs.append("MICROSOFT_CLIENT_ID")
    if not settings.microsoft_client_secret:
        missing_configs.append("MICROSOFT_CLIENT_SECRET")
    if not settings.microsoft_tenant_id:
        missing_configs.append("MICROSOFT_TENANT_ID")

    if missing_configs:
        print("\n⚠️  Missing required Microsoft Graph API configurations:")
        for config_name in missing_configs:
            print(f"   - {config_name}")
        print("\nPlease update the .env file with your Microsoft app credentials.")
        print("See README.md for setup instructions.")
        return False

    # Initialize client database with sample clients if empty
    client_manager = ClientManager()
    existing_clients = client_manager.list_clients()
    if not existing_clients:
        print("📝 Setting up sample clients...")
        create_sample_clients(client_manager)
        print("✅ Sample clients created!")

    print("✅ Environment setup complete!")
    return True


def create_env_file(env_file: Path):
    """
    Create a sample .env file

    Args:
        env_file: Path to the .env file
    """
    env_content = """# Company Information
COMPANY_NAME=Your Company Name
COMPANY_ADDRESS=Your Address
City, State ZIP
Country
COMPANY_EMAIL=your.email@example.com
COMPANY_PHONE=+1 (555) 123-4567

# Invoice Settings
HOURLY_RATE=75.0
HOURS_PER_DAY=8.0
CURRENCY=EUR
CURRENCY_SYMBOL=€

# Microsoft Graph API Settings (Required for email)
# Get these from your Microsoft App Registration
MICROSOFT_CLIENT_ID=your-client-id-here
MICROSOFT_CLIENT_SECRET=your-client-secret-here
MICROSOFT_TENANT_ID=your-tenant-id-here
MICROSOFT_REDIRECT_URI=http://localhost:8080/callback
"""

    env_file.write_text(env_content)

    print(f"📝 Created sample .env file: {env_file}")
    print("Please update it with your actual values.")


if __name__ == "__main__":
    if not setup_environment():
        sys.exit(1)

    main()
