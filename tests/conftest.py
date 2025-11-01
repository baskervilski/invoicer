"""
Pytest configuration and fixtures for invoicer tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
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
        vat_number="TST123456789",
        created_date=datetime(2023, 1, 1),
        address="123 Test St\nTest City, TS 12345",
        phone="+1-555-0123",
    )


@pytest.fixture
def sample_client_1():
    """First sample client for multi-client testing."""
    return ClientModel(
        id="client1",
        name="Client One",
        email="one@example.com",
        client_code="ONE",
        vat_number="ONE123456789",
        created_date=datetime(2023, 1, 1),
        address="456 One Ave\nOne City, OC 54321",
        phone="+1-555-0456",
    )


@pytest.fixture
def sample_client_2():
    """Second sample client for multi-client testing."""
    return ClientModel(
        id="client2",
        name="Client Two",
        email="two@example.com",
        client_code="TWO",
        vat_number="TWO123456789",
        created_date=datetime(2023, 1, 1),
        address="789 Two Blvd\nTwo City, TC 98765",
        phone="+1-555-0789",
    )


@pytest.fixture
def existing_client():
    """Existing client for mixed scenario testing."""
    return ClientModel(
        id="existing",
        name="Existing Client",
        email="existing@example.com",
        client_code="EXT",
        vat_number="EXT123456789",
        created_date=datetime(2023, 1, 1),
        address="456 Existing St\nExist City, EX 67890",
        phone="+1-555-6789",
    )


@pytest.fixture
def sample_invoice():
    """Sample invoice for testing."""
    client_info = InvoiceClientInfoModel(
        name="Test Client", email="client@test.com", client_code="TST", client_id="test", address="123 Test St\nTest City, TS 12345"
    )

    line_item = InvoiceItemModel(
        description="Consulting services", quantity=10.0, rate=800.0, amount=8000.0
    )

    return InvoiceModel(
        invoice_number="INV-001",
        invoice_date=datetime(2023, 1, 1),
        client_info=client_info,
        line_items=[line_item],
        subtotal=8000.0,
        total_amount=8000.0,
        payment_terms="Net 30 days",
    )
