"""
Unit tests for client CLI delete functionality.
"""

from unittest.mock import Mock, patch, call
from io import StringIO

from invoicer.cli.client import delete
from invoicer.models import ClientModel


def test_delete_single_client(temp_dir):
    """Test deleting a single client."""
    # Create mock client manager
    mock_client_manager = Mock()

    # Create sample client
    sample_client = ClientModel(
        id="test_client",
        name="Test Client",
        email="test@example.com",
        client_code="TST",
    )

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
        delete("test_client")

    # Verify calls
    mock_client_manager.get_client.assert_called_once_with("test_client")
    mock_client_manager.delete_client.assert_called_once_with("test_client")

    # Check output
    output = captured_output.getvalue()
    assert "Test Client" in output
    assert "deleted successfully" in output


def test_delete_multiple_clients(temp_dir):
    """Test deleting multiple clients."""
    # Create mock client manager
    mock_client_manager = Mock()

    # Create sample clients
    client1 = ClientModel(
        id="client1", name="Client One", email="one@example.com", client_code="ONE"
    )
    client2 = ClientModel(
        id="client2", name="Client Two", email="two@example.com", client_code="TWO"
    )

    # Configure mocks
    mock_client_manager.get_client.side_effect = lambda id: {
        "client1": client1,
        "client2": client2,
    }.get(id)
    mock_client_manager.delete_client.return_value = True

    # Capture stdout
    captured_output = StringIO()

    with (
        patch("invoicer.cli.client.ClientManager", return_value=mock_client_manager),
        patch("builtins.input", return_value="yes"),
        patch("sys.stdout", captured_output),
    ):
        delete("client1,client2")

    # Verify calls
    expected_get_calls = [call("client1"), call("client2")]
    expected_delete_calls = [call("client1"), call("client2")]

    mock_client_manager.get_client.assert_has_calls(expected_get_calls, any_order=True)
    mock_client_manager.delete_client.assert_has_calls(
        expected_delete_calls, any_order=True
    )

    # Check output
    output = captured_output.getvalue()
    assert "2 clients" in output
    assert "Client One" in output
    assert "Client Two" in output
    assert "2 client(s) deleted successfully" in output


def test_delete_with_spaces_in_list():
    """Test deleting clients with spaces in the comma-separated list."""
    mock_client_manager = Mock()

    client1 = ClientModel(
        id="client1", name="Client One", email="one@example.com", client_code="ONE"
    )
    client2 = ClientModel(
        id="client2", name="Client Two", email="two@example.com", client_code="TWO"
    )

    mock_client_manager.get_client.side_effect = lambda id: {
        "client1": client1,
        "client2": client2,
    }.get(id)
    mock_client_manager.delete_client.return_value = True

    captured_output = StringIO()

    with (
        patch("invoicer.cli.client.ClientManager", return_value=mock_client_manager),
        patch("builtins.input", return_value="yes"),
        patch("sys.stdout", captured_output),
    ):
        # Test with spaces around commas
        delete("client1 , client2 ")

    # Should still work properly
    expected_get_calls = [call("client1"), call("client2")]
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


def test_delete_mixed_existing_nonexistent():
    """Test deleting a mix of existing and nonexistent clients."""
    mock_client_manager = Mock()

    existing_client = ClientModel(
        id="existing",
        name="Existing Client",
        email="existing@example.com",
        client_code="EXT",
    )

    mock_client_manager.get_client.side_effect = lambda id: {
        "existing": existing_client,
        "nonexistent": None,
    }.get(id)
    mock_client_manager.delete_client.return_value = True

    captured_output = StringIO()

    with (
        patch("invoicer.cli.client.ClientManager", return_value=mock_client_manager),
        patch("builtins.input", return_value="yes"),
        patch("sys.stdout", captured_output),
    ):
        delete("existing,nonexistent")

    # Should attempt to get both clients
    expected_get_calls = [call("existing"), call("nonexistent")]
    mock_client_manager.get_client.assert_has_calls(expected_get_calls, any_order=True)

    # Should only delete the existing one
    mock_client_manager.delete_client.assert_called_once_with("existing")

    # Check output mentions both scenarios
    output = captured_output.getvalue()
    assert "not found" in output
    assert "nonexistent" in output
    assert "Existing Client" in output
    assert "deleted successfully" in output


def test_delete_user_cancels():
    """Test user cancelling the deletion."""
    mock_client_manager = Mock()

    sample_client = ClientModel(
        id="test_client",
        name="Test Client",
        email="test@example.com",
        client_code="TST",
    )

    mock_client_manager.get_client.return_value = sample_client

    captured_output = StringIO()

    with (
        patch("invoicer.cli.client.ClientManager", return_value=mock_client_manager),
        patch("builtins.input", return_value="no"),
        patch("sys.stdout", captured_output),
    ):
        delete("test_client")

    # Should not attempt deletion
    mock_client_manager.delete_client.assert_not_called()

    # Check cancellation message
    output = captured_output.getvalue()
    assert "cancelled" in output


def test_delete_failure():
    """Test deletion failure from client manager."""
    mock_client_manager = Mock()

    sample_client = ClientModel(
        id="test_client",
        name="Test Client",
        email="test@example.com",
        client_code="TST",
    )

    mock_client_manager.get_client.return_value = sample_client
    mock_client_manager.delete_client.return_value = False  # Deletion fails

    captured_output = StringIO()

    with (
        patch("invoicer.cli.client.ClientManager", return_value=mock_client_manager),
        patch("builtins.input", return_value="yes"),
        patch("sys.stdout", captured_output),
    ):
        delete("test_client")

    # Should attempt deletion
    mock_client_manager.delete_client.assert_called_once_with("test_client")

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
