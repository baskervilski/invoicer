# Directory Structure

## Overview

The invoicer application stores data files in the current working directory, keeping code and data cleanly separated. This allows you to organize invoices and clients by project or business while keeping the source code portable.

## Current Structure

```
./                     # Current working directory
├── invoices/          # Generated PDF invoices
├── clients/           # Client database files
└── src/invoicer/
    └── templates/     # PDF templates (in module)
```

## Benefits

### 1. **Clean Separation**
- Data files are no longer mixed with source code
- Module directory stays clean and portable
- Better adherence to Unix filesystem conventions

### 2. **User Control**
- Users can organize their invoices and clients by project
- Easy to backup client data separately from code
- Can run invoicer from different directories for different businesses

### 3. **Development Friendly**
- No need to clean up data files when updating the module
- Package installation doesn't include user data
- Easier to version control just the code

## Usage Examples

### Single Business Use
```bash
cd ~/business/accounting/
python -m invoicer.main        # Creates ./invoices/ and ./clients/
```

### Multiple Businesses
```bash
# Business A
cd ~/accounting/business-a/
python -m invoicer.main        # Creates ./invoices/ and ./clients/

# Business B  
cd ~/accounting/business-b/
python -m invoicer.main        # Creates separate ./invoices/ and ./clients/
```

### Project-Based Organization
```bash
# Client Project 1
cd ~/projects/client-alpha/
python -m invoicer.main

# Client Project 2
cd ~/projects/client-beta/
python -m invoicer.main
```

## Directory Contents

### `./clients/`
- `clients_index.json` - Main client database index
- `{client_id}.json` - Individual client data files
- Created automatically when first client is added

### `./invoices/`
- `Invoice_*.pdf` - Generated PDF invoices
- Named with format: `Invoice_{invoice_number}_{client_code}.pdf`
- Created automatically when first invoice is generated

### `src/invoicer/templates/` (unchanged)
- PDF template files (still in module)
- Shared across all installations
- Updated with package updates

## Getting Started

To begin using the invoicer with sample data:

```bash
# Create sample clients
python -m invoicer.client_cli init-samples

# Generate sample invoices
make demo
```

## Configuration

Directory paths are configured in `src/invoicer/config.py`:

```python
# Data directories use current working directory
INVOICES_DIR = Path.cwd() / "invoices"  
CLIENTS_DIR = Path.cwd() / "clients"
TEMPLATES_DIR = Path(__file__).parent / "templates"  # Templates stay in module
```

## Testing

The system automatically creates directories when needed:

```bash
# Test client management
make client-list          # Creates ./clients/ if needed

# Test invoice generation  
make demo                 # Creates ./invoices/ if needed

# Test from different directory
cd /tmp && python -m invoicer.client_cli list  # Creates /tmp/clients/
```

This ensures the invoicer works correctly from any directory while keeping data organized and separate from the source code.