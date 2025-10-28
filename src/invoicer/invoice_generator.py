"""
PDF Invoice Generator

This module handles the creation of professional PDF invoices using ReportLab.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_RIGHT, TA_LEFT

from invoicer import config
from invoicer.models import InvoiceModel, InvoiceItemModel, InvoiceClientInfoModel


def invoice_model_to_dict(invoice_model: InvoiceModel) -> Dict:
    """Convert InvoiceModel to dictionary format for backwards compatibility"""
    return {
        "invoice_number": invoice_model.invoice_number,
        "invoice_date": invoice_model.invoice_date.strftime("%B %d, %Y"),
        "due_date": invoice_model.due_date,
        "client_info": {
            "name": invoice_model.client_info.name,
            "email": invoice_model.client_info.email,
            "client_code": invoice_model.client_info.client_code,
            "address": invoice_model.client_info.address,
        },
        "client_id": invoice_model.client_info.client_id,
        "days_worked": invoice_model.days_worked or 0,
        "project_description": invoice_model.project_description or "",
        "period": invoice_model.period or "",
        "tax_rate": invoice_model.tax_rate,
        "payment_terms": invoice_model.payment_terms,
        "thank_you_note": invoice_model.thank_you_note
        or f"Thank you for your business! For questions about this invoice, please contact us at {config.COMPANY_EMAIL} or {config.COMPANY_PHONE}.",
    }


def dict_to_invoice_model(invoice_dict: Dict) -> InvoiceModel:
    """Convert dictionary to InvoiceModel for type safety and validation"""
    client_info_dict = invoice_dict.get("client_info", {})

    # Calculate financial details from days_worked if needed
    days_worked = invoice_dict.get("days_worked", 0)
    hours_per_day = config.HOURS_PER_DAY
    hourly_rate = config.HOURLY_RATE
    total_hours = days_worked * hours_per_day
    subtotal = total_hours * hourly_rate
    tax_rate = invoice_dict.get("tax_rate", 0.0)
    tax_amount = subtotal * tax_rate
    total_amount = subtotal + tax_amount

    # Create line item from legacy days_worked approach
    line_items = []
    if days_worked > 0:
        line_item = InvoiceItemModel(
            description=invoice_dict.get(
                "project_description",
                f"Consulting services for {invoice_dict.get('period', 'this month')}",
            ),
            quantity=float(days_worked),
            unit_type="days",
            rate=hourly_rate * hours_per_day,  # Daily rate
            amount=subtotal,
        )
        line_items.append(line_item)

    client_info = InvoiceClientInfoModel(
        name=client_info_dict.get("name", "Unknown Client"),
        email=client_info_dict.get("email", "client@example.com"),
        client_code=client_info_dict.get("client_code", "UNK"),
        address=client_info_dict.get("address", ""),
        client_id=invoice_dict.get("client_id"),
    )

    invoice_date = datetime.now()
    if "invoice_date" in invoice_dict:
        # Try to parse the date if it's a string
        date_str = invoice_dict["invoice_date"]
        if isinstance(date_str, str):
            try:
                invoice_date = datetime.strptime(date_str, "%B %d, %Y")
            except ValueError:
                # Fallback to current date
                invoice_date = datetime.now()
        elif isinstance(date_str, datetime):
            invoice_date = date_str

    return InvoiceModel(
        invoice_number=invoice_dict.get("invoice_number", "INV-001"),
        invoice_date=invoice_date,
        due_date=invoice_dict.get("due_date", "Net 30 days"),
        client_info=client_info,
        line_items=line_items,
        days_worked=days_worked,
        project_description=invoice_dict.get("project_description"),
        period=invoice_dict.get("period"),
        subtotal=subtotal,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total_amount=total_amount,
        payment_terms=invoice_dict.get(
            "payment_terms",
            "Payment is due within 30 days of invoice date. Late payments may incur additional charges.",
        ),
        thank_you_note=invoice_dict.get("thank_you_note"),
    )


class InvoiceGenerator:
    def __init__(self, page_size=A4):
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

    def create_invoice(self, invoice_data: Union[Dict, InvoiceModel]) -> Path:
        """
        Create a PDF invoice and return the file path

        Args:
            invoice_data: Dictionary or InvoiceModel containing invoice information

        Returns:
            str: Path to the generated PDF file
        """
        # Convert InvoiceModel to dict if needed for backwards compatibility with existing code
        if isinstance(invoice_data, InvoiceModel):
            invoice_data = invoice_model_to_dict(invoice_data)

        # Get client info and invoice details
        invoice_number = invoice_data.get("invoice_number", "INV-001")
        client_info = invoice_data.get("client_info", {})
        client_code = client_info.get("client_code", "CLIENT")
        invoice_date = datetime.now()
        year = invoice_date.year

        # Create year/client directory structure
        year_dir = Path(config.INVOICES_DIR) / str(year)
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

    def _build_header(self, invoice_data: Dict) -> List:
        """Build the invoice header with company info and invoice title"""
        elements = []

        # Create a table for header layout
        header_data = [
            [
                Paragraph(config.COMPANY_NAME, self.styles["CompanyHeader"]),
                Paragraph("INVOICE", self.styles["InvoiceTitle"]),
            ],
            [
                Paragraph(
                    config.COMPANY_ADDRESS.replace("\n", "<br/>"),
                    self.styles["Address"],
                ),
                Paragraph(
                    f"Invoice #: {invoice_data.get('invoice_number', 'INV-001')}<br/>"
                    f"Date: {invoice_data.get('invoice_date', datetime.now().strftime('%B %d, %Y'))}<br/>"
                    f"Due Date: {invoice_data.get('due_date', 'Upon Receipt')}",
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

    def _build_invoice_details(self, invoice_data: Dict) -> List:
        """Build the bill to and invoice details section"""
        elements = []

        # Bill To section
        bill_to = invoice_data.get("client_info", {})
        client_address = bill_to.get("address", "Client Address\nCity, State ZIP")

        details_data = [
            [Paragraph("<b>Bill To:</b>", self.styles["Normal"]), ""],
            [
                Paragraph(
                    f"{bill_to.get('name', 'Client Name')}<br/>"
                    f"{client_address.replace(chr(10), '<br/>')}<br/>"
                    f"Email: {bill_to.get('email', 'client@example.com')}",
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

    def _build_line_items(self, invoice_data: Dict) -> List:
        """Build the line items table"""
        elements = []

        # Calculate values
        days_worked = invoice_data.get("days_worked", 0)
        hours_per_day = config.HOURS_PER_DAY
        hourly_rate = config.HOURLY_RATE
        total_hours = days_worked * hours_per_day
        subtotal = total_hours * hourly_rate

        # Project description
        project_description = invoice_data.get(
            "project_description",
            f"Consulting services for {invoice_data.get('period', 'this month')}",
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
                f"{config.CURRENCY_SYMBOL}{hourly_rate:,.2f}",
                f"{total_hours:,.1f}",
                f"{config.CURRENCY_SYMBOL}{subtotal:,.2f}",
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

    def _build_totals(self, invoice_data: Dict) -> List:
        """Build the totals section"""
        elements = []

        # Calculate totals
        days_worked = invoice_data.get("days_worked", 0)
        total_hours = days_worked * config.HOURS_PER_DAY
        subtotal = total_hours * config.HOURLY_RATE
        tax_rate = invoice_data.get("tax_rate", 0.0)
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount

        # Build totals table
        totals_data = [["", "Subtotal:", f"{config.CURRENCY_SYMBOL}{subtotal:,.2f}"]]

        if tax_rate > 0:
            totals_data.append(
                [
                    "",
                    f"Tax ({tax_rate * 100:.1f}%):",
                    f"{config.CURRENCY_SYMBOL}{tax_amount:,.2f}",
                ]
            )

        totals_data.append(
            ["", "Total Amount Due:", f"{config.CURRENCY_SYMBOL}{total_amount:,.2f}"]
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

    def _build_footer(self, invoice_data: Dict) -> List:
        """Build the invoice footer with payment terms and contact info"""
        elements = []

        # Payment terms
        payment_terms = invoice_data.get(
            "payment_terms",
            "Payment is due within 30 days of invoice date. "
            "Late payments may incur additional charges.",
        )

        elements.append(Paragraph("<b>Payment Terms:</b>", self.styles["Normal"]))
        elements.append(Paragraph(payment_terms, self.styles["Normal"]))
        elements.append(Spacer(1, 20))

        # Thank you note
        thank_you = invoice_data.get(
            "thank_you_note",
            "Thank you for your business! For questions about this invoice, "
            f"please contact us at {config.COMPANY_EMAIL} or {config.COMPANY_PHONE}.",
        )

        elements.append(Paragraph(thank_you, self.styles["Normal"]))

        return elements


def generate_invoice_number(
    client_code: str, invoice_date: datetime | None = None
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
        return config.INVOICE_NUMBER_TEMPLATE.format(**template_vars)
    except KeyError:
        # Fallback to default format if template has invalid variables
        return f"INV-{invoice_date.strftime('%Y%m')}-{client_code}"


def create_sample_invoice_data(
    client_name: str = "Sample Client",
    client_email: str = "client@example.com",
    client_code: str = "SAM",
    days_worked: int = 20,
    month_year: str | None = None,
    return_model: bool = False,
) -> Union[Dict, InvoiceModel]:
    """
    Create sample invoice data for testing

    Args:
        client_name: Name of the client
        client_email: Client's email address
        client_code: Client's code (e.g., "ACM", "TSS")
        days_worked: Number of days worked
        month_year: Month and year for the invoice (e.g., "October 2024")
        return_model: If True, return InvoiceModel; if False, return Dict

    Returns:
        Dict or InvoiceModel: Invoice data
    """
    if not month_year:
        month_year = datetime.now().strftime("%B %Y")

    # Generate invoice number using the client code
    invoice_number = generate_invoice_number(client_code)

    # Create the dictionary format first
    invoice_dict = {
        "invoice_number": invoice_number,
        "invoice_date": datetime.now().strftime("%B %d, %Y"),
        "due_date": "Net 30 days",
        "client_info": {
            "name": client_name,
            "email": client_email,
            "client_code": client_code,
            "address": "Client Company\n123 Business Ave\nCity, State 12345",
        },
        "days_worked": days_worked,
        "project_description": f"Consulting services for {month_year}",
        "period": month_year,
        "tax_rate": 0.0,  # Set to 0.08 for 8% tax, etc.
    }

    if return_model:
        return dict_to_invoice_model(invoice_dict)
    else:
        return invoice_dict
