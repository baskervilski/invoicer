#!/usr/bin/env python3
"""
Configuration CLI for the invoicer application.

This module provides commands to view and modify configuration settings
with proper validation.
"""

import typer
from pathlib import Path
from typing import Optional, List, Annotated
import re
from decimal import Decimal
from pydantic import ValidationError, EmailStr
import json

from .config import settings, InvoicerSettings

app = typer.Typer(
    name="config",
    help="Configuration management commands",
    no_args_is_help=True,
)


def validate_email(email: str) -> bool:
    """Validate email address format."""
    try:
        # Use pydantic's email validation
        from pydantic import BaseModel
        
        class EmailModel(BaseModel):
            email: EmailStr
        
        EmailModel(email=email)
        return True
    except (ValidationError, Exception):
        return False


def validate_positive_float(value: str, field_name: str) -> float:
    """Validate that a string represents a positive float."""
    try:
        float_val = float(value)
        if float_val <= 0:
            raise typer.BadParameter(f"{field_name} must be greater than 0")
        return float_val
    except ValueError:
        raise typer.BadParameter(f"{field_name} must be a valid number")


def validate_vat_rate(value: str) -> float:
    """Validate VAT rate (0-100% or 0.0-1.0)."""
    try:
        float_val = float(value)
        # Accept both percentage (0-100) and decimal (0.0-1.0) formats
        if 1 < float_val <= 100:
            float_val = float_val / 100  # Convert percentage to decimal
        elif not (0 <= float_val <= 1):
            raise typer.BadParameter("VAT rate must be between 0-100% or 0.0-1.0")
        return float_val
    except ValueError:
        raise typer.BadParameter("VAT rate must be a valid number")


def validate_phone(value: str) -> bool:
    """Validate phone number format (basic check)."""
    # Allow common phone formats: +1 (555) 123-4567, +1-555-123-4567, etc.
    phone_pattern = r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$'
    return bool(re.match(phone_pattern, value.strip()))


def validate_currency_code(value: str) -> str:
    """Validate currency code (3 uppercase letters)."""
    if not re.match(r'^[A-Z]{3}$', value.upper()):
        raise typer.BadParameter("Currency code must be 3 uppercase letters (e.g., USD, EUR, GBP)")
    return value.upper()


def validate_template(template: str) -> bool:
    """Validate invoice number template format."""
    # Check for valid template variables
    valid_vars = {'year', 'month', 'day', 'client_code', 'invoice_number'}
    
    # Find all variables in template
    import re
    found_vars = set(re.findall(r'\{(\w+)(?::.*?)?\}', template))
    
    # Check if all variables are valid
    invalid_vars = found_vars - valid_vars
    if invalid_vars:
        return False
    
    # Try to format with sample data
    try:
        template.format(
            year=2024,
            month=12,
            day=31,
            client_code='TST',
            invoice_number='001'
        )
        return True
    except (KeyError, ValueError):
        return False


@app.command("show")
def show_config():
    """Show current configuration values."""
    print("📋 Current Configuration")
    print("=" * 50)
    
    print("\n🏢 Company Information:")
    print(f"  Company Name: {settings.company_name}")
    print(f"  Company Email: {settings.company_email}")
    print(f"  Company Phone: {settings.company_phone}")
    print(f"  Company Address:")
    for line in settings.company_address.split('\n'):
        print(f"    {line}")
    
    print("\n💰 Invoice Settings:")
    print(f"  Hourly Rate: {settings.currency_symbol}{settings.hourly_rate}")
    print(f"  Hours per Day: {settings.hours_per_day}")
    print(f"  Currency: {settings.currency} ({settings.currency_symbol})")
    print(f"  VAT Rate: {settings.vat_rate:.1%}")
    print(f"  Invoice Template: {settings.invoice_number_template}")
    
    print("\n📁 Directory Settings:")
    print(f"  Invoices Directory: {settings.invoices_dir}")
    print(f"  Clients Directory: {settings.clients_dir}")
    print(f"  Templates Directory: {settings.templates_dir}")
    
    print("\n🔗 Microsoft API Settings:")
    has_client_id = bool(settings.microsoft_client_id)
    has_client_secret = bool(settings.microsoft_client_secret)
    has_tenant_id = bool(settings.microsoft_tenant_id)
    
    print(f"  Client ID: {'✅ Set' if has_client_id else '❌ Not set'}")
    print(f"  Client Secret: {'✅ Set' if has_client_secret else '❌ Not set'}")
    print(f"  Tenant ID: {'✅ Set' if has_tenant_id else '❌ Not set'}")
    print(f"  Redirect URI: {settings.microsoft_redirect_uri}")
    print(f"  Scopes: {', '.join(settings.microsoft_scopes)}")


@app.command("list")
def list_configurable():
    """List all configurable settings with their current values and descriptions."""
    print("⚙️  Configurable Settings")
    print("=" * 50)
    
        # Get field info from the pydantic model
    model_fields = InvoicerSettings.model_fields
    
    categories = {
        'Company Information': [
            'company_name', 'company_email', 'company_phone', 'company_address'
        ],
        'Invoice Settings': [
            'hourly_rate', 'hours_per_day', 'currency', 'currency_symbol', 
            'vat_rate', 'invoice_number_template'
        ],
        'Microsoft API': [
            'microsoft_client_id', 'microsoft_client_secret', 'microsoft_tenant_id',
            'microsoft_redirect_uri'
        ],
        'Directories': [
            'invoices_dir', 'clients_dir'
        ]
    }
    
    for category, fields in categories.items():
        print(f"\n📋 {category}:")
        for field_name in fields:
            if field_name in model_fields:
                field_info = model_fields[field_name]
                current_value = getattr(settings, field_name)
                
                # Hide sensitive values
                if 'secret' in field_name.lower() and current_value:
                    display_value = "***[HIDDEN]***"
                elif isinstance(current_value, Path):
                    display_value = str(current_value)
                else:
                    display_value = current_value
                
                print(f"  {field_name}:")
                print(f"    Current: {display_value}")
                print(f"    Description: {field_info.description}")
                if hasattr(field_info, 'default'):
                    print(f"    Default: {field_info.default}")


@app.command("set")
def set_config(
    setting: Annotated[str, typer.Argument(help="Setting name to change")],
    value: Annotated[str, typer.Argument(help="New value for the setting")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation prompt")] = False
):
    """Set a configuration value with validation."""
    
    # Check if setting exists
    if not hasattr(settings, setting):
        available_settings = [field for field in InvoicerSettings.model_fields.keys()]
        print(f"❌ Unknown setting: {setting}")
        print(f"Available settings: {', '.join(available_settings)}")
        raise typer.Exit(1)
    
    # Get current value
    current_value = getattr(settings, setting)
    field_info = InvoicerSettings.model_fields[setting]
    
    # Validate the new value based on field type and constraints
    try:
        if setting == 'company_email':
            if not validate_email(value):
                raise typer.BadParameter("Invalid email address format")
            validated_value = value
            
        elif setting == 'company_phone':
            if not validate_phone(value):
                raise typer.BadParameter("Invalid phone number format")
            validated_value = value
            
        elif setting in ['hourly_rate', 'hours_per_day']:
            validated_value = validate_positive_float(value, setting.replace('_', ' ').title())
            
        elif setting == 'vat_rate':
            validated_value = validate_vat_rate(value)
            
        elif setting == 'currency':
            validated_value = validate_currency_code(value)
            
        elif setting == 'invoice_number_template':
            if not validate_template(value):
                raise typer.BadParameter(
                    "Invalid template format. Available variables: "
                    "{year}, {month}, {day}, {client_code}, {invoice_number}"
                )
            validated_value = value
            
        elif setting in ['invoices_dir', 'clients_dir']:
            path_value = Path(value)
            if not path_value.is_absolute():
                path_value = Path.cwd() / path_value
            validated_value = path_value
            
        else:
            # For other string fields, just use the value as-is
            validated_value = value
    
    except typer.BadParameter as e:
        print(f"❌ Validation error: {e}")
        raise typer.Exit(1)
    
    # Show what will change
    if isinstance(current_value, Path):
        current_display = str(current_value)
    else:
        current_display = current_value
        
    if isinstance(validated_value, Path):
        new_display = str(validated_value)
    else:
        new_display = validated_value
    
    print(f"Setting: {setting}")
    print(f"Current value: {current_display}")
    print(f"New value: {new_display}")
    
    # Confirm change unless --force is used
    if not force:
        confirmed = typer.confirm("Do you want to apply this change?")
        if not confirmed:
            print("❌ Change cancelled")
            raise typer.Exit(1)
    
    # Apply the change by updating the .env file
    try:
        update_env_file(setting, validated_value)
        print(f"✅ Successfully updated {setting}")
        print("💡 Note: Restart the application for changes to take effect")
        
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        raise typer.Exit(1)


def update_env_file(setting: str, value) -> None:
    """Update the .env file with a new setting value."""
    env_file = Path.cwd() / ".env"
    
    # Convert setting name to ENV format (lowercase to uppercase with underscores)
    env_key = setting.upper()
    
    # Format value for .env file
    if isinstance(value, Path):
        env_value = str(value)
    elif isinstance(value, bool):
        env_value = str(value).lower()
    elif isinstance(value, (int, float)):
        env_value = str(value)
    else:
        env_value = str(value)
    
    # Quote values that contain spaces or special characters
    if ' ' in env_value or any(char in env_value for char in '=\n\r\t"\''):
        env_value = f'"{env_value}"'
    
    # Read existing .env file or create new one
    env_lines = []
    if env_file.exists():
        env_lines = env_file.read_text().splitlines()
    
    # Find and update existing setting or add new one
    updated = False
    for i, line in enumerate(env_lines):
        if line.strip() and not line.strip().startswith('#'):
            if '=' in line:
                key = line.split('=', 1)[0].strip()
                if key == env_key:
                    env_lines[i] = f"{env_key}={env_value}"
                    updated = True
                    break
    
    # Add new setting if not found
    if not updated:
        env_lines.append(f"{env_key}={env_value}")
    
    # Write back to file
    env_file.write_text('\n'.join(env_lines) + '\n')


@app.command("validate")
def validate_config():
    """Validate all current configuration settings."""
    print("🔍 Validating Configuration")
    print("=" * 40)
    
    errors = []
    warnings = []
    
    # Validate company information
    if not settings.company_name or settings.company_name == "Your Company Name":
        warnings.append("Company name is not set or using default value")
    
    if not validate_email(str(settings.company_email)):
        errors.append("Company email is invalid")
    elif str(settings.company_email) == "your.email@example.com":
        warnings.append("Company email is using default placeholder value")
    
    if not validate_phone(settings.company_phone):
        errors.append("Company phone number format is invalid")
    
    # Validate invoice settings
    if settings.hourly_rate <= 0:
        errors.append("Hourly rate must be greater than 0")
    
    if settings.hours_per_day <= 0:
        errors.append("Hours per day must be greater than 0")
    
    if not (0 <= settings.vat_rate <= 1):
        errors.append("VAT rate must be between 0.0 and 1.0")
    
    if not validate_template(settings.invoice_number_template):
        errors.append("Invoice number template is invalid")
    
    # Validate Microsoft API settings
    api_fields = [settings.microsoft_client_id, settings.microsoft_client_secret, settings.microsoft_tenant_id]
    if any(api_fields):  # If any are set, all should be set
        if not all(api_fields):
            warnings.append("Microsoft API configuration is incomplete (some fields missing)")
        else:
            # Check for placeholder values
            if any(field and 'your-' in str(field) for field in api_fields):
                warnings.append("Microsoft API configuration contains placeholder values")
    else:
        warnings.append("Microsoft API not configured (email sending will not work)")
    
    # Validate directories
    for dir_name, dir_path in [
        ("Invoices", settings.invoices_dir),
        ("Clients", settings.clients_dir),
        ("Templates", settings.templates_dir)
    ]:
        if not dir_path.exists():
            warnings.append(f"{dir_name} directory does not exist: {dir_path}")
        elif not dir_path.is_dir():
            errors.append(f"{dir_name} path exists but is not a directory: {dir_path}")
    
    # Print results
    if errors:
        print("❌ Errors found:")
        for error in errors:
            print(f"  • {error}")
    
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"  • {warning}")
    
    if not errors and not warnings:
        print("✅ Configuration is valid!")
    elif not errors:
        print(f"\n✅ Configuration is functional with {len(warnings)} warning(s)")
    else:
        print(f"\n❌ Configuration has {len(errors)} error(s) that need attention")
        raise typer.Exit(1)


@app.command("reset")
def reset_config(
    setting: Annotated[Optional[str], typer.Argument(help="Setting to reset (or all)")] = None,
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation prompt")] = False
):
    """Reset configuration setting(s) to default values."""
    
    if setting == "all":
        # Reset entire .env file
        if not force:
            confirmed = typer.confirm("This will reset ALL settings to defaults. Continue?")
            if not confirmed:
                print("❌ Reset cancelled")
                raise typer.Exit(1)
        
        env_file = Path.cwd() / ".env"
        if env_file.exists():
            env_file.unlink()
            print("✅ All settings reset to defaults")
            print("💡 Run 'invoicer init' to recreate .env file with defaults")
        else:
            print("ℹ️  No .env file found - settings are already at defaults")
            
    elif setting:
        # Reset specific setting
        if not hasattr(settings, setting):
            available_settings = [field for field in InvoicerSettings.model_fields.keys()]
            print(f"❌ Unknown setting: {setting}")
            print(f"Available settings: {', '.join(available_settings)}")
            raise typer.Exit(1)
        
        # Get default value
        field_info = InvoicerSettings.model_fields[setting]
        if hasattr(field_info, 'default'):
            default_value = field_info.default
        else:
            print(f"❌ No default value available for {setting}")
            raise typer.Exit(1)
        
        current_value = getattr(settings, setting)
        
        print(f"Setting: {setting}")
        print(f"Current value: {current_value}")
        print(f"Default value: {default_value}")
        
        if not force:
            confirmed = typer.confirm("Reset this setting to default?")
            if not confirmed:
                print("❌ Reset cancelled")
                raise typer.Exit(1)
        
        try:
            update_env_file(setting, default_value)
            print(f"✅ Reset {setting} to default value")
            print("💡 Restart the application for changes to take effect")
        except Exception as e:
            print(f"❌ Error resetting setting: {e}")
            raise typer.Exit(1)
    else:
        print("❌ Please specify a setting name or 'all'")
        print("Use 'invoicer config list' to see available settings")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()