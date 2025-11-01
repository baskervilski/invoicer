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
import calendar

from invoicer.models import ClientModel, InvoiceModel
from invoicer.utils import print_with_underline

from .invoice_generator import InvoiceGenerator, create_sample_invoice_data
from .email_sender import EmailSender
from .client_manager import ClientManager, create_sample_clients
from .config import settings


def get_last_day_of_month(month_year_str: str) -> datetime:
    """
    Get the last day of the specified month.

    Args:
        month_year_str: Month/year string like "November 2025" or "Nov 2025"

    Returns:
        datetime: Last day of the month at 23:59:59
    """
    try:
        # Parse the month/year string
        month_year = datetime.strptime(month_year_str, "%B %Y")
    except ValueError:
        try:
            # Try abbreviated month format
            month_year = datetime.strptime(month_year_str, "%b %Y")
        except ValueError:
            # Fallback to current month if parsing fails
            month_year = datetime.now()

    # Get the last day of the month
    last_day = calendar.monthrange(month_year.year, month_year.month)[1]
    return datetime(month_year.year, month_year.month, last_day, 23, 59, 59)


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


def select_client() -> Optional[ClientModel]:
    """
    Allow user to select from existing clients

    Returns:
        Optional[ClientModel]: Client data or None if cancelled
    """
    client_manager = ClientManager()

    # Check if we have existing clients
    existing_clients = client_manager.list_clients()

    if not existing_clients:
        print("❌ No existing clients found!")
        print("\n💡 To create clients, use one of these methods:")
        print("   • Command line: invoicer client add")
        print("   • Python API: from client_utils import create_client_interactive")
        print("\nPlease create at least one client before generating invoices.")
        return None

    # Ask user how they want to select a client
    print_with_underline("\n👥 Client Selection")
    print("How would you like to select a client?")
    print("1. Search by name/email/company")
    print("2. Browse numbered list")

    while True:
        choice = input("\nEnter your choice ([1]/2): ").strip() or "1"
        
        if choice == "1":
            return _search_clients(client_manager)
        elif choice == "2":
            return _browse_clients(client_manager, existing_clients)
        else:
            print("Invalid choice. Please enter 1 or 2.")


def _browse_clients(client_manager: ClientManager, clients: list) -> Optional[ClientModel]:
    """Show numbered client list for selection"""
    print_with_underline(f"\n📋 Browse Clients ({len(clients)} found):")

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
            ).strip().lower()

            if choice == "b":
                return select_client()

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


def _search_clients(client_manager: ClientManager) -> Optional[ClientModel]:
    """Search for clients and allow selection"""
    while True:
        query = input("🔍 Enter search term (name, email, or company): ").strip()
        if not query:
            return select_client()

        results = client_manager.search_clients(query)

        if not results:
            print(f"No clients found matching '{query}'")
            retry = input("Try another search? ([y]/n): ").strip().lower() or "y"
            if retry != "y":
                return select_client()
            continue

        # Show search results using the browse function
        print(f"\n🔍 Search results for '{query}':")
        return _browse_clients(client_manager, results)


def get_invoice_details() -> Optional[InvoiceModel]:
    """
    Get invoice details from user input

    Returns:
        Optional[InvoiceModel]: Invoice data or None if cancelled
    """
    try:
        # First, select client
        client_data = select_client()
        if not client_data:
            return None

        print_with_underline(f"\n📋 Creating invoice for: {client_data.name}")

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

        # Invoice date selection
        print("\n📅 Invoice Date Selection:")
        current_date = datetime.now()
        last_day_of_month = get_last_day_of_month(month_year)

        print(
            f"1. Last day of {month_year} ({last_day_of_month.strftime('%Y-%m-%d')}) [default]"
        )
        print(f"2. Today ({current_date.strftime('%Y-%m-%d')})")

        while True:
            choice = input("Choose invoice date ([1]/2): ").strip() or "1"
            if choice == "1":
                invoice_date = last_day_of_month
                break
            elif choice == "2":
                invoice_date = current_date
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")

        # Calculate totals for display
        total_hours = days_worked * settings.hours_per_day
        subtotal = total_hours * settings.hourly_rate
        vat_amount = subtotal * settings.vat_rate
        total_with_vat = subtotal + vat_amount

        # Display summary
        print("\n📋 Invoice Summary:")
        print(f"   Client: {client_data.name}")
        print(f"   Email: {client_data.email}")
        print(f"   Period: {month_year}")
        print(f"   Days worked: {days_worked:,}")
        print(f"   Hours per day: {settings.hours_per_day:,.1f}")
        print(f"   Hourly rate: {settings.currency_symbol}{settings.hourly_rate:,.2f}")
        print(f"   Total hours: {total_hours:,.1f}")
        print(f"   Subtotal: {settings.currency_symbol}{subtotal:,.2f}")
        if settings.vat_rate > 0:
            print(
                f"   VAT ({settings.vat_rate * 100:.1f}%): {settings.currency_symbol}{vat_amount:,.2f}"
            )
        print(f"   Total amount: {settings.currency_symbol}{total_with_vat:,.2f}")

        # Confirm
        confirm = (
            input("\nProceed with invoice creation? ([y]/n): ").lower().strip() or "y"
        )
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
            invoice_date=invoice_date,
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
VAT_RATE=0.21

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
