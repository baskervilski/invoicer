"""
Unit tests for main.py functions - testing main functionality.
"""

from unittest.mock import patch, MagicMock
from pathlib import Path

from invoicer.main import send_invoice_email


@patch("invoicer.main.EmailSender")
def test_send_invoice_email_success(mock_email_sender_class, sample_invoice):
    """Test successful email sending."""
    # Mock EmailSender instance
    mock_sender = MagicMock()
    mock_sender.authenticate.return_value = True
    mock_sender.send_email.return_value = True
    mock_sender.create_invoice_email_body.return_value = "Test email body"
    mock_email_sender_class.return_value = mock_sender

    # Test the function
    pdf_path = Path("/tmp/test_invoice.pdf")
    result = send_invoice_email(sample_invoice, pdf_path)

    assert result is True
    mock_sender.authenticate.assert_called_once()
    mock_sender.send_email.assert_called_once()


@patch("invoicer.main.EmailSender")
def test_send_invoice_email_auth_failure(mock_email_sender_class, sample_invoice):
    """Test email sending with authentication failure."""
    # Mock EmailSender instance with auth failure
    mock_sender = MagicMock()
    mock_sender.authenticate.return_value = False
    mock_email_sender_class.return_value = mock_sender

    # Test the function
    pdf_path = Path("/tmp/test_invoice.pdf")
    result = send_invoice_email(sample_invoice, pdf_path)

    assert result is False
    mock_sender.authenticate.assert_called_once()
    mock_sender.send_email.assert_not_called()


@patch("invoicer.main.EmailSender")
def test_send_invoice_email_send_failure(mock_email_sender_class, sample_invoice):
    """Test email sending with send failure."""
    # Mock EmailSender instance with send failure
    mock_sender = MagicMock()
    mock_sender.authenticate.return_value = True
    mock_sender.send_email.return_value = False
    mock_sender.create_invoice_email_body.return_value = "Test email body"
    mock_email_sender_class.return_value = mock_sender

    # Test the function
    pdf_path = Path("/tmp/test_invoice.pdf")
    result = send_invoice_email(sample_invoice, pdf_path)

    assert result is False
    mock_sender.send_email.assert_called_once()


@patch("invoicer.main.ClientManager")
@patch("builtins.input")
def test_create_new_client_basic(mock_input, mock_client_manager_class, temp_dir):
    """Test basic client creation flow."""
    # Mock inputs
    mock_input.side_effect = [
        "Test Client",  # name
        "test@example.com",  # email
        "",  # company (uses default)
        "",  # client_code (uses default)
        "123 Test St",  # address
        "+1-555-0123",  # phone
        "Test notes",  # notes
    ]

    # Mock ClientManager
    mock_manager = MagicMock()
    mock_manager.add_client.return_value = "test_client_id"
    mock_manager.get_client.return_value = MagicMock(
        id="test_client_id", name="Test Client", email="test@example.com"
    )
    mock_client_manager_class.return_value = mock_manager

    from invoicer.main import create_new_client

    result = create_new_client(mock_manager)

    assert result is not None
    mock_manager.add_client.assert_called_once()
    mock_manager.get_client.assert_called_once_with("test_client_id")


@patch("builtins.input")
def test_create_new_client_missing_required_fields(mock_input):
    """Test client creation with missing required fields."""
    # Mock inputs with empty name
    mock_input.side_effect = ["", "test@example.com"]

    mock_manager = MagicMock()

    from invoicer.main import create_new_client

    result = create_new_client(mock_manager)

    assert result is None
    mock_manager.add_client.assert_not_called()
