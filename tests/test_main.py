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
