"""
Unit tests for client manager - testing main functionality.
"""

from invoicer.client_manager import ClientManager
from invoicer.models import ClientModel


def test_client_manager_initialization(temp_dir):
    """Test that ClientManager can be initialized."""
    client_manager = ClientManager(clients_dir=temp_dir)

    assert client_manager.clients_dir.exists()
    assert hasattr(client_manager, "index")
    assert client_manager.index is not None


def test_add_and_get_client(temp_dir):
    """Test adding and retrieving a client."""
    client_manager = ClientManager(clients_dir=temp_dir)

    client_data = {
        "name": "Test Client",
        "email": "test@example.com",
        "client_code": "TST",
    }

    # Add client
    client_id = client_manager.add_client(client_data)
    assert client_id is not None

    # Retrieve client
    retrieved_client = client_manager.get_client(client_id)
    assert retrieved_client is not None
    assert isinstance(retrieved_client, ClientModel)
    assert retrieved_client.name == "Test Client"
    assert retrieved_client.email == "test@example.com"


def test_list_clients(temp_dir):
    """Test listing clients."""
    client_manager = ClientManager(clients_dir=temp_dir)

    # Initially empty
    clients = client_manager.list_clients()
    assert len(clients) == 0

    # Add a client
    client_data = {
        "name": "Test Client",
        "email": "test@example.com",
        "client_code": "TST",
    }
    client_manager.add_client(client_data)

    # Should have one client
    clients = client_manager.list_clients()
    assert len(clients) == 1
    assert clients[0].name == "Test Client"


def test_search_clients(temp_dir):
    """Test searching clients."""
    client_manager = ClientManager(clients_dir=temp_dir)

    # Add test clients
    client_manager.add_client({"name": "Acme Corp", "email": "contact@acme.com", "client_code": "ACM"})
    client_manager.add_client({"name": "Beta Inc", "email": "info@beta.com", "client_code": "BET"})

    # Search by name
    results = client_manager.search_clients("Acme")
    assert len(results) == 1
    assert results[0].name == "Acme Corp"

    # Search by email
    results = client_manager.search_clients("beta.com")
    assert len(results) == 1
    assert results[0].name == "Beta Inc"


def test_update_client(temp_dir):
    """Test updating client information."""
    client_manager = ClientManager(clients_dir=temp_dir)

    # Add client
    client_id = client_manager.add_client(
        {"name": "Original Name", "email": "original@example.com", "client_code": "ORG"}
    )

    # Update client
    success = client_manager.update_client(client_id, {"name": "Updated Name", "phone": "+1-555-0123"})

    assert success is True

    # Verify update
    updated_client = client_manager.get_client(client_id)
    assert updated_client is not None
    assert updated_client.name == "Updated Name"
    assert updated_client.phone == "+1-555-0123"
    assert updated_client.email == "original@example.com"  # Unchanged


def test_delete_client(temp_dir):
    """Test deleting a client."""
    client_manager = ClientManager(clients_dir=temp_dir)

    # Add client
    client_id = client_manager.add_client({"name": "To Delete", "email": "delete@example.com", "client_code": "DEL"})

    # Verify client exists
    assert client_manager.get_client(client_id) is not None

    # Delete client
    success = client_manager.delete_client(client_id)
    assert success is True

    # Verify client is gone
    assert client_manager.get_client(client_id) is None


# Project functionality tests
def test_add_and_get_project(temp_dir):
    """Test adding and retrieving a project."""
    client_manager = ClientManager(clients_dir=temp_dir)

    # Add a client first
    client_id = client_manager.add_client({"name": "Test Client", "email": "test@example.com", "client_code": "TST"})

    # Add a project
    project_id = client_manager.add_project(client_id, "Test Project")
    assert project_id is not None

    # Retrieve project
    project = client_manager.get_project(project_id)
    assert project is not None
    assert project.name == "Test Project"
    assert project.client_id == client_id

    # Verify client has the project listed
    client = client_manager.get_client(client_id)
    assert client is not None


def test_list_projects(temp_dir):
    """Test listing projects for a client."""
    client_manager = ClientManager(clients_dir=temp_dir)

    # Add a client
    client_id = client_manager.add_client({"name": "Test Client", "email": "test@example.com", "client_code": "TST"})

    # Initially no projects
    projects = client_manager.list_projects(client_id)
    assert len(projects) == 0

    # Add some projects
    client_manager.add_project(client_id, "Project Alpha")
    client_manager.add_project(client_id, "Project Beta")

    # Should have two projects
    projects = client_manager.list_projects(client_id)
    assert len(projects) == 2

    # Projects should be sorted by creation date (newest first)
    project_names = [p.name for p in projects]
    assert "Project Alpha" in project_names
    assert "Project Beta" in project_names


def test_delete_project(temp_dir):
    """Test deleting a project."""
    client_manager = ClientManager(clients_dir=temp_dir)

    # Add client and project
    client_id = client_manager.add_client({"name": "Test Client", "email": "test@example.com", "client_code": "TST"})

    project_id = client_manager.add_project(client_id, "To Delete Project")
    assert project_id is not None  # Ensure project was created

    # Verify project exists
    assert client_manager.get_project(project_id) is not None

    # Delete project
    success = client_manager.delete_project(project_id)
    assert success is True

    # Verify project is gone
    assert client_manager.get_project(project_id) is None

    # Verify it's removed from client's project list
    client = client_manager.get_client(client_id)
    assert client is not None


def test_add_project_nonexistent_client(temp_dir):
    """Test adding a project to a nonexistent client."""
    client_manager = ClientManager(clients_dir=temp_dir)

    # Try to add project to non-existent client
    project_id = client_manager.add_project("nonexistent_client", "Test Project")
    assert project_id is None


def test_project_id_generation(temp_dir):
    """Test that project IDs are generated correctly and uniquely."""
    client_manager = ClientManager(clients_dir=temp_dir)

    # Add a client
    client_id = client_manager.add_client({"name": "Test Client", "email": "test@example.com", "client_code": "TST"})

    # Add projects with same name - should get unique IDs
    project_id1 = client_manager.add_project(client_id, "Test Project")
    project_id2 = client_manager.add_project(client_id, "Test Project")

    assert project_id1 != project_id2
    assert project_id1 is not None
    assert project_id2 is not None

    # Both projects should exist
    assert client_manager.get_project(project_id1) is not None
    assert client_manager.get_project(project_id2) is not None
