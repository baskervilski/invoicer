"""
Unit tests for client utilities - testing shared client creation functionality.
"""

from unittest.mock import Mock, patch
from io import StringIO

import pytest

from invoicer.client_utils import create_client_interactive, get_client_creation_data
from invoicer.models import ClientModel


def test_create_client_interactive_success():
    """Test successful interactive client creation."""
    # Create mock client manager
    mock_client_manager = Mock()

    # Create sample client to return
    sample_client = ClientModel(
        id="test_client",
        name="Test Client",
        email="test@example.com",
        client_code="TST",
        address="123 Test St",
    )

    # Configure mocks
    mock_client_manager.add_client.return_value = "test_client"
    mock_client_manager.add_project.return_value = "test_client_test_project"
    mock_client_manager.get_client.return_value = sample_client

    # Mock user inputs
    user_inputs = [
        "Test Client",  # name
        "test@example.com",  # email
        "",  # company (uses default)
        "",  # client_code (uses default)
        "123 Test St",  # address
        "+1-555-0123",  # phone
        "Test notes",  # notes
        "Test Project",  # project_name
    ]

    captured_output = StringIO()

    with (
        patch("builtins.input", side_effect=user_inputs),
        patch("sys.stdout", captured_output),
    ):
        result = create_client_interactive(mock_client_manager)

    # Verify client was created
    assert result is not None
    assert result.name == "Test Client"
    assert result.email == "test@example.com"

    # Verify client manager calls
    mock_client_manager.add_client.assert_called_once()
    mock_client_manager.get_client.assert_called_once_with("test_client")

    # Check output contains success message
    output = captured_output.getvalue()
    assert "Create New Client" in output
    assert "created successfully" in output


def test_create_client_interactive_empty_name():
    """Test client creation with empty name."""
    mock_client_manager = Mock()

    captured_output = StringIO()

    with patch("builtins.input", return_value=""), patch("sys.stdout", captured_output):
        result = create_client_interactive(mock_client_manager)

    # Should return None
    assert result is None

    # Should not attempt to create client
    mock_client_manager.add_client.assert_not_called()

    # Check error message
    output = captured_output.getvalue()
    assert "Client name is required" in output


def test_create_client_interactive_empty_email():
    """Test client creation with empty email."""
    mock_client_manager = Mock()

    user_inputs = ["Test Client", ""]  # name, then empty email

    captured_output = StringIO()

    with (
        patch("builtins.input", side_effect=user_inputs),
        patch("sys.stdout", captured_output),
    ):
        result = create_client_interactive(mock_client_manager)

    # Should return None
    assert result is None

    # Should not attempt to create client
    mock_client_manager.add_client.assert_not_called()

    # Check error message
    output = captured_output.getvalue()
    assert "Email address is required" in output


def test_create_client_interactive_exception():
    """Test client creation with exception during creation."""
    mock_client_manager = Mock()
    mock_client_manager.add_client.side_effect = Exception("Database error")

    user_inputs = [
        "Test Client",
        "test@example.com",
        "",
        "",
        "",
        "",
        "",  # Default values for other fields
        "Test Project",  # project_name
    ]

    captured_output = StringIO()

    with (
        patch("builtins.input", side_effect=user_inputs),
        patch("sys.stdout", captured_output),
    ):
        result = create_client_interactive(mock_client_manager)

    # Should return None due to exception
    assert result is None

    # Check error message
    output = captured_output.getvalue()
    assert "Error creating client" in output
    assert "Database error" in output


def test_get_client_creation_data_success(client_creation_user_inputs):
    """Test successful data collection without creating client."""
    user_inputs = client_creation_user_inputs.values()
    with patch("builtins.input", side_effect=user_inputs):
        result = get_client_creation_data()

    # Verify data was collected correctly
    for key, value in client_creation_user_inputs.items():
        assert result[key] == value

@pytest.fixture
def client_creation_user_inputs() -> dict:
    """Fixture providing default user inputs for client creation tests."""
    return {
        "name": "Test Client",
        "email": "test@example.com",
        "company": "Test Company",
        "client_code": "TST",
        "address": "123 Test St",
        "phone": "+1-555-0123",
        "vat_number": "VAT123",
        "notes": "Test notes",
        "project_name": "Test Project",
    }

def test_get_client_creation_data_with_defaults(client_creation_user_inputs):
    """Test data collection using default values."""
    user_inputs = client_creation_user_inputs.values()

    with patch("builtins.input", side_effect=user_inputs):
        result = get_client_creation_data(raise_errors=True)

    # Verify defaults were applied
    for key, value in client_creation_user_inputs.items():
        assert result[key] == value


def test_get_client_creation_data_empty_name():
    """Test data collection with empty name."""
    with patch("builtins.input", return_value=""):
        result = get_client_creation_data()

    assert result is None


def test_get_client_creation_data_empty_email():
    """Test data collection with empty email."""
    user_inputs = ["Test Client", ""]  # name, then empty email

    with patch("builtins.input", side_effect=user_inputs):
        result = get_client_creation_data()

    assert result is None


def test_create_client_interactive_custom_title():
    """Test that custom title is displayed correctly."""
    mock_client_manager = Mock()
    sample_client = ClientModel(
        id="test_client",
        name="Test Client",
        email="test@example.com",
        client_code="TST",
        address="123 Test St",
    )
    mock_client_manager.add_client.return_value = "test_client"
    mock_client_manager.get_client.return_value = sample_client

    user_inputs = ["Test", "test@test.com", "", "", "", "", ""]

    captured_output = StringIO()

    with (
        patch("builtins.input", side_effect=user_inputs),
        patch("sys.stdout", captured_output),
    ):
        create_client_interactive(mock_client_manager)

    output = captured_output.getvalue()
    assert "Create New Client" in output
