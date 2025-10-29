"""
PDF Invoice Generator

This module handles the creation of professional PDF invoices using ReportLab.
"""

from datetime import datetime
from pathlib import Path
from typing import List
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_RIGHT, TA_LEFT

from invoicer.config import InvoicerSettings

# from . import config
from .models import InvoiceModel, InvoiceItemModel, InvoiceClientInfoModel


class InvoiceGenerator:
    def __init__(self, settings: InvoicerSettings, page_size=A4):
        self.settings = settings
        self.page_size = page_size
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the invoice"""
        # Company header style
        self.styles.add(
            ParagraphStyle(
                name="CompanyHeader",
                parent=self.styles["Heading1"],
                fontSize=24,
                spaceAfter=12,
                textColor=colors.HexColor("#2E86AB"),
                alignment=TA_LEFT,
            )
        )

        # Invoice title style
        self.styles.add(
            ParagraphStyle(
                name="InvoiceTitle",
                parent=self.styles["Heading1"],
                fontSize=28,
                spaceAfter=20,
                textColor=colors.HexColor("#A23B72"),
                alignment=TA_RIGHT,
            )
        )

        # Address style
        self.styles.add(
            ParagraphStyle(
                name="Address",
                parent=self.styles["Normal"],
                fontSize=10,
                spaceAfter=6,
                alignment=TA_LEFT,
            )
        )

        # Right aligned text style
        self.styles.add(
            ParagraphStyle(
                name="RightAlign",
                parent=self.styles["Normal"],
                fontSize=10,
                alignment=TA_RIGHT,
            )
        )

    def create_invoice(self, invoice_data: InvoiceModel) -> Path:
        """
        Create a PDF invoice and return the file path

        Args:
            invoice_data: InvoiceModel containing invoice information

        Returns:
            str: Path to the generated PDF file
        """

        # Get client info and invoice details
        invoice_number = invoice_data.invoice_number
        client_code = invoice_data.client_info.client_code
        invoice_date = invoice_data.invoice_date
        year = invoice_date.year

        # Create year/client directory structure
        year_dir = Path(self.settings.invoices_dir) / str(year)
        client_dir = year_dir / client_code
        client_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"Invoice_{invoice_number}.pdf"
        filepath = client_dir / filename

        # Create the PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Build the invoice content
        story = []
        story.extend(self._build_header(invoice_data))
        story.append(Spacer(1, 20))
        story.extend(self._build_invoice_details(invoice_data))
        story.append(Spacer(1, 20))
        story.extend(self._build_line_items(invoice_data))
        story.append(Spacer(1, 20))
        story.extend(self._build_totals(invoice_data))
        story.append(Spacer(1, 30))
        story.extend(self._build_footer(invoice_data))

        # Generate the PDF
        doc.build(story)

        return filepath

    def _build_header(self, invoice_data: InvoiceModel) -> List:
        """Build the invoice header with company info and invoice title"""
        elements = []

        # Create a table for header layout
        header_data = [
            [
                Paragraph(self.settings.company_name, self.styles["CompanyHeader"]),
                Paragraph("INVOICE", self.styles["InvoiceTitle"]),
            ],
            [
                Paragraph(
                    self.settings.company_address.replace("\n", "<br/>"),
                    self.styles["Address"],
                ),
                Paragraph(
                    f"Invoice #: {invoice_data.invoice_number}<br/>"
                    f"Date: {invoice_data.invoice_date.strftime('%B %d, %Y')}<br/>"
                    f"Due Date: {invoice_data.due_date}",
                    self.styles["RightAlign"],
                ),
            ],
        ]

        header_table = Table(header_data, colWidths=[3.5 * inch, 3 * inch])
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        elements.append(header_table)
        elements.append(
            HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2E86AB"))
        )

        return elements

    def _build_invoice_details(self, invoice_data: InvoiceModel) -> List:
        """Build the bill to and invoice details section"""
        elements = []

        # Bill To section
        client_info = invoice_data.client_info
        client_address = client_info.address or "Client Address\nCity, State ZIP"

        details_data = [
            [Paragraph("<b>Bill To:</b>", self.styles["Normal"]), ""],
            [
                Paragraph(
                    f"{client_info.name}<br/>"
                    f"{client_address.replace(chr(10), '<br/>')}<br/>"
                    f"Email: {client_info.email}",
                    self.styles["Address"],
                ),
                "",
            ],
        ]

        details_table = Table(details_data, colWidths=[4 * inch, 2.5 * inch])
        details_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        elements.append(details_table)

        return elements

    def _build_line_items(self, invoice_data: InvoiceModel) -> List:
        """Build the line items table"""
        elements = []

        # Calculate values
        days_worked = invoice_data.days_worked or 0
        hours_per_day = self.settings.hours_per_day
        hourly_rate = self.settings.hourly_rate
        total_hours = days_worked * hours_per_day
        subtotal = total_hours * hourly_rate

        # Project description
        project_description = (
            invoice_data.project_description
            or f"Consulting services for {invoice_data.period or 'this month'}"
        )
        # Table headers
        line_items_data = [
            ["Description", "Days", "Hours/Day", "Rate/Hour", "Total Hours", "Amount"]
        ]

        # Line item
        line_items_data.append(
            [
                project_description,
                f"{days_worked:,}",
                f"{hours_per_day:.1f}",
                f"{self.settings.currency_symbol}{hourly_rate:,.2f}",
                f"{total_hours:,.1f}",
                f"{self.settings.currency_symbol}{subtotal:,.2f}",
            ]
        )

        # Create table
        line_items_table = Table(
            line_items_data,
            colWidths=[
                2.5 * inch,
                0.6 * inch,
                0.8 * inch,
                0.8 * inch,
                0.8 * inch,
                1 * inch,
            ],
        )

        # Style the table
        line_items_table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E86AB")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    # Data rows
                    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                    ("ALIGN", (0, 1), (0, -1), "LEFT"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F8F9FA")],
                    ),
                ]
            )
        )

        elements.append(line_items_table)

        return elements

    def _build_totals(self, invoice_data: InvoiceModel) -> List:
        """Build the totals section"""
        elements = []

        # Use the calculated totals from the InvoiceModel
        subtotal = invoice_data.subtotal
        tax_rate = invoice_data.tax_rate
        tax_amount = invoice_data.tax_amount
        total_amount = invoice_data.total_amount

        # Build totals table
        totals_data = [
            ["", "Subtotal:", f"{self.settings.currency_symbol}{subtotal:,.2f}"]
        ]

        if tax_rate > 0:
            totals_data.append(
                [
                    "",
                    f"Tax ({tax_rate * 100:.1f}%):",
                    f"{self.settings.currency_symbol}{tax_amount:,.2f}",
                ]
            )

        totals_data.append(
            [
                "",
                "Total Amount Due:",
                f"{self.settings.currency_symbol}{total_amount:,.2f}",
            ]
        )

        totals_table = Table(totals_data, colWidths=[4 * inch, 1.5 * inch, 1 * inch])
        totals_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (1, 0), (-1, -2), "Helvetica-Bold"),
                    ("FONTNAME", (1, -1), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (1, -1), (-1, -1), 12),
                    ("TEXTCOLOR", (1, -1), (-1, -1), colors.HexColor("#A23B72")),
                    ("LINEBELOW", (1, -1), (-1, -1), 2, colors.HexColor("#A23B72")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        elements.append(totals_table)

        return elements

    def _build_footer(self, invoice_data: InvoiceModel) -> List:
        """Build the invoice footer with payment terms and contact info"""
        elements = []

        # Payment terms
        payment_terms = invoice_data.payment_terms

        elements.append(Paragraph("<b>Payment Terms:</b>", self.styles["Normal"]))
        elements.append(Paragraph(payment_terms, self.styles["Normal"]))
        elements.append(Spacer(1, 20))

        # Thank you note
        thank_you = invoice_data.thank_you_note or (
            "Thank you for your business! For questions about this invoice, "
            f"please contact us at {self.settings.company_email} or {self.settings.company_phone}."
        )

        elements.append(Paragraph(thank_you, self.styles["Normal"]))

        return elements


def generate_invoice_number(
    invoice_number_template, client_code: str, invoice_date: datetime | None = None
) -> str:
    """
    Generate invoice number using the configured template

    Args:
        client_code: Client code (e.g., "ACM", "TSS") - manually defined
        invoice_date: Date for the invoice (defaults to current date)

    Returns:
        str: Generated invoice number

    Available template variables:
        - {year}: Full year (e.g., 2024)
        - {month}: Month number (1-12)
        - {month:02d}: Zero-padded month (01-12)
        - {day}: Day of month (1-31)
        - {day:02d}: Zero-padded day (01-31)
        - {client_code}: Manually defined client code
        - {invoice_number}: Sequential invoice number (starting from 001)
    """
    if invoice_date is None:
        invoice_date = datetime.now()

    # Generate a simple sequential number based on year and month
    # In a real implementation, this would come from a database
    invoice_counter = 1  # This could be enhanced to read from a file or database

    template_vars = {
        "year": invoice_date.year,
        "month": invoice_date.month,
        "day": invoice_date.day,
        "client_code": client_code,
        "invoice_number": f"{invoice_counter:03d}",
    }

    try:
        return invoice_number_template.format(**template_vars)
    except KeyError:
        # Fallback to default format if template has invalid variables
        return f"INV-{invoice_date.strftime('%Y%m')}-{client_code}"


def create_sample_invoice_data(
    settings: InvoicerSettings,
    client_name: str = "Sample Client",
    client_email: str = "client@example.com",
    client_code: str = "SAM",
    days_worked: int = 20,
    month_year: str | None = None,
) -> InvoiceModel:
    """
    Create sample invoice data for testing

    Args:
        client_name: Name of the client
        client_email: Client's email address
        client_code: Client's code (e.g., "ACM", "TSS")
        days_worked: Number of days worked
        month_year: Month and year for the invoice (e.g., "October 2024")

    Returns:
        InvoiceModel: Invoice data
    """
    if not month_year:
        month_year = datetime.now().strftime("%B %Y")

    # Generate invoice number using the client code
    invoice_number = generate_invoice_number(
        settings.invoice_number_template, client_code
    )

    assert isinstance(invoice_number, str), f"Expected str, got {type(invoice_number)}"

    # Calculate financial details
    hours_per_day = settings.hours_per_day
    hourly_rate = settings.hourly_rate
    total_hours = days_worked * hours_per_day
    subtotal = total_hours * hourly_rate
    tax_rate = 0.0  # Set to 0.08 for 8% tax, etc.
    tax_amount = subtotal * tax_rate
    total_amount = subtotal + tax_amount

    # Create client info
    client_info = InvoiceClientInfoModel(
        name=client_name,
        email=client_email,
        client_code=client_code,
        address="Client Company\n123 Business Ave\nCity, State 12345",
        client_id=None,
    )

    # Create line item
    project_description = f"Consulting services for {month_year}"
    line_items = []
    if days_worked > 0:
        line_item = InvoiceItemModel(
            description=project_description,
            quantity=float(days_worked),
            unit_type="days",
            rate=hourly_rate * hours_per_day,  # Daily rate
            amount=subtotal,
        )
        line_items.append(line_item)

    # Create invoice model
    return InvoiceModel(
        invoice_number=invoice_number,
        invoice_date=datetime.now(),
        due_date="Net 30 days",
        client_info=client_info,
        line_items=line_items,
        days_worked=days_worked,
        project_description=project_description,
        period=month_year,
        subtotal=subtotal,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total_amount=total_amount,
        payment_terms="Payment is due within 30 days of invoice date. Late payments may incur additional charges.",
        thank_you_note=None,
    )
