#!/usr/bin/env python3
"""
Generate sample invoices for different project scenarios
"""

from pathlib import Path
from .invoice_generator import InvoiceGenerator, create_sample_invoice_data


def generate_samples():
    """Generate sample invoices for different scenarios"""
    print("📄 Generating sample invoices for different scenarios...")

    scenarios = [
        ("Small Project", "startup@example.com", 5, "October 2024"),
        ("Medium Project", "corp@example.com", 15, "October 2024"),
        ("Large Project", "enterprise@example.com", 22, "October 2024"),
    ]

    generator = InvoiceGenerator()

    for name, email, days, month in scenarios:
        data = create_sample_invoice_data(name, email, days, month)
        path = generator.create_invoice(data)
        print(f"✅ {name}: {Path(path).name}")

    print("✅ Sample invoices generated in invoices/ directory")


if __name__ == "__main__":
    generate_samples()
