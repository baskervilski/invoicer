# Invoicer CLI Commands

The invoicer application now provides a comprehensive command-line interface that allows you to run all functionality directly without needing the Makefile.

## Usage

```bash
# Direct CLI (with UV)
uv run invoicer [command]

# Using the wrapper script (system-wide)
./bin/invoicer [command]

# Or add to PATH for global access
export PATH="$PATH:/path/to/invoicer/bin"
invoicer [command]

# Legacy Makefile (still supported)
make [target]
```

## Available Commands

### Main Application
```bash
invoicer run           # Run the interactive invoice generator
invoicer demo          # Run demo with sample invoices  
invoicer samples       # Generate sample invoices for different scenarios
```

### Client Management
```bash
invoicer client list                    # List all clients
invoicer client add                     # Add a new client (interactive)
invoicer client search "query"          # Search clients by name, email, or company
invoicer client show client_id          # Show detailed client information
invoicer client delete client_id        # Delete a client
invoicer client init-samples            # Create sample clients for testing
```

### Configuration & Status
```bash
invoicer config        # Show current configuration
invoicer status        # Show project status and information
invoicer init          # Initialize a new invoicer workspace
invoicer clean         # Clean up generated files
```

### System Information
```bash
invoicer --help        # Show main help
invoicer client --help # Show client management help
```

## Examples

### Quick Start
```bash
# Initialize a new workspace
invoicer init

# Create sample clients and invoices
invoicer demo

# List clients
invoicer client list

# Run the full application
invoicer run
```

### Working with Clients
```bash
# Add a new client
invoicer client add

# Find clients
invoicer client search "Acme"

# Show client details
invoicer client show acme_corporation

# Delete client
invoicer client delete old_client_id
```

### Project Management
```bash
# Check status
invoicer status

# View configuration
invoicer config

# Clean up files
invoicer clean
```

## Directory Structure

Commands work with the current working directory:

```bash
# Work with different projects
cd ~/business/project-a
invoicer client list    # Shows clients for project-a

cd ~/business/project-b  
invoicer client list    # Shows clients for project-b

# Initialize new workspace
cd ~/new-client
invoicer init           # Creates ./invoices/ and ./clients/
```

## Integration with Makefile

The Makefile now uses the CLI commands internally, so both approaches work:

```bash
# These are equivalent:
make demo          <-->  uv run invoicer demo
make client-list   <-->  uv run invoicer client list
make status        <-->  uv run invoicer status
```

## Installation for System-Wide Access

To use `invoicer` commands from anywhere:

1. **Add to PATH** (recommended):
   ```bash
   echo 'export PATH="$PATH:/path/to/invoicer/bin"' >> ~/.bashrc
   source ~/.bashrc
   ```

2. **Create symlink**:
   ```bash
   ln -s /path/to/invoicer/bin/invoicer /usr/local/bin/invoicer
   ```

3. **Use UV directly**:
   ```bash
   alias invoicer="cd /path/to/invoicer && uv run invoicer"
   ```

## Benefits

✅ **Simplified Commands**: Clean, memorable command structure  
✅ **Consistent Interface**: All functionality through one entry point  
✅ **Better Help**: Rich, contextual help messages  
✅ **Type Safety**: Automatic argument validation  
✅ **Shell Completion**: Built-in autocompletion support  
✅ **Portable**: Works from any directory while managing data locally  

The CLI provides a modern, professional interface while maintaining full backward compatibility with existing Makefile workflows.