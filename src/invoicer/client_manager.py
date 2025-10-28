"""
Client Data Management

This module handles storing and retrieving client information for invoice generation.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import ValidationError

from .models import ClientModel, ClientSummaryModel


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

        # Create index file if it doesn't exist
        self.index_file = self.clients_dir / "clients_index.json"
        if not self.index_file.exists():
            self._create_initial_index()

    def _create_initial_index(self):
        """Create initial client index file"""
        initial_data = {
            "clients": {},
            "last_updated": datetime.now().isoformat(),
            "version": "1.0",
        }
        self.index_file.write_text(json.dumps(initial_data, indent=2))

    def _load_index(self) -> dict[str, dict]:
        """Load the client index"""
        try:
            return json.loads(self.index_file.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            self._create_initial_index()
            return json.loads(self.index_file.read_text())

    def _save_index(self, index_data: Dict):
        """Save the client index"""
        index_data["last_updated"] = datetime.now().isoformat()
        self.index_file.write_text(json.dumps(index_data, indent=2))

    def _generate_client_id(self, client_name: str) -> str:
        """Generate a unique client ID from the client name"""
        # Remove special characters and spaces, convert to lowercase
        import re

        client_id = re.sub(r"[^a-zA-Z0-9]", "_", client_name.lower())
        client_id = re.sub(r"_+", "_", client_id).strip("_")

        # Check if ID already exists, add number if needed
        index = self._load_index()
        original_id = client_id
        counter = 1

        while client_id in index["clients"]:
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
            notes=client_data.get("notes", ""),
        )

        # Save individual client file
        client_file = self.clients_dir / f"{client_id}.json"
        client_file.write_text(client_model.model_dump_json(indent=2))

        # Update index using model data
        index = self._load_index()
        index["clients"][client_id] = {
            "name": client_model.name,
            "email": client_model.email,
            "client_code": client_model.client_code,
            "created_date": client_model.created_date.isoformat(),
            "last_invoice_date": None,
            "total_invoices": 0,
        }
        self._save_index(index)

        return client_id

    def get_client(self, client_id: str) -> Optional[ClientModel]:
        """Get client data by ID

        Args:
            client_id: The client ID

        Returns:
            ClientModel or None: Client model if found, None otherwise
        """
        client_file = self.clients_dir / f"{client_id}.json"

        if not client_file.exists():
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
        index = self._load_index()
        clients = []

        for client_id, client_summary in index["clients"].items():
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
        client_file = self.clients_dir / f"{client_id}.json"
        client_file.write_text(
            json.dumps(updated_model.model_dump(mode="json"), indent=2)
        )

        # Update index if necessary
        if any(key in ["name", "email", "client_code"] for key in updates.keys()):
            index = self._load_index()
            if client_id in index["clients"]:
                if "name" in updates:
                    index["clients"][client_id]["name"] = updated_model.name
                if "email" in updates:
                    index["clients"][client_id]["email"] = updated_model.email
                if "client_code" in updates:
                    index["clients"][client_id]["client_code"] = (
                        updated_model.client_code
                    )
                self._save_index(index)

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
        client_file = self.clients_dir / f"{client_id}.json"
        client_file.write_text(
            json.dumps(updated_model.model_dump(mode="json"), indent=2)
        )

        # Update index
        index = self._load_index()
        if client_id in index["clients"]:
            index["clients"][client_id]["last_invoice_date"] = (
                updated_model.last_invoice_date.isoformat()
                if updated_model.last_invoice_date
                else None
            )
            index["clients"][client_id]["total_invoices"] = updated_model.total_invoices
            self._save_index(index)

    def delete_client(self, client_id: str) -> bool:
        """Delete a client

        Args:
            client_id: The client ID

        Returns:
            bool: True if successful, False if client not found
        """
        client_file = self.clients_dir / f"{client_id}.json"
        if not client_file.exists():
            return False

        # Remove client file
        client_file.unlink()

        # Remove from index
        index = self._load_index()
        if client_id in index["clients"]:
            del index["clients"][client_id]
            self._save_index(index)

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


def create_sample_clients(client_manager: ClientManager):
    """Create some sample clients for demonstration"""
    sample_clients = [
        {
            "name": "Acme Corporation",
            "email": "billing@acme-corp.com",
            "address": "123 Business Ave\nNew York, NY 10001",
            "phone": "+1 (555) 123-4567",
            "client_code": "ACM",
            "notes": "Long-term client, payment terms NET 30",
        },
        {
            "name": "TechStart Solutions",
            "email": "finance@techstart.io",
            "address": "456 Innovation Drive\nSan Francisco, CA 94107",
            "phone": "+1 (555) 987-6543",
            "client_code": "TSS",
            "notes": "Startup client, prefers electronic invoices",
        },
        {
            "name": "Global Dynamics Inc",
            "email": "accounts@globaldynamics.com",
            "address": "789 Corporate Blvd\nChicago, IL 60601",
            "phone": "+1 (555) 246-8135",
            "client_code": "GDI",
            "notes": "Enterprise client, requires detailed project descriptions",
        },
    ]

    for client_data in sample_clients:
        try:
            client_manager.add_client(client_data)
        except ValueError:
            # Client might already exist
            pass
