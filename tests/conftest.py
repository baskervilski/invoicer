"""
Pytest configuration and fixtures for invoicer tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from invoicer.config import InvoicerSettings
from invoicer.invoice_generator import InvoiceGenerator
from invoicer.models import (
    ClientModel,
    InvoiceModel,
    InvoiceItemModel,
    InvoiceClientInfoModel,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_settings(tmp_path) -> InvoicerSettings:
    """Mock settings for testing."""
    return InvoicerSettings(
        microsoft_client_id="test_client_id",
        microsoft_client_secret="test_client_secret",
        microsoft_tenant_id="test_tenant_id",
        invoices_dir=tmp_path / "test_invoices",
        company_name="Test Company",
        company_email="test@company.com",
        company_phone="+1-555-0123",
        hourly_rate=75.0,
        hours_per_day=8.0,
        currency_symbol="$",
    )


@pytest.fixture
def test_generator(mock_settings: InvoicerSettings) -> InvoiceGenerator:
    """Test InvoiceGenerator."""
    return InvoiceGenerator(settings=mock_settings)


@pytest.fixture
def sample_client():
    """Sample client for testing."""
    return ClientModel(
        id="test_client",
        name="Test Client Corp",
        email="client@test.com",
        client_code="TST",
    )


@pytest.fixture
def sample_invoice():
    """Sample invoice for testing."""
    client_info = InvoiceClientInfoModel(
        name="Test Client", email="client@test.com", client_code="TST"
    )

    line_item = InvoiceItemModel(
        description="Consulting services", quantity=10.0, rate=800.0, amount=8000.0
    )

    return InvoiceModel(
        invoice_number="INV-001",
        client_info=client_info,
        line_items=[line_item],
        subtotal=8000.0,
        total_amount=8000.0,
    )
