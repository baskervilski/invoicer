"""
Client Data Management

This module handles storing and retrieving client information for invoice generation.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import ValidationError

from .models import ClientModel, ClientSummaryModel, ProjectModel


class ClientManager:
    """Manages client data storage and retrieval"""

    def __init__(self, clients_dir: Optional[Path] = None):
        """Initialize the client manager

        Args:
            clients_dir: Directory to store client data files. If None, uses default.
        """
        if clients_dir is None:
            from . import config

            self.clients_dir = config.CLIENTS_DIR
        else:
            self.clients_dir = Path(clients_dir) / "clients"

        # Create clients directory if it doesn't exist
        self.clients_dir.mkdir(parents=True, exist_ok=True)

        # Build in-memory index from actual client files on startup
        self.index = self._build_index_from_files()

    def _build_index_from_files(self):
        """Build the client index by scanning actual client directories and files"""
        index_data = {
            "clients": {},
            "last_updated": datetime.now().isoformat(),
            "version": "1.0",
        }
        
        # Scan all client directories
        for client_dir in self.clients_dir.iterdir():
            if not client_dir.is_dir() or client_dir.name.startswith('.'):
                continue
                
            client_id = client_dir.name
            client_file = client_dir / "client.json"
            
            # Skip if no client.json file exists
            if not client_file.exists():
                continue
                
            try:
                # Load client data
                client_data = json.loads(client_file.read_text())
                
                # Handle backwards compatibility - if old data has 'company' but no 'name'
                client_name = client_data.get("name") or client_data.get("company", "Unknown Client")
                
                # Build index entry (projects removed from client.json)
                index_data["clients"][client_id] = {
                    "name": client_name,
                    "email": client_data.get("email", ""),
                    "client_code": client_data.get("client_code", ""),
                    "vat_number": client_data.get("vat_number", ""),
                    "created_date": client_data.get("created_date", datetime.now().isoformat()),
                    "last_invoice_date": client_data.get("last_invoice_date"),
                    "total_invoices": client_data.get("total_invoices", 0),
                }
                
            except (json.JSONDecodeError, KeyError, Exception):
                # Skip invalid client files
                continue
        
        # Return the built index
        return index_data

    def _get_client_dir(self, client_id: str) -> Path:
        """Get the directory path for a client"""
        return self.clients_dir / client_id

    def _get_client_file(self, client_id: str) -> Path:
        """Get the client.json file path for a client"""
        return self._get_client_dir(client_id) / "client.json"

    def _get_project_file(self, client_id: str, project_name: str) -> Path:
        """Get the project file path for a project"""
        return self._get_client_dir(client_id) / f"project_{project_name}.json"

    def _update_index(self):
        """Update the in-memory client index"""
        self.index = self._build_index_from_files()

    def _generate_client_id(self, client_name: str) -> str:
        """Generate a unique client ID from the client name"""
        # Remove special characters and spaces, convert to lowercase
        import re

        client_id = re.sub(r"[^a-zA-Z0-9]", "_", client_name.lower())
        client_id = re.sub(r"_+", "_", client_id).strip("_")

        # Check if ID already exists, add number if needed
        original_id = client_id
        counter = 1

        while client_id in self.index["clients"]:
            client_id = f"{original_id}_{counter}"
            counter += 1

        return client_id

    def add_client(self, client_data: Dict) -> str:
        """Add a new client to the database

        Args:
            client_data: Dictionary containing client information

        Returns:
            str: The generated client ID
        """
        # Generate client ID
        client_id = self._generate_client_id(client_data["name"])

        # Create Pydantic model with validation
        client_model = ClientModel(
            id=client_id,
            name=client_data["name"],
            email=client_data["email"],
            address=client_data.get("address", ""),
            phone=client_data.get("phone", ""),
            client_code=client_data.get("client_code", client_data["name"][:3].upper()),
            vat_number=client_data.get("vat_number", ""),
            notes=client_data.get("notes", ""),
            created_date=datetime.now(),
        )

        # Create client directory and save client file
        client_dir = self._get_client_dir(client_id)
        client_dir.mkdir(exist_ok=True)
        
        client_file = self._get_client_file(client_id)
        client_file.write_text(client_model.model_dump_json(indent=2))

        # Update index using model data
        self._update_index()

        return client_id

    def get_client(self, client_id: str, raise_if_not_found: bool = False) -> Optional[ClientModel]:
        """Get client data by ID

        Args:
            client_id: The client ID

        Returns:
            ClientModel or None: Client model if found, None otherwise
        """
        client_file = self._get_client_file(client_id)

        if not client_file.exists():
            if raise_if_not_found:
                raise ValueError(f"Client with ID '{client_id}' not found.")
            return None

        try:
            data = json.loads(client_file.read_text())

            # Handle backwards compatibility - if old data has 'company' but no 'name', use company as name
            if "company" in data and "name" not in data:
                data["name"] = data["company"]
            elif "company" in data and not data.get("name"):
                data["name"] = data["company"]

            # Remove the old company field if it exists
            if "company" in data:
                del data["company"]

            # Create and return the model
            return ClientModel(**data)
        except json.JSONDecodeError:
            return None
        except ValidationError:
            return None
        except Exception:
            return None

    def list_clients(self) -> List[ClientSummaryModel]:
        """List all clients

        Returns:
            List of client summary models
        """
        clients = []

        for client_id, client_summary in self.index["clients"].items():
            try:
                # Handle backwards compatibility - if old data has 'company' but no 'name', use company as name
                client_name = client_summary.get("name") or client_summary.get(
                    "company", "Unknown Client"
                )

                client_model = ClientSummaryModel(
                    id=client_id,
                    name=client_name,
                    email=client_summary["email"],
                    client_code=client_summary["client_code"],
                    vat_number=client_summary.get("vat_number", ""),
                    created_date=datetime.fromisoformat(client_summary["created_date"]),
                    last_invoice_date=datetime.fromisoformat(
                        client_summary["last_invoice_date"]
                    )
                    if client_summary.get("last_invoice_date")
                    else None,
                    total_invoices=client_summary.get("total_invoices", 0),
                )
                clients.append(client_model)
            except (ValidationError, ValueError, KeyError):
                # Skip invalid entries
                continue

        # Sort by name
        return sorted(clients, key=lambda x: x.name.lower())

    def update_client(self, client_id: str, updates: Dict) -> bool:
        """Update client information

        Args:
            client_id: The client ID
            updates: Dictionary of fields to update

        Returns:
            bool: True if successful, False if client not found
        """
        client_model = self.get_client(client_id)
        if not client_model:
            return False

        # Create updated data dict
        current_data = client_model.model_dump()
        for key, value in updates.items():
            if key not in ["id", "created_date"]:  # Protect immutable fields
                current_data[key] = value

        # Validate the updated data
        try:
            updated_model = ClientModel(**current_data)
        except ValidationError:
            return False

        # Save updated client file
        client_file = self._get_client_file(client_id)
        client_file.write_text(
            json.dumps(updated_model.model_dump(mode="json"), indent=2)
        )

        # Update index if necessary
        if any(key in ["name", "email", "client_code", "vat_number"] for key in updates.keys()):
            self._update_index()

        return True

    def record_invoice(self, client_id: str, invoice_data: Dict):
        """Record that an invoice was created for a client

        Args:
            client_id: The client ID
            invoice_data: Invoice data containing amount and date info
        """
        client_model = self.get_client(client_id)
        if not client_model:
            return

        # Calculate invoice amount
        days_worked = invoice_data.get("days_worked", 0)
        from . import config

        amount = days_worked * config.HOURS_PER_DAY * config.HOURLY_RATE

        # Create updated data
        updated_data = client_model.model_dump()
        updated_data.update(
            {
                "total_invoices": client_model.total_invoices + 1,
                "last_invoice_date": datetime.now(),
                "total_amount": client_model.total_amount + amount,
            }
        )

        # Create updated model with new statistics
        updated_model = ClientModel(**updated_data)

        # Save updated client data
        client_file = self._get_client_file(client_id)
        client_file.write_text(
            json.dumps(updated_model.model_dump(mode="json"), indent=2)
        )

        # Update index
        self._update_index()

    def delete_client(self, client_id: str) -> bool:
        """Delete a client and all associated projects

        Args:
            client_id: The client ID

        Returns:
            bool: True if successful, False if client not found
        """
        client_dir = self._get_client_dir(client_id)
        if not client_dir.exists():
            return False

        # Remove entire client directory and all contents
        import shutil
        shutil.rmtree(client_dir)

        # Remove from index
        self._update_index()

        return True

    def search_clients(self, query: str) -> List[ClientSummaryModel]:
        """Search clients by name or email."""
        all_clients = self.list_clients()
        if not query:
            return all_clients

        query_lower = query.lower()
        return [
            client
            for client in all_clients
            if (
                query_lower in client.name.lower()
                or query_lower in client.email.lower()
            )
        ]

    def _generate_project_id(self, client_id: str, project_name: str) -> str:
        """Generate a unique project ID from client ID and project name"""
        import re

        project_id = re.sub(r"[^a-zA-Z0-9]", "_", project_name.lower())
        project_id = re.sub(r"_+", "_", project_id).strip("_")
        base_id = f"{client_id}_{project_id}"

        # Check if ID already exists, add number if needed
        counter = 1
        final_id = base_id

        # Check existing projects for this client
        client = self.get_client(client_id)
        if client:
            existing_projects = self.list_projects(client_id)
            existing_ids = {proj.id for proj in existing_projects}

            while final_id in existing_ids:
                final_id = f"{base_id}_{counter}"
                counter += 1

        return final_id

    def add_project(self, client_id: str, project_name: str) -> Optional[str]:
        """Add a new project to a client

        Args:
            client_id: The client ID
            project_name: Name of the project

        Returns:
            str: The generated project ID, or None if client not found
        """
        client = self.get_client(client_id)
        if not client:
            return None

        project_id = self._generate_project_id(client_id, project_name)

        # Create project model
        project_model = ProjectModel(
            id=project_id,
            name=project_name.strip(),
            client_id=client_id,
            created_date=datetime.now(),
        )

        # Save project file in client directory
        # Extract just the project name from the project_id (remove client_id prefix)
        project_name = project_id[len(client_id) + 1:]  # +1 for the underscore
        project_file = self._get_project_file(client_id, project_name)
        project_file.write_text(project_model.model_dump_json(indent=2))

        # Projects are no longer tracked in client.json - they exist as individual files
        return project_id

    def get_project(self, project_id: str) -> Optional[ProjectModel]:
        """Get project data by ID

        Args:
            project_id: The project ID (format: client_id_project_name)

        Returns:
            ProjectModel or None: Project model if found, None otherwise
        """
        # Extract client_id and project_name from project_id
        parts = project_id.split('_', 1)
        if len(parts) != 2:
            return None
            
        client_id, project_name = parts
        project_file = self._get_project_file(client_id, project_name)

        if not project_file.exists():
            # Try to find the project by searching through client directories
            return self._find_project_by_id(project_id)

        try:
            data = json.loads(project_file.read_text())
            return ProjectModel(**data)
        except (json.JSONDecodeError, ValidationError, Exception):
            return None

    def _find_project_by_id(self, project_id: str) -> Optional[ProjectModel]:
        """Find a project by ID by searching through all client directories"""
        for client_dir in self.clients_dir.iterdir():
            if client_dir.is_dir() and not client_dir.name.startswith('.'):
                for project_file in client_dir.glob("project_*.json"):
                    try:
                        data = json.loads(project_file.read_text())
                        project = ProjectModel(**data)
                        if project.id == project_id:
                            return project
                    except (json.JSONDecodeError, ValidationError, Exception):
                        continue
        return None

    def list_projects(self, client_id: str) -> List[ProjectModel]:
        """List all projects for a client

        Args:
            client_id: The client ID

        Returns:
            List of project models
        """
        client_dir = self._get_client_dir(client_id)
        if not client_dir.exists():
            return []

        projects = []
        # Find all project files in the client directory
        for project_file in client_dir.glob("project_*.json"):
            try:
                data = json.loads(project_file.read_text())
                project = ProjectModel(**data)
                projects.append(project)
            except (json.JSONDecodeError, ValidationError, Exception):
                continue

        # Sort by creation date (newest first)
        return sorted(projects, key=lambda x: x.created_date, reverse=True)

    def delete_project(self, project_id: str) -> bool:
        """Delete a project

        Args:
            project_id: The project ID

        Returns:
            bool: True if successful, False if project not found
        """
        project = self.get_project(project_id)
        if not project:
            return False

        # Extract client_id and project_name from project_id
        parts = project_id.split('_', 1)
        if len(parts) == 2:
            client_id, project_name = parts
            project_file = self._get_project_file(client_id, project_name)
            if project_file.exists():
                project_file.unlink()
            else:
                # Fallback: find and delete the project file
                client_dir = self._get_client_dir(project.client_id)
                for pf in client_dir.glob("project_*.json"):
                    try:
                        data = json.loads(pf.read_text())
                        if data.get("id") == project_id:
                            pf.unlink()
                            break
                    except:
                        continue

        # Projects are no longer tracked in client.json, just delete the file
        return True


def create_sample_clients(client_manager: ClientManager):
    """Create some sample clients for demonstration"""
    sample_clients = [
        {
            "name": "Acme Corporation",
            "email": "billing@acme-corp.com",
            "address": "123 Business Ave\nNew York, NY 10001",
            "phone": "+1 (555) 123-4567",
            "client_code": "ACM",
            "vat_number": "US123456789",
            "notes": "Long-term client, payment terms NET 30",
        },
        {
            "name": "TechStart Solutions",
            "email": "finance@techstart.io",
            "address": "456 Innovation Drive\nSan Francisco, CA 94107",
            "phone": "+1 (555) 987-6543",
            "client_code": "TSS",
            "vat_number": "US987654321",
            "notes": "Startup client, prefers electronic invoices",
        },
        {
            "name": "Global Dynamics Inc",
            "email": "accounts@globaldynamics.com",
            "address": "789 Corporate Blvd\nChicago, IL 60601",
            "phone": "+1 (555) 246-8135",
            "client_code": "GDI",
            "vat_number": "US456789123",
            "notes": "Enterprise client, requires detailed project descriptions",
        },
    ]

    for client_data in sample_clients:
        try:
            client_manager.add_client(client_data)
        except ValueError:
            # Client might already exist
            pass
