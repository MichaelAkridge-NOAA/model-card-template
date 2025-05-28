import json
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, Table, TableStyle, Frame, PageTemplate
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

# Create new styles
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
    name='ModelCardSection',
    parent=styles['Heading2'],
    fontSize=12,
    leading=14,
    textColor=PRIMARY_COLOR,
    spaceBefore=15,
    spaceAfter=5,
    bold=True
))

# Modify existing styles instead of adding new ones
styles['BodyText'].fontSize = 10
styles['BodyText'].leading = 14
styles['BodyText'].textColor = TEXT_COLOR

# Create custom footer style
styles.add(ParagraphStyle(
    name='ModelCardFooter',
    parent=styles['BodyText'],
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

# Build PDF content with a frame for the header
from reportlab.platypus import Frame, PageTemplate

def header_footer(canvas, doc):
    # Draw the logo in top left
    canvas.saveState()
    logo = Image(logo_path, width=1.8*inch, height=0.65*inch)
    logo.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - 0.65*inch)
    canvas.restoreState()

doc = SimpleDocTemplate(
    pdf_path,
    pagesize=letter,
    topMargin=1.2*inch,  # Increased top margin for logo
    bottomMargin=0.75*inch,
    leftMargin=0.75*inch,
    rightMargin=0.75*inch
)

# Add header to page template
template = PageTemplate(
    'normal',
    frames=[Frame(
        doc.leftMargin, 
        doc.bottomMargin, 
        doc.width, 
        doc.height,
        id='normal'
    )],
    onPage=header_footer
)
doc.addPageTemplates([template])

elements = []

# Title and version (logo is handled in header)
elements.append(Paragraph(f"{data['model_name']}", styles['ModelCardTitle']))
elements.append(Paragraph(f"Version {data['model_details']['version']} | {data['model_details']['release_date']}", styles['ModelCardSubtitle']))

# Two-column layout for content
left_column = []
right_column = []

# Left column content
left_column.append(Paragraph("What This Model Does", styles['ModelCardSection']))
for point in data['plain_language_summary']:
    left_column.append(Paragraph(f"• {point}", styles['BodyText']))
left_column.append(Spacer(1, 10))

left_column.append(Paragraph("Model Performance", styles['ModelCardSection']))
left_column.append(create_metric_table(data['key_numbers']))
left_column.append(Spacer(1, 10))

# Right column content
# Example detection image at top of right column
right_column.append(Image(detection_img_path, width=3.5*inch, height=3.5*inch))
right_column.append(Spacer(1, 10))

right_column.append(Paragraph("Technical Details", styles['ModelCardSection']))
details_text = f"""
• <b>Architecture:</b> {data['model_details']['architecture']}
• <b>Input Size:</b> {data['model_details']['input_size']}
• <b>Training Data:</b> {data['model_details']['training_data']}
"""
right_column.append(Paragraph(details_text, styles['BodyText']))
right_column.append(Spacer(1, 10))

# Confidence thresholds with more detail
right_column.append(Paragraph("Confidence Threshold Guide", styles['ModelCardSection']))
threshold_text = """
Adjust the confidence threshold to balance between catching all fish and avoiding false detections:
"""
right_column.append(Paragraph(threshold_text, styles['BodyText']))
for threshold in data['confidence_thresholds']:
    desc = threshold['description'].replace('<i>', '').replace('</i>', '')  # Clean up italics
    right_column.append(Paragraph(
        f"• <b>{threshold['threshold']}</b>: {desc}",
        styles['BodyText']
    ))

# Create two-column layout
table_data = [[left_column, right_column]]
main_table = Table(table_data, colWidths=[3.5*inch, 3.5*inch], rowHeights=[7*inch])
main_table.setStyle(TableStyle([
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
]))

# Add the main two-column layout
elements.append(main_table)
elements.append(Spacer(1, 15))

# Quote and disclaimer at bottom
elements.append(Paragraph(data['quote'], styles['ModelCardSubtitle']))
elements.append(Paragraph(data['disclaimer'], styles['BodyText']))

# Footer
footer_text = f"""
{data['footer_info']['organization']} | Contact: {data['footer_info']['contact_email']} | Version {data['footer_info']['version']} | {data['footer_info']['year']}
"""
elements.append(Spacer(1, 10))
elements.append(Paragraph(footer_text, styles['ModelCardFooter']))

# Build the PDF
doc.build(elements)

print(f"Model card PDF created at: {pdf_path}")
