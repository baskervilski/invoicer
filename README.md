# Invoice Generator & Email Sender

A professional Python application that creates PDF invoices based on days worked and automatically sends them via Microsoft email integration.

## Features

- 📄 **Professional PDF Invoice Generation**: Creates beautifully formatted invoices with your company branding
- 📧 **Microsoft Email Integration**: Sends invoices directly through your Microsoft email account
- ⚙️ **Configurable Settings**: Customize rates, company info, and invoice templates
- 🎨 **Professional Styling**: Clean, modern invoice design with company colors
- 📊 **Automatic Calculations**: Calculates totals based on days worked, hours per day, and hourly rate
- 🔐 **Secure Authentication**: Uses Microsoft OAuth2 for secure email access

## Prerequisites

- Python 3.10 or higher
- Microsoft 365 account (for sending emails)
- Microsoft App Registration (for email API access)

## Quick Start

### Using the CLI (Recommended)

The easiest way to get started is using the direct CLI commands:

```bash
# Complete setup (installs UV, dependencies, creates config)
make setup

# Initialize workspace and try the demo
uv run invoicer init
uv run invoicer demo

# Run the full application
uv run invoicer run
```

### Using Make (Alternative)

You can also use the provided Makefile:

```bash
# Complete setup (installs UV, dependencies, creates config)  
make setup

# Try the demo (no configuration needed)
make demo

# Run the full application
make run
```

### Manual Installation

1. **Clone or download this project**
   ```bash
   cd /home/nemanja/projects/personal/invoicer
   ```

2. **Install UV package manager** (recommended)
   ```bash
   make install-uv
   # or manually: curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**
   ```bash
   make install
   # or with pip: pip install -e .
   ```

## Available Make Commands

Run `make help` to see all available commands:

- **Environment Setup**: `make setup`, `make install`, `make install-uv`
- **Development**: `make run`, `make demo`, `make test`
- **Code Quality**: `make lint`, `make format`, `make typecheck`
- **Configuration**: `make check-env`, `make show-config`, `make init-env`
- **Maintenance**: `make clean`, `make update`

## Microsoft App Registration Setup

To send emails via Microsoft Graph API, you need to register an application:

1. **Go to Azure Portal**: https://portal.azure.com/
2. **Navigate to**: Azure Active Directory → App registrations → New registration
3. **Configure the app**:
   - Name: "Invoice Generator"
   - Supported account types: "Accounts in this organizational directory only"
   - Redirect URI: Web → `http://localhost:8080/callback`

4. **Get credentials**:
   - **Application (client) ID**: Copy this value
   - **Directory (tenant) ID**: Copy this value
   - **Client Secret**: Go to "Certificates & secrets" → "New client secret" → Copy the value

5. **Set API permissions**:
   - Go to "API permissions" → "Add a permission" → "Microsoft Graph" → "Delegated permissions"
   - Add: `Mail.Send` and `User.Read`
   - Click "Grant admin consent"

## Configuration

1. **Update the `.env` file** (created automatically on first run):
   ```env
   # Company Information
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
   INVOICE_NUMBER_TEMPLATE=INV-{year}{month:02d}-{client_code}

   # Microsoft Graph API Settings
   MICROSOFT_CLIENT_ID=your-client-id-from-azure
   MICROSOFT_CLIENT_SECRET=your-client-secret-from-azure
   MICROSOFT_TENANT_ID=your-tenant-id-from-azure
   MICROSOFT_REDIRECT_URI=http://localhost:8080/callback
   ```

## Usage

### Running the Application

**Using Make (Recommended):**
```bash
make run
```

**Direct Python:**
```bash
python main.py
# or with UV: uv run python main.py
```

### Quick Demo

To test without any configuration:
```bash
make demo
```

### Interactive Process

The application will guide you through:

1. **Client Information**: Enter client name and email
2. **Work Details**: Specify days worked for the month
3. **Invoice Generation**: PDF is created automatically
4. **Email Sending**: Choose whether to send via email

### Example Workflow

```
=== Invoice Generator ===
Please provide the following information:
Client name: Acme Corp
Client email: billing@acmecorp.com
Number of days worked this month: 15
Month/Year (default: October 2024): 
Project description (default: Consulting services for October 2024): 

📋 Invoice Summary:
   Client: Acme Corp
   Email: billing@acmecorp.com
   Period: October 2024
   Days worked: 15
   Hours per day: 8.0
   Hourly rate: €75
   Total hours: 120.0
   Total amount: €9,000.00

Proceed with invoice creation? (y/n): y

📄 Generating PDF invoice...
✅ Invoice created: /home/nemanja/projects/personal/invoicer/invoices/Invoice_INV-202410-ACM_Acme_Corp.pdf

📧 Send this invoice via email? (y/n): y
```

## File Structure

```
invoicer/
├── src/invoicer/          # Python module
│   ├── main.py            # Main application entry point
│   ├── invoice_generator.py # PDF invoice generation
│   ├── email_sender.py    # Microsoft Graph email integration
│   ├── client_manager.py  # Client database management
│   ├── client_cli.py      # Client management CLI
│   └── config.py          # Configuration management
├── .env                   # Environment variables (created on first run)
├── invoices/              # Generated PDF invoices (organized by year/client)
│   └── 2025/              # Year-based organization
│       ├── ACM/           # Client code directories
│       ├── TSS/           
│       └── GDI/           
├── clients/               # Client database files (created in CWD)
├── Makefile              # Development and build commands
└── pyproject.toml        # Project dependencies
```

**Note**: The `invoices/` and `clients/` directories are created in your current working directory. Invoices are automatically organized by year and client code (e.g., `invoices/2025/ACM/Invoice_INV-202510-ACM.pdf`) for easy organization and retrieval.

## Customization

### Client Codes & Organization

Each client has a manually defined **client code** (e.g., "ACM", "TSS", "GDI") used for:
- Invoice numbering and templates
- Directory organization (`invoices/2025/ACM/`)
- Easy identification and sorting

When adding clients, you'll be prompted for a client code (defaults to first 3 letters of company name).

### Invoice Number Templates

Customize your invoice numbering scheme in the `.env` file:

```env
# Available template variables:
# {year} - Full year (e.g., 2024)
# {month} - Month number (1-12)
# {month:02d} - Zero-padded month (01-12)
# {day} - Day of month (1-31)
# {day:02d} - Zero-padded day (01-31)
# {client_code} - Manually defined client code (e.g., ACM, TSS)
# {invoice_number} - Sequential invoice number (001, 002, etc.)

# Examples:
INVOICE_NUMBER_TEMPLATE=INV-{year}{month:02d}-{client_code}    # INV-202410-ACM
INVOICE_NUMBER_TEMPLATE={client_code}-{year}-{invoice_number}  # ACM-2024-001
INVOICE_NUMBER_TEMPLATE={year}-{invoice_number}                # 2024-001
```

### Directory Structure

Invoices are automatically organized in a hierarchical structure:
```
invoices/
├── 2025/
│   ├── ACM/
│   │   ├── Invoice_INV-202510-ACM.pdf
│   │   └── Invoice_INV-202511-ACM.pdf
│   ├── TSS/
│   │   └── Invoice_INV-202510-TSS.pdf
│   └── GDI/
│       └── Invoice_INV-202510-GDI.pdf
└── 2024/
    └── ACM/
        └── Invoice_INV-202412-ACM.pdf
```

This organization makes it easy to find invoices by year and client, backup client-specific data, and maintain clean file organization as your business grows.

### Invoice Styling

Edit `invoice_generator.py` to customize:
- Colors and fonts
- Company logo (add logo handling in `_build_header`)
- Layout and spacing
- Additional fields

### Email Templates

Modify `create_invoice_email_body()` in `email_sender.py` to customize the email format.

### Configuration

Update `config.py` to add new settings or modify defaults.

## Troubleshooting

### Common Issues

1. **Import Errors**: Install dependencies with `pip install -e .`
2. **Authentication Fails**: Check Microsoft app registration and credentials
3. **Email Not Sending**: Verify API permissions and admin consent
4. **PDF Generation Fails**: Ensure `invoices/` directory exists and is writable

### Microsoft Graph API Issues

- **401 Unauthorized**: Check client ID, secret, and tenant ID
- **403 Forbidden**: Ensure API permissions are granted and admin consent given
- **Redirect URI Mismatch**: Verify redirect URI matches exactly in Azure portal

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- Client secrets should be rotated periodically
- Use least-privilege permissions in Microsoft Graph

## License

This project is for personal/business use. Modify as needed for your requirements.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify Microsoft app registration setup
3. Ensure all dependencies are installed
4. Check that configuration values are correct