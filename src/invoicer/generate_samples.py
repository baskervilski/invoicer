#!/usr/bin/env python3
"""
Generate sample invoices for different project scenarios
"""

from pathlib import Path
from .invoice_generator import InvoiceGenerator, create_invoice_data


def generate_samples():
    """Generate sample invoices for different scenarios"""
    print("📄 Generating sample invoices for different scenarios...")

    scenarios = [
        ("Small Project", "startup@example.com", 5, "C01", "October 2024"),
        ("Medium Project", "corp@example.com", 15, "C02", "October 2024"),
        ("Large Project", "enterprise@example.com", 22, "C03", "October 2024"),
    ]

    generator = InvoiceGenerator()

    for name, email, days, client_code, month in scenarios:
        data = create_invoice_data(name, email, client_code, days, month)
        path = generator.create_invoice(data)
        print(f"✅ {name}: {Path(path).name}")

    print("✅ Sample invoices generated in invoices/ directory")


if __name__ == "__main__":
    generate_samples()
