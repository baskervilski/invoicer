"""
Client Data Management

This module handles storing and retrieving client information for invoice generation.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


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
            self.clients_dir = Path(clients_dir)

        # Create clients directory if it doesn't exist
        self.clients_dir.mkdir(exist_ok=True)

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

    def _load_index(self) -> Dict:
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
        required_fields = ["name", "email"]
        for field in required_fields:
            if field not in client_data:
                raise ValueError(f"Missing required field: {field}")

        # Generate client ID
        client_id = self._generate_client_id(client_data["name"])

        # Prepare client data with metadata
        full_client_data = {
            "id": client_id,
            "name": client_data["name"],
            "email": client_data["email"],
            "address": client_data.get("address", ""),
            "phone": client_data.get("phone", ""),
            "company": client_data.get("company", client_data["name"]),
            "client_code": client_data.get(
                "client_code", client_data["name"][:3].upper()
            ),
            "notes": client_data.get("notes", ""),
            "created_date": datetime.now().isoformat(),
            "last_invoice_date": None,
            "total_invoices": 0,
            "total_amount": 0.0,
        }

        # Save individual client file
        client_file = self.clients_dir / f"{client_id}.json"
        client_file.write_text(json.dumps(full_client_data, indent=2))

        # Update index
        index = self._load_index()
        index["clients"][client_id] = {
            "name": client_data["name"],
            "email": client_data["email"],
            "company": full_client_data["company"],
            "client_code": full_client_data["client_code"],
            "created_date": full_client_data["created_date"],
            "last_invoice_date": None,
            "total_invoices": 0,
        }
        self._save_index(index)

        return client_id

    def get_client(self, client_id: str) -> Optional[Dict]:
        """Get client data by ID

        Args:
            client_id: The client ID

        Returns:
            Dict or None: Client data if found, None otherwise
        """
        client_file = self.clients_dir / f"{client_id}.json"
        if not client_file.exists():
            return None

        try:
            return json.loads(client_file.read_text())
        except json.JSONDecodeError:
            return None

    def list_clients(self) -> List[Dict]:
        """List all clients

        Returns:
            List of client summary dictionaries
        """
        index = self._load_index()
        clients = []

        for client_id, client_summary in index["clients"].items():
            clients.append({"id": client_id, **client_summary})

        # Sort by name
        return sorted(clients, key=lambda x: x["name"].lower())

    def update_client(self, client_id: str, updates: Dict) -> bool:
        """Update client information

        Args:
            client_id: The client ID
            updates: Dictionary of fields to update

        Returns:
            bool: True if successful, False if client not found
        """
        client_data = self.get_client(client_id)
        if not client_data:
            return False

        # Update client data
        for key, value in updates.items():
            if key not in ["id", "created_date"]:  # Protect immutable fields
                client_data[key] = value

        # Save updated client file
        client_file = self.clients_dir / f"{client_id}.json"
        client_file.write_text(json.dumps(client_data, indent=2))

        # Update index if necessary
        if any(key in ["name", "email", "company"] for key in updates.keys()):
            index = self._load_index()
            if client_id in index["clients"]:
                if "name" in updates:
                    index["clients"][client_id]["name"] = updates["name"]
                if "email" in updates:
                    index["clients"][client_id]["email"] = updates["email"]
                if "company" in updates:
                    index["clients"][client_id]["company"] = updates["company"]
                self._save_index(index)

        return True

    def record_invoice(self, client_id: str, invoice_data: Dict):
        """Record that an invoice was created for a client

        Args:
            client_id: The client ID
            invoice_data: Invoice data containing amount and date info
        """
        client_data = self.get_client(client_id)
        if not client_data:
            return

        # Update client statistics
        client_data["total_invoices"] += 1
        client_data["last_invoice_date"] = datetime.now().isoformat()

        # Calculate invoice amount
        days_worked = invoice_data.get("days_worked", 0)
        from . import config

        amount = days_worked * config.HOURS_PER_DAY * config.HOURLY_RATE
        client_data["total_amount"] += amount

        # Save updated client data
        client_file = self.clients_dir / f"{client_id}.json"
        client_file.write_text(json.dumps(client_data, indent=2))

        # Update index
        index = self._load_index()
        if client_id in index["clients"]:
            index["clients"][client_id]["last_invoice_date"] = client_data[
                "last_invoice_date"
            ]
            index["clients"][client_id]["total_invoices"] = client_data[
                "total_invoices"
            ]
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

    def search_clients(self, query: str) -> List[Dict]:
        """Search clients by name, email, or company

        Args:
            query: Search query

        Returns:
            List of matching client dictionaries
        """
        query_lower = query.lower()
        all_clients = self.list_clients()

        matching_clients = []
        for client in all_clients:
            if (
                query_lower in client["name"].lower()
                or query_lower in client["email"].lower()
                or query_lower in client.get("company", "").lower()
            ):
                matching_clients.append(client)

        return matching_clients


def create_sample_clients(client_manager: ClientManager):
    """Create some sample clients for demonstration"""
    sample_clients = [
        {
            "name": "Acme Corporation",
            "email": "billing@acme-corp.com",
            "address": "123 Business Ave\nNew York, NY 10001",
            "phone": "+1 (555) 123-4567",
            "company": "Acme Corporation",
            "client_code": "ACM",
            "notes": "Long-term client, payment terms NET 30",
        },
        {
            "name": "TechStart Solutions",
            "email": "finance@techstart.io",
            "address": "456 Innovation Drive\nSan Francisco, CA 94107",
            "phone": "+1 (555) 987-6543",
            "company": "TechStart Solutions Inc",
            "client_code": "TSS",
            "notes": "Startup client, prefers electronic invoices",
        },
        {
            "name": "Global Dynamics Inc",
            "email": "accounts@globaldynamics.com",
            "address": "789 Corporate Blvd\nChicago, IL 60601",
            "phone": "+1 (555) 246-8135",
            "company": "Global Dynamics Inc",
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
