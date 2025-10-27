"""
Microsoft Graph Email Integration

This module handles sending emails through Microsoft Graph API using OAuth2 authentication.
"""

import base64
from pathlib import Path
import msal
import requests
from typing import Dict, Optional
import webbrowser
import http.server
import socketserver
import urllib.parse
import time

from . import config


class EmailSender:
    def __init__(self):
        self.access_token = None
        self.app = msal.ConfidentialClientApplication(
            config.CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{config.TENANT_ID}",
            client_credential=config.CLIENT_SECRET,
        )

    def authenticate(self) -> bool:
        """
        Authenticate with Microsoft Graph API using OAuth2 flow

        Returns:
            bool: True if authentication successful, False otherwise
        """
        # First try to get token silently
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(config.SCOPES, account=accounts[0])
            if result and "access_token" in result:
                self.access_token = result["access_token"]
                return True

        # If silent acquisition fails, do interactive flow
        return self._interactive_authentication()

    def _interactive_authentication(self) -> bool:
        """
        Perform interactive OAuth2 authentication

        Returns:
            bool: True if authentication successful, False otherwise
        """
        # Get authorization URL
        auth_url = self.app.get_authorization_request_url(
            config.SCOPES, redirect_uri=config.REDIRECT_URI
        )

        print(f"Please visit this URL to authorize the application: {auth_url}")
        webbrowser.open(auth_url)

        # Start a simple HTTP server to catch the redirect
        auth_code = self._wait_for_auth_code()

        if not auth_code:
            print("Failed to get authorization code")
            return False

        # Exchange authorization code for access token
        result = self.app.acquire_token_by_authorization_code(
            auth_code, scopes=config.SCOPES, redirect_uri=config.REDIRECT_URI
        )

        if "access_token" in result:
            self.access_token = result["access_token"]
            return True
        else:
            print(
                f"Failed to acquire token: {result.get('error_description', 'Unknown error')}"
            )
            return False

    def _wait_for_auth_code(self) -> Optional[str]:
        """
        Wait for the authorization code from the redirect URI

        Returns:
            Optional[str]: Authorization code if successful, None otherwise
        """
        auth_code = None

        class AuthHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                nonlocal auth_code
                parsed_url = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed_url.query)

                if "code" in query_params:
                    auth_code = query_params["code"][0]
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(
                        b"<html><body><h1>Authentication successful!</h1><p>You can close this window.</p></body></html>"
                    )
                else:
                    self.send_response(400)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(
                        b"<html><body><h1>Authentication failed!</h1></body></html>"
                    )

            def log_message(self, format, *args):
                # Suppress log messages
                pass

        # Start server on port 8080
        try:
            with socketserver.TCPServer(("", 8080), AuthHandler) as httpd:
                print("Waiting for authentication... (Check your web browser)")

                # Wait for the auth code (with timeout)
                timeout = 300  # 5 minutes
                start_time = time.time()

                while auth_code is None and (time.time() - start_time) < timeout:
                    httpd.handle_request()
                    time.sleep(0.1)

                return auth_code
        except Exception as e:
            print(f"Error starting authentication server: {e}")
            return None

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachment_path: Optional[Path] = None,
    ) -> bool:
        """
        Send an email using Microsoft Graph API

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (HTML or plain text)
            attachment_path: Optional path to file attachment

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.access_token:
            print("Not authenticated. Please call authenticate() first.")
            return False

        # Prepare the email message
        message = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body},
                "toRecipients": [{"emailAddress": {"address": to_email}}],
            }
        }

        # Add attachment if provided
        if attachment_path and attachment_path.exists():
            attachment = self._prepare_attachment(attachment_path)
            if attachment:
                message["message"]["attachments"] = [attachment]

        # Send the email
        endpoint = "https://graph.microsoft.com/v1.0/me/sendMail"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(endpoint, headers=headers, json=message)

            if response.status_code == 202:
                print("Email sent successfully!")
                return True
            else:
                print(f"Failed to send email. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def _prepare_attachment(self, file_path: Path) -> Optional[Dict]:
        """
        Prepare file attachment for email

        Args:
            file_path: Path to the file to attach

        Returns:
            Optional[Dict]: Attachment dictionary or None if failed
        """
        try:
            with open(file_path, "rb") as file:
                file_content = file.read()
                encoded_content = base64.b64encode(file_content).decode("utf-8")

            file_path_obj = Path(file_path)
            filename = file_path_obj.name
            file_size = file_path_obj.stat().st_size

            # Determine content type based on file extension
            content_type = "application/octet-stream"
            if filename.lower().endswith(".pdf"):
                content_type = "application/pdf"
            elif filename.lower().endswith(".txt"):
                content_type = "text/plain"
            elif filename.lower().endswith(".html"):
                content_type = "text/html"

            return {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": filename,
                "contentType": content_type,
                "contentBytes": encoded_content,
                "size": file_size,
            }

        except Exception as e:
            print(f"Error preparing attachment: {e}")
            return None

    def create_invoice_email_body(
        self, client_name: str, invoice_number: str, total_amount: str, month_year: str
    ) -> str:
        """
        Create a professional email body for invoice

        Args:
            client_name: Name of the client
            invoice_number: Invoice number
            total_amount: Total amount due
            month_year: Month and year of services

        Returns:
            str: HTML email body
        """
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2E86AB;">Invoice for {month_year} Services</h2>
                
                <p>Dear {client_name},</p>
                
                <p>I hope this email finds you well. Please find attached the invoice for the consulting services provided during <strong>{month_year}</strong>.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #2E86AB; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Invoice Details:</strong></p>
                    <ul style="margin: 10px 0;">
                        <li>Invoice Number: <strong>{invoice_number}</strong></li>
                        <li>Total Amount Due: <strong>{total_amount}</strong></li>
                        <li>Payment Terms: Net 30 days</li>
                    </ul>
                </div>
                
                <p>The invoice includes detailed information about the days worked, hours, and rates. Payment can be made via your preferred method, and please reference the invoice number when making payment.</p>
                
                <p>If you have any questions about this invoice or need any clarification, please don't hesitate to reach out to me.</p>
                
                <p>Thank you for your continued business and trust in my services.</p>
                
                <p>Best regards,<br>
                <strong>{config.COMPANY_NAME}</strong><br>
                {config.COMPANY_EMAIL}<br>
                {config.COMPANY_PHONE}</p>
            </div>
        </body>
        </html>
        """
