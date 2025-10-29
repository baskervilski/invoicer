"""
Unit tests for configuration settings using pydantic_settings.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from invoicer.config import InvoicerSettings, settings


def test_settings_from_environment():
    """Test that settings can be loaded from environment variables."""
    with patch.dict(
        os.environ,
        {
            "COMPANY_NAME": "Test Company",
            "HOURLY_RATE": "100.0",
            "HOURS_PER_DAY": "7.5",
            "CURRENCY": "USD",
            "CURRENCY_SYMBOL": "$",
            "MICROSOFT_CLIENT_ID": "test-client-id",
        },
    ):
        test_settings = InvoicerSettings()

        assert test_settings.company_name == "Test Company"
        assert test_settings.hourly_rate == 100.0
        assert test_settings.hours_per_day == 7.5
        assert test_settings.currency == "USD"
        assert test_settings.currency_symbol == "$"
        assert test_settings.microsoft_client_id == "test-client-id"


def test_settings_validation():
    """Test that settings validation works."""
    # Test invalid hourly rate (should be > 0)
    try:
        InvoicerSettings(hourly_rate=-10.0)
        assert False, "Should have raised validation error"
    except Exception:
        pass  # Expected validation error

    # Test invalid email format
    try:
        InvoicerSettings(company_email="invalid-email")
        assert False, "Should have raised validation error"
    except Exception:
        pass  # Expected validation error


def test_directories_creation():
    """Test that directories are created when settings are initialized."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        test_settings = InvoicerSettings(
            invoices_dir=temp_path / "invoices",
            clients_dir=temp_path / "clients",
            templates_dir=temp_path / "templates",
        )

        assert test_settings.invoices_dir.exists()
        assert test_settings.clients_dir.exists()
        assert test_settings.templates_dir.exists()


def test_singleton_settings():
    """Test that the module-level settings instance works."""
    assert settings.company_name is not None
    assert settings.hourly_rate > 0
    assert settings.hours_per_day > 0
    assert isinstance(settings.invoices_dir, Path)


def test_backward_compatibility():
    """Test that backward compatibility variables are available."""
    from invoicer.config import (
        COMPANY_NAME,
        COMPANY_EMAIL,
        HOURLY_RATE,
        HOURS_PER_DAY,
        CURRENCY_SYMBOL,
        INVOICES_DIR,
    )

    assert COMPANY_NAME is not None
    assert COMPANY_EMAIL is not None
    assert HOURLY_RATE > 0
    assert HOURS_PER_DAY > 0
    assert CURRENCY_SYMBOL is not None
    assert isinstance(INVOICES_DIR, Path)
