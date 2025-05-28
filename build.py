import json
import re
import sys
import argparse
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, Table, TableStyle, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
from fetch_hf_model_card import fetch_model_card

def build_model_card(model_data_path, output_path=None, assets_dir=None):
    """Build a model card PDF from model data"""
    # Set up paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if assets_dir is None:
        assets_dir = os.path.join(script_dir, 'assets')
    if output_path is None:
        output_path = os.path.join(script_dir, 'Model_Card.pdf')

    # Check for model data
    if not os.path.exists(model_data_path):
        print(f"Error: Model data file not found at {model_data_path}")
        return False

    # Asset paths
    logo_path = os.path.join(assets_dir, 'NOAA_FISHERIES_logoH_web.png')
    pr_curve_img_path = os.path.join(assets_dir, 'example_PR_curve.png')
    detection_img_path = os.path.join(assets_dir, 'example_detection.png')

    # Load model data
    with open(model_data_path, 'r') as f:
        hf_data = json.load(f)

    # Extract key information for the summary
    def extract_metrics_from_text(text):
        metrics = []
        # Look for common metrics patterns
        patterns = {
            'mAP': r'mAP[@\s]*0\.5[\s:]+([0-9.]+)',
            'Precision': r'[Pp]recision[\s:]+([0-9.]+)',
            'Recall': r'[Rr]ecall[\s:]+([0-9.]+)'
        }
        
        for metric, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                metrics.append({
                    "metric": metric,
                    "value": f"<b>{match.group(1)}</b>",
                    "meaning": {
                        'mAP': "Mean Average Precision at 0.5 IOU",
                        'Precision': "Share of detections that are real fish",
                        'Recall': "Share of all fish that are found"
                    }[metric]
                })
        return metrics

    # Create summary data structure
    model_info = hf_data.get("model_info", {})
    data = {
        "model_name": model_info.get("model_name", "Unnamed Model"),
        "model_details": {
            "version": model_info.get("version", "1.0.0"),
            "release_date": model_info.get("release_date", "N/A"),
            "architecture": model_info.get("architecture", "Not specified"),
            "input_size": model_info.get("input_size", "Not specified"),
            "training_data": model_info.get("training_data", "Not specified")
        },
        "plain_language_summary": hf_data["sections"].get("Overview", "No overview available"),
        "key_numbers": extract_metrics_from_text(str(hf_data["sections"])),
        "confidence_thresholds": [
            {"threshold": "0.20", "description": "Maximum recall, more false positives"},
            {"threshold": "0.50", "description": "Balanced detection (default)"},
            {"threshold": "0.80", "description": "High precision, fewer false positives"}
        ],
        "footer_info": {
            "organization": "NOAA / CIMAR",
            "contact_email": "michael.akridge@noaa.gov",
            "version": "1.0",
            "year": "2025"
        }
    }

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
    def safe_load_image(path, default_width, default_height):
        """Load an image file with fallback for missing files"""
        if os.path.exists(path):
            return Image(path, width=default_width, height=default_height)
        print(f"Warning: Image file not found: {path}")
        # Return an empty spacer instead
        return Spacer(default_width, default_height)

    def header_footer(canvas, doc):
        # Draw the logo in top left
        if os.path.exists(logo_path):
            canvas.saveState()
            logo = Image(logo_path, width=1.8*inch, height=0.65*inch)
            logo.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - 0.65*inch)
            canvas.restoreState()

    doc = SimpleDocTemplate(
        output_path,
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
        safe_load_image(detection_img_path, 4*inch, 2.5*inch)
    ]]
    img_table = Table(img_data)
    img_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    summary_items.append(img_table)
    if os.path.exists(detection_img_path):
        summary_items.append(Paragraph("Example detection on underwater footage", styles['BodyText']))
    sections.append(summary_items)

    # 2. Performance metrics section
    metrics_items = []
    metrics_items.append(Paragraph("📊 Model Performance", styles['ModelCardSection']))
    metrics_items.append(create_metric_table(data['key_numbers']))
    metrics_items.append(Spacer(1, 10))

    # Add PR curve if available
    img_data = [[
        safe_load_image(pr_curve_img_path, 3*inch, 2*inch)
    ]]
    pr_table = Table(img_data)
    pr_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    if os.path.exists(pr_curve_img_path):
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
    main_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))

    # Add the sections layout
    elements.append(main_table)
    elements.append(Spacer(1, 10))

    # Quote and disclaimer at bottom
    if 'quote' in data and data['quote']:
        elements.append(Paragraph(data['quote'], styles['ModelCardSubtitle']))
    if 'disclaimer' in data and data['disclaimer']:
        elements.append(Paragraph(data['disclaimer'], styles['BodyText']))

    # Footer
    footer_text = f"""
    {data['footer_info']['organization']} | Contact: {data['footer_info']['contact_email']} | Version {data['footer_info']['version']} | {data['footer_info']['year']}
    """
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(footer_text, styles['ModelCardFooter']))

    # Build the PDF
    doc.build(elements)
    print(f"Model card PDF created at: {output_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Build a model card PDF from a Hugging Face model')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--url', '-u', help='URL of the Hugging Face model')
    group.add_argument('--data', '-d', help='Path to existing model_data.json file')
    parser.add_argument('--output', '-o', help='Output path for the PDF file')
    parser.add_argument('--assets', '-a', help='Directory containing asset files (images)')
    args = parser.parse_args()

    # If URL is provided, fetch the data first
    if args.url:
        try:
            model_data_path = fetch_model_card(args.url)
        except Exception as e:
            print(f"Error fetching model card data: {e}")
            return 1
    else:
        model_data_path = args.data

    # Build the model card
    success = build_model_card(
        model_data_path=model_data_path,
        output_path=args.output,
        assets_dir=args.assets
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
