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

from .invoice_generator import InvoiceGenerator, create_sample_invoice_data
from .email_sender import EmailSender
from . import config


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
        generator = InvoiceGenerator()
        pdf_path = generator.create_invoice(invoice_data)
        print(f"✅ Invoice created: {pdf_path}")

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


def get_invoice_details() -> Optional[dict]:
    """
    Get invoice details from user input

    Returns:
        Optional[dict]: Invoice data or None if cancelled
    """
    try:
        print("Please provide the following information:")

        # Client information
        client_name = input("Client name: ").strip()
        if not client_name:
            print("Client name is required.")
            return None

        client_email = input("Client email: ").strip()
        if not client_email:
            print("Client email is required.")
            return None

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
        total_hours = days_worked * config.HOURS_PER_DAY
        subtotal = total_hours * config.HOURLY_RATE

        # Display summary
        print("\n📋 Invoice Summary:")
        print(f"   Client: {client_name}")
        print(f"   Email: {client_email}")
        print(f"   Period: {month_year}")
        print(f"   Days worked: {days_worked}")
        print(f"   Hours per day: {config.HOURS_PER_DAY}")
        print(f"   Hourly rate: {config.CURRENCY_SYMBOL}{config.HOURLY_RATE}")
        print(f"   Total hours: {total_hours}")
        print(f"   Total amount: {config.CURRENCY_SYMBOL}{subtotal:.2f}")

        # Confirm
        confirm = input("\nProceed with invoice creation? (y/n): ").lower().strip()
        if confirm not in ["y", "yes"]:
            return None

        # Create invoice data
        invoice_data = create_sample_invoice_data(
            client_name, client_email, days_worked, month_year
        )
        invoice_data["project_description"] = project_description

        return invoice_data

    except Exception as e:
        print(f"Error getting invoice details: {e}")
        return None


def send_invoice_email(invoice_data: dict, pdf_path: Path) -> bool:
    """
    Send invoice via email

    Args:
        invoice_data: Invoice data dictionary
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
        client_name = invoice_data["client_info"]["name"]
        client_email = invoice_data["client_info"]["email"]
        invoice_number = invoice_data["invoice_number"]
        month_year = invoice_data["period"]

        # Calculate total amount
        days_worked = invoice_data["days_worked"]
        total_hours = days_worked * config.HOURS_PER_DAY
        total_amount = total_hours * config.HOURLY_RATE

        subject = f"Invoice {invoice_number} - {month_year} Services"
        body = email_sender.create_invoice_email_body(
            client_name,
            invoice_number,
            f"{config.CURRENCY_SYMBOL}{total_amount:.2f}",
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

    if not config.CLIENT_ID:
        missing_configs.append("MICROSOFT_CLIENT_ID")
    if not config.CLIENT_SECRET:
        missing_configs.append("MICROSOFT_CLIENT_SECRET")
    if not config.TENANT_ID:
        missing_configs.append("MICROSOFT_TENANT_ID")

    if missing_configs:
        print("\n⚠️  Missing required Microsoft Graph API configurations:")
        for config_name in missing_configs:
            print(f"   - {config_name}")
        print("\nPlease update the .env file with your Microsoft app credentials.")
        print("See README.md for setup instructions.")
        return False

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
CURRENCY=USD
CURRENCY_SYMBOL=$

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
