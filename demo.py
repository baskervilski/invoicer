#!/usr/bin/env python3
"""
Demo script showing the invoice generator functionality
This script demonstrates PDF creation without requiring Microsoft email setup
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from invoice_generator import InvoiceGenerator, create_sample_invoice_data


def demo_invoice_generation():
    """Demonstrate invoice generation with sample data"""
    print("=== Invoice Generator Demo ===")
    print("Creating sample invoices...\n")

    # Sample clients and scenarios
    clients = [
        {
            "name": "Acme Corporation",
            "email": "billing@acme-corp.com",
            "days": 20,
            "month": "October 2024",
        },
        {
            "name": "TechStart Solutions",
            "email": "finance@techstart.io",
            "days": 15,
            "month": "September 2024",
        },
        {
            "name": "Global Dynamics Inc",
            "email": "accounts@globaldynamics.com",
            "days": 12,
            "month": "October 2024",
        },
    ]

    generator = InvoiceGenerator()
    created_invoices = []

    for i, client in enumerate(clients, 1):
        print(f"📄 Creating invoice {i}/3 for {client['name']}...")

        try:
            # Create invoice data
            invoice_data = create_sample_invoice_data(
                client_name=client["name"],
                client_email=client["email"],
                days_worked=client["days"],
                month_year=client["month"],
            )

            # Calculate totals for display
            total_hours = client["days"] * 8.0  # Assuming 8 hours per day
            total_amount = total_hours * 75.0  # Assuming $75/hour

            print(f"   Client: {client['name']}")
            print(f"   Period: {client['month']}")
            print(f"   Days worked: {client['days']}")
            print(f"   Total amount: ${total_amount:.2f}")

            # Generate PDF
            pdf_path = generator.create_invoice(invoice_data)

            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                print(
                    f"   ✅ Invoice created: {os.path.basename(pdf_path)} ({file_size} bytes)"
                )
                created_invoices.append(pdf_path)
            else:
                print(f"   ❌ Failed to create invoice")

            print()

        except Exception as e:
            print(f"   ❌ Error creating invoice: {e}")
            print()

    # Summary
    print("=== Demo Summary ===")
    print(f"Successfully created {len(created_invoices)} invoices:")
    for invoice_path in created_invoices:
        print(f"  📄 {os.path.basename(invoice_path)}")

    print(f"\nInvoices saved in: {os.path.join(os.getcwd(), 'invoices')}")
    print("\n💡 To use the full application with email functionality:")
    print("   1. Set up Microsoft App Registration (see README.md)")
    print("   2. Update .env file with your credentials")
    print("   3. Run: python main.py")


if __name__ == "__main__":
    demo_invoice_generation()
