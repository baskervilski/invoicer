"""
Tests for the configuration CLI functionality.
"""

import pytest
from typer.testing import CliRunner
from pathlib import Path
import tempfile
import os

from src.invoicer.config_cli import app


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("""COMPANY_NAME=Test Company
COMPANY_EMAIL=test@example.com
HOURLY_RATE=50.0
VAT_RATE=0.20
CURRENCY=USD
""")
        temp_path = f.name
    
    # Change to the directory containing the temp file
    original_cwd = os.getcwd()
    temp_dir = os.path.dirname(temp_path)
    os.chdir(temp_dir)
    
    # Rename to .env
    env_path = os.path.join(temp_dir, '.env')
    os.rename(temp_path, env_path)
    
    yield env_path
    
    # Cleanup
    os.chdir(original_cwd)
    if os.path.exists(env_path):
        os.unlink(env_path)


def test_config_show_command(runner):
    """Test the config show command."""
    result = runner.invoke(app, ["show"])
    assert result.exit_code == 0
    assert "Current Configuration" in result.stdout
    assert "Company Information" in result.stdout
    assert "Invoice Settings" in result.stdout


def test_config_list_command(runner):
    """Test the config list command."""
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Configurable Settings" in result.stdout
    assert "company_name" in result.stdout
    assert "hourly_rate" in result.stdout


def test_config_validate_command(runner):
    """Test the config validate command."""
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0
    assert "Validating Configuration" in result.stdout


def test_config_set_invalid_setting(runner):
    """Test setting an invalid configuration setting."""
    result = runner.invoke(app, ["set", "invalid_setting", "value"])
    assert result.exit_code == 1
    assert "Unknown setting" in result.stdout


def test_config_set_invalid_email(runner):
    """Test setting an invalid email address."""
    result = runner.invoke(app, ["set", "company_email", "invalid-email"])
    assert result.exit_code == 1
    assert "Invalid email address format" in result.stdout


def test_config_set_invalid_hourly_rate(runner):
    """Test setting an invalid hourly rate."""
    result = runner.invoke(app, ["set", "--", "hourly_rate", "-10"])
    assert result.exit_code == 1
    assert "must be greater than 0" in result.stdout


def test_config_set_invalid_currency(runner):
    """Test setting an invalid currency code."""
    result = runner.invoke(app, ["set", "currency", "INVALID"])
    assert result.exit_code == 1
    assert "3 uppercase letters" in result.stdout


def test_config_set_invalid_vat_rate(runner):
    """Test setting an invalid VAT rate."""
    result = runner.invoke(app, ["set", "vat_rate", "150"])
    assert result.exit_code == 1
    assert "VAT rate must be between" in result.stdout


def test_config_set_invalid_template(runner):
    """Test setting an invalid invoice template."""
    result = runner.invoke(app, ["set", "invoice_number_template", "INV-{invalid_var}"])
    assert result.exit_code == 1
    assert "Invalid template format" in result.stdout


def test_vat_rate_percentage_conversion():
    """Test VAT rate conversion from percentage to decimal."""
    from src.invoicer.config_cli import validate_vat_rate
    
    # Test percentage format (should convert to decimal)
    assert validate_vat_rate("21") == 0.21
    assert validate_vat_rate("19.5") == 0.195
    
    # Test decimal format (should remain as-is)
    assert validate_vat_rate("0.21") == 0.21
    assert validate_vat_rate("0.195") == 0.195
    
    # Test invalid values
    with pytest.raises(Exception):
        validate_vat_rate("150")  # Too high
    with pytest.raises(Exception):
        validate_vat_rate("-5")   # Negative


def test_currency_validation():
    """Test currency code validation."""
    from src.invoicer.config_cli import validate_currency_code
    
    # Valid currency codes
    assert validate_currency_code("USD") == "USD"
    assert validate_currency_code("eur") == "EUR"  # Should convert to uppercase
    assert validate_currency_code("gbp") == "GBP"
    
    # Invalid currency codes
    with pytest.raises(Exception):
        validate_currency_code("US")      # Too short
    with pytest.raises(Exception):
        validate_currency_code("USDD")    # Too long
    with pytest.raises(Exception):
        validate_currency_code("123")     # Numbers not allowed


def test_email_validation():
    """Test email validation."""
    from src.invoicer.config_cli import validate_email
    
    # Valid emails
    assert validate_email("test@example.com") == True
    assert validate_email("user.name@domain.co.uk") == True
    assert validate_email("test+tag@example.org") == True
    
    # Invalid emails
    assert validate_email("invalid-email") == False
    assert validate_email("@example.com") == False
    assert validate_email("test@") == False
    assert validate_email("") == False


def test_phone_validation():
    """Test phone number validation."""
    from src.invoicer.config_cli import validate_phone
    
    # Valid phone numbers
    assert validate_phone("+1 (555) 123-4567") == True
    assert validate_phone("+32 472 904 555") == True
    assert validate_phone("+44-20-7946-0958") == True
    assert validate_phone("555-123-4567") == True
    
    # Invalid phone numbers
    assert validate_phone("123") == False
    assert validate_phone("abc-def-ghij") == False
    assert validate_phone("") == False


def test_template_validation():
    """Test invoice template validation."""
    from src.invoicer.config_cli import validate_template
    
    # Valid templates
    assert validate_template("INV-{year}{month:02d}-{client_code}") == True
    assert validate_template("INV-{year}-{client_code}-{invoice_number}") == True
    assert validate_template("{client_code}-{year}{month}{day}") == True
    
    # Invalid templates
    assert validate_template("INV-{invalid_var}") == False
    assert validate_template("INV-{year}{month:invalid}") == False


if __name__ == "__main__":
    pytest.main([__file__])