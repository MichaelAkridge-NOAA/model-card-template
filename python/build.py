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
def header_footer(canvas, doc):
    # Draw the logo in top left
    canvas.saveState()
    logo = Image(logo_path, width=1.8*inch, height=0.65*inch)
    logo.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - 0.65*inch)
    canvas.restoreState()

doc = SimpleDocTemplate(
    pdf_path,
    pagesize=letter,
    topMargin=1.0*inch,
    bottomMargin=0.5*inch,
    leftMargin=0.5*inch,
    rightMargin=0.5*inch
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

# Header section with title and version
elements.append(Paragraph(f"{data['model_name']}", styles['ModelCardTitle']))
elements.append(Paragraph(f"Version {data['model_details']['version']} | {data['model_details']['release_date']}", styles['ModelCardSubtitle']))

# Create main sections
sections = []

# 1. Summary section (with example detection)
summary_items = []
summary_items.append(Paragraph("📋 Model Summary", styles['ModelCardSection']))
# Combine all summary points into a single paragraph
summary_text = " ".join([point.replace("**", "") for point in data['plain_language_summary']])
summary_items.append(Paragraph(summary_text, styles['BodyText']))
summary_items.append(Spacer(1, 10))

# Add example detection with caption
img_data = [[
    Image(detection_img_path, width=4*inch, height=2.5*inch)
]]
img_table = Table(img_data)
img_table.setStyle(TableStyle([
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
summary_items.append(img_table)
summary_items.append(Paragraph("Example detection on underwater footage", styles['BodyText']))
sections.append(summary_items)

# 2. Performance metrics section
metrics_items = []
metrics_items.append(Paragraph("📊 Model Performance", styles['ModelCardSection']))
metrics_items.append(create_metric_table(data['key_numbers']))
metrics_items.append(Spacer(1, 10))

# Add PR curve
img_data = [[
    Image(pr_curve_img_path, width=3*inch, height=2*inch)
]]
pr_table = Table(img_data)
pr_table.setStyle(TableStyle([
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
metrics_items.append(pr_table)
sections.append(metrics_items)

# 3. Usage and implementation section
usage_items = []
usage_items.append(Paragraph("⚙️ Usage Guide", styles['ModelCardSection']))
usage_items.append(Paragraph("<b>Technical Details</b>", styles['BodyText']))
details_text = f"""
• Architecture: {data['model_details']['architecture']}
• Input Size: {data['model_details']['input_size']}
• Training Data: {data['model_details']['training_data']}
"""
usage_items.append(Paragraph(details_text, styles['BodyText']))
usage_items.append(Spacer(1, 5))

usage_items.append(Paragraph("<b>Confidence Threshold Settings</b>", styles['BodyText']))
for threshold in data['confidence_thresholds']:
    desc = threshold['description'].replace('<i>', '').replace('</i>', '')
    usage_items.append(Paragraph(f"• {threshold['threshold']}: {desc}", styles['BodyText']))
sections.append(usage_items)

# Create sections table
section_data = []
for i in range(0, len(sections), 2):
    row = []
    row.append(sections[i])
    if i + 1 < len(sections):
        row.append(sections[i + 1])
    else:
        row.append([])  # Empty cell if odd number of sections
    section_data.append(row)

main_table = Table(section_data, colWidths=[3.7*inch, 3.7*inch])
maihttps://huggingface.co/akridge/yolo11-fish-detector-grayscalen_table.setStyle(TableStyle([
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
]))

# Add the sections layout
elements.append(main_table)
elements.append(Spacer(1, 10))

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
