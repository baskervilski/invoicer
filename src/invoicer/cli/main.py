#!/usr/bin/env python3
"""
Main CLI entry point for the invoicer application.

This module provides the main command-line interface with subcommands for
all invoicer functionality.
"""

import typer
from pathlib import Path
import sys

# Import subcommands
from .. import main as invoicer_main
from .. import demo as invoicer_demo
from .. import generate_samples
from .client import app as client_app
from .config import app as config_app

app = typer.Typer(
    name="invoicer",
    help="Professional Invoice Generator - Create and send PDF invoices with ease",
    no_args_is_help=True,
)

# Add subcommand groups
app.add_typer(client_app, name="client", help="Client management commands")
app.add_typer(config_app, name="config", help="Configuration management commands")


@app.command()
def run():
    """Run the interactive invoice generator"""
    print("🚀 Starting Invoice Generator...")
    try:
        if not invoicer_main.setup_environment():
            sys.exit(1)
        invoicer_main.main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


@app.command()
def demo():
    """Run demo with sample invoices"""
    print("🎭 Running invoice generation demo...")
    try:
        invoicer_demo.demo_invoice_generation()
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        sys.exit(1)


@app.command()
def samples():
    """Generate sample invoices for different scenarios"""
    print("📄 Generating sample invoices for different scenarios...")
    try:
        generate_samples.generate_samples()
    except Exception as e:
        print(f"❌ Error generating samples: {e}")
        sys.exit(1)


@app.command()
def status():
    """Show project status and information"""
    print("📊 Invoice Generator Status")
    print("==========================")

    # Python version
    print(f"Python version: {sys.version.split()[0]}")

    # Check directories
    invoices_dir = Path.cwd() / "invoices"
    clients_dir = Path.cwd() / "clients"

    print(f"Working directory: {Path.cwd()}")
    print(f"Invoices directory: {'Present' if invoices_dir.exists() else 'Missing'}")
    print(f"Clients directory: {'Present' if clients_dir.exists() else 'Missing'}")

    # Count files
    if invoices_dir.exists():
        pdf_count = len(list(invoices_dir.glob("*.pdf")))
        print(f"Generated invoices: {pdf_count} files")

    if clients_dir.exists():
        json_count = len(list(clients_dir.glob("*.json"))) - 1  # Exclude index file
        print(f"Stored clients: {max(0, json_count)} clients")

    # Config file
    env_file = Path.cwd() / ".env"
    print(f"Config file: {'Present' if env_file.exists() else 'Missing'}")


@app.command()
def init():
    """Initialize a new invoicer workspace"""
    print("🚀 Initializing new invoicer workspace...")

    # Create directories
    invoices_dir = Path.cwd() / "invoices"
    clients_dir = Path.cwd() / "clients"

    invoices_dir.mkdir(exist_ok=True)
    clients_dir.mkdir(exist_ok=True)

    print("✅ Created directories:")
    print(f"   📁 {invoices_dir}")
    print(f"   📁 {clients_dir}")

    # Create .env file if it doesn't exist
    env_file = Path.cwd() / ".env"
    if not env_file.exists():
        print("📝 Creating .env configuration file...")
        env_content = """# Company Information
COMPANY_NAME=Your Company Name
COMPANY_ADDRESS="Your Address\nCity, State ZIP\nCountry"
COMPANY_EMAIL=your.email@example.com
COMPANY_PHONE=+1 (555) 123-4567

# Invoice Settings
HOURLY_RATE=75.0
HOURS_PER_DAY=8.0
CURRENCY=EUR
CURRENCY_SYMBOL=€

# Invoice Number Template - Available variables:
# {year} - Full year (e.g., 2024)
# {month} - Month number (1-12) 
# {month:02d} - Zero-padded month (01-12)
# {day} - Day of month (1-31)
# {day:02d} - Zero-padded day (01-31)
# {client_code} - Manually defined client code (e.g., ACM, TSS, GDI)
# {invoice_number} - Sequential invoice number (001, 002, etc.)
INVOICE_NUMBER_TEMPLATE=INV-{year}{month:02d}-{client_code}

# Microsoft Graph API Settings (Required for email)
# Get these from your Microsoft App Registration
MICROSOFT_CLIENT_ID=your-client-id-here
MICROSOFT_CLIENT_SECRET=your-client-secret-here
MICROSOFT_TENANT_ID=your-tenant-id-here
MICROSOFT_REDIRECT_URI=http://localhost:8080/callback
"""
        env_file.write_text(env_content)
        print(f"✅ Created .env file: {env_file}")
        print("   Please edit it with your company details.")
    else:
        print("⚠️  .env file already exists")

    # Create sample clients
    print("📝 Creating sample clients...")
    try:
        from ..client_manager import ClientManager, create_sample_clients

        client_manager = ClientManager()
        create_sample_clients(client_manager)
        print("✅ Sample clients created!")
    except Exception as e:
        print(f"⚠️  Could not create sample clients: {e}")

    print("\n🎉 Workspace initialized successfully!")
    print("\nNext steps:")
    print("  1. Edit .env file with your company details")
    print("  2. Run 'invoicer demo' to test PDF generation")
    print("  3. Run 'invoicer client list' to see sample clients")
    print("  4. Run 'invoicer run' for the full application")


@app.command()
def clean():
    """Clean up generated files"""
    print("🧹 Cleaning generated files...")

    # Clean Python cache
    import shutil

    cache_dirs = [
        Path.cwd() / "__pycache__",
        Path.cwd() / ".pytest_cache",
        Path.cwd() / ".mypy_cache",
        Path.cwd() / ".ruff_cache",
    ]

    for cache_dir in cache_dirs:
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            print(f"   Removed {cache_dir}")

    # Clean invoice PDFs (optional)
    invoices_dir = Path.cwd() / "invoices"
    if invoices_dir.exists():
        pdf_files = list(invoices_dir.glob("*.pdf"))
        if pdf_files:
            confirm = typer.confirm(f"Delete {len(pdf_files)} PDF invoice(s)?")
            if confirm:
                for pdf_file in pdf_files:
                    pdf_file.unlink()
                    print(f"   Deleted {pdf_file.name}")

    print("✅ Cleanup complete")


if __name__ == "__main__":
    app()