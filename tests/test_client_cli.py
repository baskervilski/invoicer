"""
Unit tests for client CLI delete functionality.
"""

from unittest.mock import Mock, patch, call
from io import StringIO

from invoicer.cli.client import delete


def test_delete_single_client(temp_dir, sample_client):
    """Test deleting a single client."""
    # Create mock client manager
    mock_client_manager = Mock()

    # Configure mocks
    mock_client_manager.get_client.return_value = sample_client
    mock_client_manager.delete_client.return_value = True

    # Capture stdout
    captured_output = StringIO()

    with (
        patch("invoicer.cli.client.ClientManager", return_value=mock_client_manager),
        patch("builtins.input", return_value="yes"),
        patch("sys.stdout", captured_output),
    ):
        delete(sample_client.id)

    # Verify calls
    mock_client_manager.get_client.assert_called_once_with(sample_client.id)
    mock_client_manager.delete_client.assert_called_once_with(sample_client.id)

    # Check output
    output = captured_output.getvalue()
    assert sample_client.name in output
    assert "deleted successfully" in output


def test_delete_multiple_clients(temp_dir, sample_client_1, sample_client_2):
    """Test deleting multiple clients."""
    # Create mock client manager
    mock_client_manager = Mock()

    # Configure mocks
    mock_client_manager.get_client.side_effect = lambda id: {
        sample_client_1.id: sample_client_1,
        sample_client_2.id: sample_client_2,
    }.get(id)
    mock_client_manager.delete_client.return_value = True

    # Capture stdout
    captured_output = StringIO()

    with (
        patch("invoicer.cli.client.ClientManager", return_value=mock_client_manager),
        patch("builtins.input", return_value="yes"),
        patch("sys.stdout", captured_output),
    ):
        delete(f"{sample_client_1.id},{sample_client_2.id}")

    # Verify calls
    expected_get_calls = [call(sample_client_1.id), call(sample_client_2.id)]
    expected_delete_calls = [call(sample_client_1.id), call(sample_client_2.id)]

    mock_client_manager.get_client.assert_has_calls(expected_get_calls, any_order=True)
    mock_client_manager.delete_client.assert_has_calls(expected_delete_calls, any_order=True)

    # Check output
    output = captured_output.getvalue()
    assert "2 clients" in output
    assert sample_client_1.name in output
    assert sample_client_2.name in output
    assert "2 client(s) deleted successfully" in output


def test_delete_with_spaces_in_list(sample_client_1, sample_client_2):
    """Test deleting clients with spaces in the comma-separated list."""
    mock_client_manager = Mock()

    mock_client_manager.get_client.side_effect = lambda id: {
        sample_client_1.id: sample_client_1,
        sample_client_2.id: sample_client_2,
    }.get(id)
    mock_client_manager.delete_client.return_value = True

    captured_output = StringIO()

    with (
        patch("invoicer.cli.client.ClientManager", return_value=mock_client_manager),
        patch("builtins.input", return_value="yes"),
        patch("sys.stdout", captured_output),
    ):
        # Test with spaces around commas
        delete(f"{sample_client_1.id} , {sample_client_2.id} ")

    # Should still work properly
    expected_get_calls = [call(sample_client_1.id), call(sample_client_2.id)]
    mock_client_manager.get_client.assert_has_calls(expected_get_calls, any_order=True)


def test_delete_nonexistent_client():
    """Test attempting to delete a nonexistent client."""
    mock_client_manager = Mock()
    mock_client_manager.get_client.return_value = None

    captured_output = StringIO()

    with (
        patch("invoicer.cli.client.ClientManager", return_value=mock_client_manager),
        patch("sys.stdout", captured_output),
    ):
        delete("nonexistent")

    # Verify client lookup was attempted
    mock_client_manager.get_client.assert_called_once_with("nonexistent")

    # Should not attempt deletion
    mock_client_manager.delete_client.assert_not_called()

    # Check error message
    output = captured_output.getvalue()
    assert "not found" in output
    assert "nonexistent" in output


def test_delete_mixed_existing_nonexistent(existing_client):
    """Test deleting a mix of existing and nonexistent clients."""
    mock_client_manager = Mock()

    mock_client_manager.get_client.side_effect = lambda id: {
        existing_client.id: existing_client,
        "nonexistent": None,
    }.get(id)
    mock_client_manager.delete_client.return_value = True

    captured_output = StringIO()

    with (
        patch("invoicer.cli.client.ClientManager", return_value=mock_client_manager),
        patch("builtins.input", return_value="yes"),
        patch("sys.stdout", captured_output),
    ):
        delete(f"{existing_client.id},nonexistent")

    # Should attempt to get both clients
    expected_get_calls = [call(existing_client.id), call("nonexistent")]
    mock_client_manager.get_client.assert_has_calls(expected_get_calls, any_order=True)

    # Should only delete the existing one
    mock_client_manager.delete_client.assert_called_once_with(existing_client.id)

    # Check output mentions both scenarios
    output = captured_output.getvalue()
    assert "not found" in output
    assert "nonexistent" in output
    assert existing_client.name in output
    assert "deleted successfully" in output


def test_delete_user_cancels(sample_client):
    """Test user cancelling the deletion."""
    mock_client_manager = Mock()

    mock_client_manager.get_client.return_value = sample_client

    captured_output = StringIO()

    with (
        patch("invoicer.cli.client.ClientManager", return_value=mock_client_manager),
        patch("builtins.input", return_value="no"),
        patch("sys.stdout", captured_output),
    ):
        delete(sample_client.id)

    # Should not attempt deletion
    mock_client_manager.delete_client.assert_not_called()

    # Check cancellation message
    output = captured_output.getvalue()
    assert "cancelled" in output


def test_delete_failure(sample_client):
    """Test deletion failure from client manager."""
    mock_client_manager = Mock()

    mock_client_manager.get_client.return_value = sample_client
    mock_client_manager.delete_client.return_value = False  # Deletion fails

    captured_output = StringIO()

    with (
        patch("invoicer.cli.client.ClientManager", return_value=mock_client_manager),
        patch("builtins.input", return_value="yes"),
        patch("sys.stdout", captured_output),
    ):
        delete(sample_client.id)

    # Should attempt deletion
    mock_client_manager.delete_client.assert_called_once_with(sample_client.id)

    # Check failure message
    output = captured_output.getvalue()
    assert "Failed to delete" in output


def test_delete_empty_input():
    """Test delete command with empty input."""
    captured_output = StringIO()

    with patch("sys.stdout", captured_output):
        delete("")

    output = captured_output.getvalue()
    assert "No client IDs provided" in output


def test_delete_whitespace_only():
    """Test delete command with only whitespace."""
    captured_output = StringIO()

    with patch("sys.stdout", captured_output):
        delete("  ,  ,  ")

    output = captured_output.getvalue()
    assert "No client IDs provided" in output
