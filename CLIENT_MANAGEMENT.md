# Client Management System

The Invoice Generator now includes a comprehensive client management system that stores client information and tracks invoice history.

## Features

### 🏢 Client Database
- Store client information (name, email, company, address, phone, notes)
- Automatic client ID generation
- Track invoice history and totals
- Search and filter clients

### 📋 Interactive Client Selection
When creating invoices, you can:
1. **Select from existing clients** - Choose from your client database
2. **Create new clients** - Add client information on-the-fly
3. **Search clients** - Find clients by name, email, or company

### 📊 Client Statistics
- Total number of invoices created
- Last invoice date
- Total amount invoiced
- Client creation date

## Usage

### Main Application
Run the main invoicer application:
```bash
uv run python -m invoicer.main
```

The application will now prompt you to:
1. Select an existing client, or
2. Create a new client, or  
3. Search for a client

### Client Management CLI
Manage clients from the command line:

```bash
# List all clients
uv run python -m invoicer.client_cli list

# Add a new client (interactive)
uv run python -m invoicer.client_cli add

# Search clients
uv run python -m invoicer.client_cli search "acme"

# Show detailed client info
uv run python -m invoicer.client_cli show acme_corporation

# Delete a client
uv run python -m invoicer.client_cli delete client_id

# Create sample clients for testing
uv run python -m invoicer.client_cli init-samples
```

## File Structure

```
src/invoicer/
├── clients/                    # Client data storage
│   ├── clients_index.json     # Client index and metadata
│   ├── acme_corporation.json  # Individual client files
│   ├── techstart_solutions.json
│   └── global_dynamics_inc.json
├── client_manager.py          # Client management logic
├── client_cli.py             # Command-line interface
└── main.py                   # Updated main application
```

## Client Data Format

Each client is stored as a JSON file containing:

```json
{
  "id": "acme_corporation",
  "name": "Acme Corporation",
  "email": "billing@acme-corp.com",
  "address": "123 Business Ave\\nNew York, NY 10001",
  "phone": "+1 (555) 123-4567",
  "company": "Acme Corporation",
  "notes": "Long-term client, payment terms NET 30",
  "created_date": "2024-10-27T21:33:45.123456",
  "last_invoice_date": null,
  "total_invoices": 0,
  "total_amount": 0.0
}
```

## Sample Clients

The system includes three sample clients:
- **Acme Corporation** - billing@acme-corp.com
- **TechStart Solutions** - finance@techstart.io  
- **Global Dynamics Inc** - accounts@globaldynamics.com

## Integration with Invoice Generation

When you create an invoice:
1. The system records the invoice in the client's history
2. Updates `total_invoices` count
3. Updates `last_invoice_date`
4. Accumulates `total_amount`

## Data Privacy

- Client data is stored locally in JSON files
- No data is sent to external services (except Microsoft Graph for email)
- You can exclude the `clients/` directory from version control
- Easy to backup or migrate by copying the `clients/` folder

## Workflow Example

1. **First Time Setup**:
   ```bash
   uv run python -m invoicer.client_cli init-samples
   ```

2. **Create Invoice**:
   ```bash
   uv run python -m invoicer.main
   ```
   - Select "1" to choose existing client
   - Pick "Acme Corporation"
   - Enter days worked: 15
   - Confirm and generate invoice

3. **View Updated Client**:
   ```bash
   uv run python -m invoicer.client_cli show acme_corporation
   ```
   - Shows `total_invoices: 1`
   - Shows updated `last_invoice_date`
   - Shows calculated `total_amount`

This system makes it easy to manage recurring clients and track your invoicing history! 🎉