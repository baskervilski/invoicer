#!/usr/bin/env python3
"""
Test script for invoice generation without email functionality
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from invoice_generator import InvoiceGenerator, create_sample_invoice_data


def test_pdf_generation():
    """Test PDF invoice generation"""
    print("🧪 Testing PDF invoice generation...")

    try:
        # Create sample invoice data
        invoice_data = create_sample_invoice_data(
            client_name="Test Client Corp",
            client_email="test@example.com",
            days_worked=10,
            month_year="October 2024",
        )

        print(f"📋 Test Invoice Data:")
        print(f"   Client: {invoice_data['client_info']['name']}")
        print(f"   Days worked: {invoice_data['days_worked']}")
        print(f"   Invoice number: {invoice_data['invoice_number']}")

        # Generate PDF
        generator = InvoiceGenerator()
        pdf_path = generator.create_invoice(invoice_data)

        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"✅ PDF generated successfully!")
            print(f"   File: {pdf_path}")
            print(f"   Size: {file_size} bytes")
            return True
        else:
            print("❌ PDF file was not created")
            return False

    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("=== Invoice Generator Test ===\n")

    success = test_pdf_generation()

    if success:
        print("\n✅ Test completed successfully!")
        print("The invoice generator is working correctly.")
    else:
        print("\n❌ Test failed!")
        print("Please check the error messages above.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
