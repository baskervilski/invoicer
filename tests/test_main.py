"""
Unit tests for main.py functions - testing main functionality.
"""

from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime

from invoicer.main import send_invoice_email, get_last_day_of_month


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


def test_get_last_day_of_month():
    """Test getting the last day of various months."""
    # Test regular month
    result = get_last_day_of_month("November 2025")
    assert result.year == 2025
    assert result.month == 11
    assert result.day == 30
    assert result.hour == 23
    assert result.minute == 59
    assert result.second == 59

    # Test February in leap year
    result = get_last_day_of_month("February 2024")
    assert result.year == 2024
    assert result.month == 2
    assert result.day == 29

    # Test February in non-leap year
    result = get_last_day_of_month("February 2025")
    assert result.year == 2025
    assert result.month == 2
    assert result.day == 28

    # Test December
    result = get_last_day_of_month("December 2025")
    assert result.year == 2025
    assert result.month == 12
    assert result.day == 31


def test_get_last_day_of_month_abbreviated():
    """Test getting the last day with abbreviated month names."""
    result = get_last_day_of_month("Nov 2025")
    assert result.year == 2025
    assert result.month == 11
    assert result.day == 30


def test_get_last_day_of_month_invalid_input():
    """Test handling of invalid input defaults to current month."""
    result = get_last_day_of_month("Invalid Month 2025")
    current_date = datetime.now()

    # Should default to current month and year
    assert result.year == current_date.year
    assert result.month == current_date.month
