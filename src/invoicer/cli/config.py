#!/usr/bin/env python3
"""
Configuration CLI for the invoicer application.

This module provides commands to view and modify configuration settings
with proper validation using Pydantic field validation.
"""

from pathlib import Path
from typing import Annotated, Optional, get_args, get_origin
from pydantic import ValidationError, EmailStr
from pydantic.fields import FieldInfo

import typer

from ..config import settings, InvoicerSettings

app = typer.Typer(
    name="config",
    help="Configuration management commands",
    no_args_is_help=True,
)


def get_field_info(field_name: str) -> FieldInfo:
    """Get field info for a setting from the Pydantic model."""
    return InvoicerSettings.model_fields[field_name]


def validate_field_value(field_name: str, value: str):
    """Validate a field value using Pydantic's validation."""
    try:
        # Create a temporary model instance with just this field to validate
        temp_data = {field_name: value}
        temp_instance = InvoicerSettings(**temp_data)
        return getattr(temp_instance, field_name)
    except ValidationError as e:
        # Extract the error message for this field
        for error in e.errors():
            if error["loc"] == (field_name,):
                raise typer.BadParameter(error["msg"])
        raise typer.BadParameter(f"Validation failed: {str(e)}")


def get_field_type_name(field_name: str) -> str:
    """Get a human-readable type name for a field."""
    annotation = InvoicerSettings.model_fields[field_name].annotation

    if get_origin(annotation) is Annotated:
        base_type = get_args(annotation)[0]
        if base_type is EmailStr:
            return "email"
        elif base_type is Path:
            return "path"
        elif base_type is float:
            return "number"
        elif base_type is list:
            return "list"
        else:
            return str(base_type.__name__) if hasattr(base_type, "__name__") else str(base_type)
    elif annotation is not None:
        return str(annotation.__name__)
    else:
        return str(annotation)


@app.command("show")
def show_config():
    """Show current configuration values."""
    print("📋 Current Configuration")
    print("=" * 50)

    print("\n🏢 Company Information:")
    print(f"  Company Name: {settings.company_name}")
    print(f"  Company Email: {settings.company_email}")
    print(f"  Company Phone: {settings.company_phone}")
    if settings.company_vat:
        print(f"  Company VAT: {settings.company_vat}")
    print("  Company Address:")
    for line in settings.company_address.split("\n"):
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

    # Dynamically categorize fields based on naming patterns
    categories = {}
    for field_name in model_fields.keys():
        if field_name.startswith("company_"):
            category = "Company Information"
        elif field_name.startswith("microsoft_"):
            category = "Microsoft API"
        elif field_name.endswith("_dir"):
            category = "Directories"
        elif field_name in [
            "hourly_rate",
            "hours_per_day",
            "currency",
            "currency_symbol",
            "vat_rate",
            "invoice_number_template",
        ]:
            category = "Invoice Settings"
        else:
            category = "Other Settings"

        if category not in categories:
            categories[category] = []
        categories[category].append(field_name)

    for category, fields in sorted(categories.items()):
        print(f"\n📋 {category}:")
        for field_name in sorted(fields):
            field_info = get_field_info(field_name)
            field_type = get_field_type_name(field_name)
            current_value = getattr(settings, field_name)

            # Hide sensitive values
            if "secret" in field_name.lower() and current_value:
                display_value = "***[HIDDEN]***"
            elif isinstance(current_value, Path):
                display_value = str(current_value)
            elif isinstance(current_value, list):
                display_value = ", ".join(str(item) for item in current_value)
            else:
                display_value = current_value

            print(f"  {field_name}:")
            print(f"    Current: {display_value}")
            print(f"    Type: {field_type}")
            print(f"    Description: {field_info.description}")

            # Show default value if available
            if hasattr(field_info, "default") and field_info.default is not None:
                if callable(field_info.default):
                    print("    Default: <computed>")
                else:
                    print(f"    Default: {field_info.default}")

            # Note: Field constraints would be shown here if needed


@app.command("set")
def set_config(
    setting: Annotated[str, typer.Argument(help="Setting name to change")],
    value: Annotated[str, typer.Argument(help="New value for the setting")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation prompt")] = False,
):
    """Set a configuration value with validation."""

    # Check if setting exists
    if not hasattr(settings, setting):
        available_settings = [field for field in InvoicerSettings.model_fields.keys()]
        print(f"❌ Unknown setting: {setting}")
        print(f"Available settings: {', '.join(available_settings)}")
        raise typer.Exit(1)

    # Get current value and field info
    current_value = getattr(settings, setting)
    field_info = get_field_info(setting)
    field_type = get_field_type_name(setting)

    # Validate the new value using Pydantic's validation
    try:
        validated_value = validate_field_value(setting, value)
    except typer.BadParameter as e:
        print(f"❌ Validation error for {setting} ({field_type}): {e}")
        if field_info.description:
            print(f"💡 Field description: {field_info.description}")
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
    if " " in env_value or any(char in env_value for char in "=\n\r\t\"'"):
        env_value = f'"{env_value}"'

    # Read existing .env file or create new one
    env_lines = []
    if env_file.exists():
        env_lines = env_file.read_text().splitlines()

    # Find and update existing setting or add new one
    updated = False
    for i, line in enumerate(env_lines):
        if line.strip() and not line.strip().startswith("#"):
            if "=" in line:
                key = line.split("=", 1)[0].strip()
                if key == env_key:
                    env_lines[i] = f"{env_key}={env_value}"
                    updated = True
                    break

    # Add new setting if not found
    if not updated:
        env_lines.append(f"{env_key}={env_value}")

    # Write back to file
    env_file.write_text("\n".join(env_lines) + "\n")


@app.command("validate")
def validate_config():
    """Validate all current configuration settings."""
    print("🔍 Validating Configuration")
    print("=" * 40)

    errors = []
    warnings = []

    # Try to validate the entire configuration using Pydantic
    try:
        # Create a new instance to trigger validation
        current_dict = settings.model_dump()
        InvoicerSettings(**current_dict)

        # Check for default/placeholder values
        field_defaults = {
            "company_name": "Your Company Name",
            "company_email": "your.email@example.com",
            "company_phone": "+1 (555) 123-4567",
        }

        for field_name, default_value in field_defaults.items():
            current_value = getattr(settings, field_name)
            if str(current_value) == default_value:
                warnings.append(f"{field_name.replace('_', ' ').title()} is using default placeholder value")

        # Check Microsoft API configuration
        api_fields = [
            settings.microsoft_client_id,
            settings.microsoft_client_secret,
            settings.microsoft_tenant_id,
        ]
        if any(api_fields):  # If any are set, all should be set
            if not all(api_fields):
                warnings.append("Microsoft API configuration is incomplete (some fields missing)")
            else:
                # Check for placeholder values
                if any(field and "your-" in str(field) for field in api_fields):
                    warnings.append("Microsoft API configuration contains placeholder values")
        else:
            warnings.append("Microsoft API not configured (email sending will not work)")

        # Validate directories exist
        for dir_name, field_name in [
            ("Invoices", "invoices_dir"),
            ("Clients", "clients_dir"),
            ("Templates", "templates_dir"),
        ]:
            dir_path = getattr(settings, field_name)
            if not dir_path.exists():
                warnings.append(f"{dir_name} directory does not exist: {dir_path}")
            elif not dir_path.is_dir():
                errors.append(f"{dir_name} path exists but is not a directory: {dir_path}")

    except ValidationError as e:
        for error in e.errors():
            field_name = ".".join(str(loc) for loc in error["loc"])
            errors.append(f"{field_name}: {error['msg']}")

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
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation prompt")] = False,
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
        field_info = get_field_info(setting)
        if hasattr(field_info, "default") and field_info.default is not None:
            default_value = field_info.default
            if callable(default_value):
                # For factory defaults, we need to call the function
                try:
                    default_value = default_value()
                except Exception as e:
                    print(f"❌ Cannot compute default value for {setting}: {e}")
                    raise typer.Exit(1)
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
