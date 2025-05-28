import json
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

# Load model card data
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
with open(os.path.join(root_dir, 'model_card_data.json')) as f:
    data = json.load(f)

# Set up paths
logo_path = os.path.join(root_dir, 'assets', 'NOAA_FISHERIES_logoH_web.png')
pr_curve_img_path = os.path.join(root_dir, 'assets', 'example_PR_curve.png')
detection_img_path = os.path.join(root_dir, 'assets', 'example_detection.png')
pdf_path = os.path.join(root_dir, 'Model_Card.pdf')

# Colors
PRIMARY_COLOR = HexColor("#005CB9")
TEXT_COLOR = HexColor("#1a1a1a")
LIGHT_GRAY = HexColor("#f5f5f5")

# Setup styles
styles = getSampleStyleSheet()

# Create custom styles
styles.add(ParagraphStyle(
    name='ModelCardTitle',
    parent=styles['Title'],
    fontSize=24,
    leading=28,
    textColor=PRIMARY_COLOR,
    alignment=TA_CENTER,
    spaceAfter=20
))

styles.add(ParagraphStyle(
    name='ModelCardSubtitle',
    parent=styles['Title'],
    fontSize=14,
    leading=18,
    textColor=TEXT_COLOR,
    alignment=TA_CENTER,
    spaceAfter=20
))
styles.add(ParagraphStyle(
    name='SectionHeader',
    fontSize=12,
    leading=14,
    textColor=PRIMARY_COLOR,
    spaceBefore=15,
    spaceAfter=5,
    bold=True
))
styles.add(ParagraphStyle(
    name='BodyText',
    fontSize=10,
    leading=14,
    textColor=TEXT_COLOR
))
styles.add(ParagraphStyle(
    name='Footer',
    fontSize=8,
    leading=10,
    textColor=TEXT_COLOR,
    alignment=TA_CENTER
))

def create_metric_table(metrics):
    """Create a table for model metrics"""
    table_data = [[Paragraph(f"<b>{m['metric']}</b>", styles['BodyText']),
                  Paragraph(m['value'], styles['BodyText']),
                  Paragraph(m['meaning'], styles['BodyText'])] for m in metrics]
    
    t = Table(table_data, colWidths=[1.5*inch, 1*inch, 3.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('GRID', (0, 0), (-1, -1), 0.5, TEXT_COLOR),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return t

# Build PDF content
doc = SimpleDocTemplate(
    pdf_path,
    pagesize=letter,
    topMargin=0.75*inch,
    bottomMargin=0.75*inch,
    leftMargin=0.75*inch,
    rightMargin=0.75*inch
)

elements = []

# Header with logo
logo = Image(logo_path, width=2.5*inch, height=0.9*inch)
elements.append(logo)
elements.append(Spacer(1, 20))

# Title and version
elements.append(Paragraph(f"{data['model_name']}", styles['ModelCardTitle']))
elements.append(Paragraph(f"Version {data['model_details']['version']} | {data['model_details']['release_date']}", styles['ModelCardSubtitle']))

# Plain language summary
elements.append(Paragraph("What This Model Does", styles['SectionHeader']))
for point in data['plain_language_summary']:
    elements.append(Paragraph(f"• {point}", styles['BodyText']))
elements.append(Spacer(1, 10))

# Key metrics
elements.append(Paragraph("Model Performance", styles['SectionHeader']))
elements.append(create_metric_table(data['key_numbers']))
elements.append(Spacer(1, 15))

# Model details in a cleaner format
elements.append(Paragraph("Technical Details", styles['SectionHeader']))
details_text = f"""
• <b>Architecture:</b> {data['model_details']['architecture']}
• <b>Input Size:</b> {data['model_details']['input_size']}
• <b>Training Data:</b> {data['model_details']['training_data']}
"""
elements.append(Paragraph(details_text, styles['BodyText']))
elements.append(Spacer(1, 15))

# Confidence thresholds
elements.append(Paragraph("Confidence Threshold Guide", styles['SectionHeader']))
for threshold in data['confidence_thresholds']:
    elements.append(Paragraph(
        f"• <b>{threshold['threshold']}</b> - {threshold['description']}",
        styles['BodyText']
    ))
elements.append(Spacer(1, 15))

# Images side by side using a table
img_table_data = [[
    Image(detection_img_path, width=3*inch, height=3*inch),
    Image(pr_curve_img_path, width=3*inch, height=3*inch)
]]
img_table = Table(img_table_data, colWidths=[3.5*inch, 3.5*inch])
img_table.setStyle(TableStyle([
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
elements.append(img_table)
elements.append(Spacer(1, 15))

# Quote and disclaimer
elements.append(Paragraph(data['quote'], styles['ModelCardSubtitle']))
elements.append(Paragraph(data['disclaimer'], styles['BodyText']))

# Footer
footer_text = f"""
{data['footer_info']['organization']} | Contact: {data['footer_info']['contact_email']} | Version {data['footer_info']['version']} | {data['footer_info']['year']}
"""
elements.append(Spacer(1, 20))
elements.append(Paragraph(footer_text, styles['Footer']))

# Build the PDF
doc.build(elements)

print(f"Model card PDF created at: {pdf_path}")
