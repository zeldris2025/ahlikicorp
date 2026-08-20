from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
import io
from django.conf import settings

def generate_quote_pdf(quote):
    """Generate a PDF file for a quote using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3a5f'),
        spaceAfter=30,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1e3a5f'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )

    elements = []

    # Header
    elements.append(Paragraph(f'Quote #{quote.reference}', title_style))
    elements.append(Spacer(1, 0.3*inch))

    # Customer Info
    elements.append(Paragraph('Bill To:', heading_style))
    cust_info = f"""
    {quote.customer_name}<br/>
    {quote.company or 'N/A'}<br/>
    {quote.email}<br/>
    {quote.phone}
    """
    elements.append(Paragraph(cust_info, styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))

    # Items Table
    elements.append(Paragraph('Order Details:', heading_style))
    items_data = [['SKU', 'Product', 'Qty', 'Unit Price', 'Total']]
    for item in quote.items.all():
        items_data.append([
            item.product.sku,
            item.product.name,
            str(item.quantity),
            f'${item.unit_price or 0:.2f}' if item.unit_price else 'TBD',
            f'${item.line_total:.2f}' if item.unit_price else 'TBD',
        ])

    items_table = Table(items_data, colWidths=[1*inch, 2.5*inch, 0.8*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.2*inch))

    # Totals
    totals_data = [
        ['Subtotal', f'${quote.subtotal:.2f}'],
        ['Tax ({quote.tax_rate}%)', f'${quote.tax_total:.2f}'],
        ['TOTAL', f'${quote.total:.2f}'],
    ]
    totals_table = Table(totals_data, colWidths=[4*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 12),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.whitesmoke),
    ]))
    elements.append(totals_table)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
