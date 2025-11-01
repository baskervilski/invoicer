#!/usr/bin/env python3
"""
Demo script showing the invoice generator functionality
This script demonstrates PDF creation without requiring Microsoft email setup
"""

from pathlib import Path
from .invoice_generator import InvoiceGenerator, create_invoice_data
from .config import settings


def demo_invoice_generation():
    """Demonstrate invoice generation with sample data"""
    print("=== Invoice Generator Demo ===")
    print("Creating sample invoices...\n")

    # Sample clients and scenarios
    clients = [
        {
            "name": "Acme Corporation",
            "email": "billing@acme-corp.com",
            "client_code": "ACM",
            "days": 20,
            "month": "October 2024",
        },
        {
            "name": "TechStart Solutions",
            "email": "finance@techstart.io",
            "client_code": "TSS",
            "days": 15,
            "month": "September 2024",
        },
        {
            "name": "Global Dynamics Inc",
            "email": "accounts@globaldynamics.com",
            "client_code": "GDI",
            "days": 12,
            "month": "October 2024",
        },
    ]

    generator = InvoiceGenerator(settings=settings)
    created_invoices = []

    for i, client in enumerate(clients, 1):
        print(f"📄 Creating invoice {i}/3 for {client['name']}...")

        try:
            # Create invoice data
            invoice_data = create_invoice_data(
                settings=settings,
                client_name=client["name"],
                client_email=client["email"],
                client_code=client["client_code"],
                days_worked=client["days"],
                month_year=client["month"],
            )

            # Calculate totals for display
            total_hours = client["days"] * 8.0  # Assuming 8 hours per day
            total_amount = total_hours * settings.hourly_rate

            print(f"   Client: {client['name']}")
            print(f"   Period: {client['month']}")
            print(f"   Days worked: {client['days']:,}")
            print(f"   Total amount: {settings.currency_symbol}{total_amount:,.2f}")

            # Generate PDF
            pdf_path = generator.create_invoice(invoice_data)

            pdf_path_obj = Path(pdf_path)
            if pdf_path_obj.exists():
                file_size = pdf_path_obj.stat().st_size
                print(f"   ✅ Invoice created: {pdf_path_obj.name} ({file_size} bytes)")
                created_invoices.append(pdf_path)
            else:
                print("   ❌ Failed to create invoice")

            print()

        except Exception as e:
            print(f"   ❌ Error creating invoice: {e}")
            print()

    # Summary
    print("=== Demo Summary ===")
    print(f"Successfully created {len(created_invoices)} invoices:")
    for invoice_path in created_invoices:
        print(f"  📄 {Path(invoice_path).name}")

    print(f"\nInvoices saved in: {Path.cwd() / 'invoices'}")
    print("\n💡 To use the full application with email functionality:")
    print("   1. Set up Microsoft App Registration (see README.md)")
    print("   2. Update .env file with your credentials")
    print("   3. Run: python main.py")


if __name__ == "__main__":
    demo_invoice_generation()
