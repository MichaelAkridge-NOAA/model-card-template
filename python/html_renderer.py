from __future__ import annotations

import base64
import html
import mimetypes
import os
from typing import Optional

import markdown

from python.model_card_document import (
    BulletListBlock,
    CardDocument,
    CardSection,
    ImageBlock,
    KeyValueListBlock,
    MetricTableBlock,
    TextBlock,
)


THEMES = {
    "noaa": """
body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
  background: #f3f7fb;
  color: #1a1a1a;
}

.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px 48px;
}

.masthead {
  text-align: center;
  margin-bottom: 24px;
}

.template-badge {
  display: inline-block;
  margin-bottom: 12px;
  padding: 6px 12px;
  border-radius: 999px;
  background: #d9ecff;
  color: #005cb9;
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.title {
  margin: 0 0 8px;
  color: #005cb9;
  font-size: 2.4rem;
}

.subtitle {
  margin: 0;
  color: #34495e;
  font-size: 1rem;
}

.logo {
  display: block;
  max-width: 240px;
  margin: 0 auto 18px;
}

.section-grid {
  column-width: 320px;
  column-gap: 20px;
}

.card-section {
  background: #ffffff;
  border: 1px solid #d5e2ef;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 8px 24px rgba(0, 56, 101, 0.08);
  display: inline-block;
  width: 100%;
  box-sizing: border-box;
  margin: 0 0 20px;
  break-inside: avoid;
  -webkit-column-break-inside: avoid;
}

.card-section h2 {
  margin-top: 0;
  color: #005cb9;
}

.block-title {
  margin: 0 0 10px;
  font-size: 1rem;
}

.metric-table {
  width: 100%;
  border-collapse: collapse;
}

.metric-table th,
.metric-table td {
  padding: 10px;
  border-bottom: 1px solid #d5e2ef;
  text-align: left;
  vertical-align: top;
}

.metric-table th {
  color: #005cb9;
}

.metric-value {
  font-weight: 700;
}

.image-block {
  margin-top: 16px;
}

.image-block img {
  width: 100%;
  border-radius: 12px;
  border: 1px solid #d5e2ef;
}

.image-block figcaption {
  margin-top: 8px;
  font-size: 0.9rem;
  color: #4f6578;
}

.key-value-list,
.bullet-list {
  margin: 0;
  padding-left: 18px;
}

.key-value-list li,
.bullet-list li {
  margin-bottom: 8px;
}

.footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #d5e2ef;
  color: #4f6578;
  font-size: 0.95rem;
  text-align: center;
}
""",
    "noaa_brand_colors": """
body {
  margin: 0;
  font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background: #FFFFFF;
  color: #181818;
  line-height: 1.4;
}

.page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 16px 12px;
}

.masthead {
  text-align: left;
  margin-bottom: 16px;
  border-bottom: 3px solid #003087;
  padding-bottom: 12px;
}

.template-badge {
  display: inline-block;
  margin-bottom: 4px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #0085CA;
  color: #FFFFFF;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.title {
  margin: 0 0 4px;
  color: #003087;
  font-size: 2rem;
}

.subtitle {
  margin: 0;
  color: #646464;
  font-size: 0.9rem;
}

.logo {
  display: block;
  max-width: 180px;
  margin: 0 0 12px;
}

.section-grid {
  column-width: 320px;
  column-gap: 12px;
}

.card-section {
  background: #FFFFFF;
  border: 1px solid #E8E8E8;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  display: inline-block;
  width: 100%;
  box-sizing: border-box;
  margin: 0 0 12px;
  break-inside: avoid;
  -webkit-column-break-inside: avoid;
}

.card-section h2 {
  margin-top: 0;
  margin-bottom: 8px;
  color: #003087;
  font-size: 1.2rem;
  border-bottom: 1px solid #0085CA;
}

.block-title {
  margin: 8px 0 4px;
  font-size: 0.9rem;
  font-weight: 700;
  color: #0085CA;
}

.text-block h2,
.text-block h3 {
  color: #003087;
  font-size: 0.95rem;
  margin: 10px 0 4px;
}

.text-block p {
  margin: 0 0 6px;
  font-size: 0.875rem;
}

.text-block ul,
.text-block ol {
  margin: 0 0 6px;
  padding-left: 16px;
  font-size: 0.875rem;
}

pre,
code {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 0.82rem;
  background: #F4F7FB;
  border-radius: 4px;
}

code {
  padding: 1px 4px;
  color: #003087;
}

pre {
  padding: 10px 12px;
  border: 1px solid #DDE8F4;
  overflow-x: auto;
  margin: 6px 0;
  white-space: pre-wrap;
  word-break: break-word;
}

pre code {
  background: none;
  padding: 0;
  color: inherit;
}

.metric-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.metric-table th,
.metric-table td {
  padding: 6px;
  border-bottom: 1px solid #E8E8E8;
  text-align: left;
}

.metric-table th {
  color: #003087;
  background: #F4F7FB;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.metric-value {
  font-weight: 700;
  color: #003087;
}

.image-block {
  margin-top: 8px;
}

.image-block img {
  width: 100%;
  border-radius: 4px;
  border: 1px solid #E8E8E8;
}

.image-block figcaption {
  margin-top: 4px;
  font-size: 0.8rem;
  color: #646464;
}

.key-value-list,
.bullet-list {
  margin: 0;
  padding-left: 14px;
  font-size: 0.875rem;
}

.key-value-list li,
.bullet-list li {
  margin-bottom: 3px;
}

.footer {
  margin-top: 16px;
  padding-top: 8px;
  border-top: 1px solid #E8E8E8;
  color: #646464;
  font-size: 0.8rem;
  text-align: center;
}
""",
    "graphical": """
body {
  margin: 0;
  font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background: #F8FAFB;
  color: #1a1a1a;
  line-height: 1.5;
}

.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px 48px;
}

.masthead {
  text-align: left;
  margin-bottom: 32px;
  border-bottom: none;
  padding-bottom: 16px;
}

.template-badge {
  display: inline-block;
  margin-bottom: 8px;
  padding: 4px 10px;
  border-radius: 6px;
  background: #0085CA;
  color: #FFFFFF;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.title {
  margin: 0 0 4px;
  color: #003087;
  font-size: 2.8rem;
  font-weight: 700;
}

.subtitle {
  margin: 0;
  color: #646464;
  font-size: 0.95rem;
}

.logo {
  display: block;
  max-width: 200px;
  margin: 0 0 16px;
}

.section-grid {
  column-count: 2;
  column-gap: 20px;
  margin-bottom: 24px;
}

@media (max-width: 900px) {
  .section-grid {
    column-count: 1;
  }
}

.card-section {
  background: white;
  border: none;
  border-left: 6px solid #0085CA;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 56, 101, 0.08);
  position: relative;
  overflow: hidden;
  display: inline-block;
  width: 100%;
  box-sizing: border-box;
  margin: 0 0 20px;
  break-inside: avoid;
  -webkit-column-break-inside: avoid;
}

.card-section[style*="--section-color"] {
  border-left-color: var(--section-color, #0085CA);
  background: linear-gradient(135deg, var(--section-color, #0085CA) 0%, rgba(255,255,255,0) 1%), 
              linear-gradient(to bottom, color-mix(in srgb, var(--section-color, #0085CA) 5%, white), white);
}

.card-section h2 {
  margin: 0 0 16px;
  color: #003087;
  font-size: 1.3rem;
  font-weight: 700;
  border-bottom: none;
}

.block-title {
  margin: 0 0 12px;
  font-size: 1rem;
  font-weight: 700;
  color: #003087;
}

.text-block h2,
.text-block h3 {
  color: #003087;
  font-size: 1rem;
  font-weight: 700;
  margin: 12px 0 6px;
}

.text-block p {
  margin: 0 0 8px;
  font-size: 0.95rem;
}

.text-block ul,
.text-block ol {
  margin: 0 0 8px;
  padding-left: 18px;
  font-size: 0.95rem;
}

/* Metric cards instead of table */
.metric-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin: 16px 0;
}

.metric-card {
  background: white;
  border: 2px solid #E8E8E8;
  border-radius: 12px;
  padding: 12px;
  text-align: center;
}

.metric-card .metric-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #0085CA;
  margin-bottom: 4px;
}

.metric-card .metric-name {
  font-size: 0.85rem;
  font-weight: 700;
  color: #003087;
  margin-bottom: 4px;
}

.metric-card .metric-meaning {
  font-size: 0.75rem;
  color: #646464;
  line-height: 1.3;
}

/* Legacy table support */
.metric-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
  margin: 12px 0;
}

.metric-table th,
.metric-table td {
  padding: 8px;
  border-bottom: 1px solid #E8E8E8;
  text-align: left;
}

.metric-table th {
  color: #003087;
  background: #F4F7FB;
  font-weight: 700;
}

.metric-value {
  font-weight: 700;
  color: #0085CA;
}

pre,
code {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 0.82rem;
  background: #F4F7FB;
  border-radius: 4px;
}

code {
  padding: 1px 4px;
  color: #003087;
}

pre {
  padding: 10px 12px;
  border: 1px solid #DDE8F4;
  overflow-x: auto;
  margin: 8px 0;
  white-space: pre-wrap;
  word-break: break-word;
}

pre code {
  background: none;
  padding: 0;
  color: inherit;
}

.image-block {
  margin-top: 12px;
}

.image-block img {
  width: 100%;
  border-radius: 12px;
  border: 1px solid #E8E8E8;
}

.image-block figcaption {
  margin-top: 8px;
  font-size: 0.85rem;
  color: #646464;
  text-align: center;
}

.key-value-list,
.bullet-list {
  margin: 0;
  padding-left: 18px;
  font-size: 0.95rem;
}

.key-value-list li,
.bullet-list li {
  margin-bottom: 4px;
}

.footer {
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid #E8E8E8;
  color: #646464;
  font-size: 0.9rem;
  text-align: center;
}
"""
}


def render_card_document(document: CardDocument, output_path: str) -> None:
    rendered = render_card_document_to_string(document, output_path)
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(rendered)


def render_card_document_to_string(
    document: CardDocument,
    output_path: Optional[str] = None,
) -> str:
    logo_html = ""
    logo_path = _asset_url(document.logo_path, output_path)
    if logo_path:
        logo_html = f'<img class="logo" src="{logo_path}" alt="Organization logo">'

    sections_html = "\n".join(_render_section(section, output_path, document.template) for section in document.sections)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(document.title)}</title>
  <style>{THEMES.get(document.theme, THEMES["noaa"])}</style>
</head>
<body class="theme-{html.escape(document.theme)}">
  <main class="page template-{html.escape(document.template)}">
    <header class="masthead">
      {logo_html}
      <div class="template-badge">{html.escape(document.template)} template</div>
      <h1 class="title">{html.escape(document.title)}</h1>
      <p class="subtitle">{html.escape(document.subtitle)}</p>
    </header>
    <section class="section-grid">
      {sections_html}
    </section>
    <footer class="footer">{html.escape(document.footer)}</footer>
  </main>
</body>
</html>
"""
def _render_section(section: CardSection, output_path: Optional[str], template: str = "standard") -> str:
    blocks = "\n".join(_render_block(block, output_path, template) for block in section.blocks)
    color_attr = f' style="--section-color: {html.escape(section.color)}"' if section.color else ""
    return f"""
<article class="card-section"{color_attr}>
  <h2>{html.escape(section.title)}</h2>
  {blocks}
</article>
"""


def _render_block(block: object, output_path: Optional[str], template: str = "standard") -> str:
    if isinstance(block, TextBlock):
        return _render_text_block(block)
    if isinstance(block, MetricTableBlock):
        return _render_metric_table(block, template)
    if isinstance(block, ImageBlock):
        return _render_image_block(block, output_path)
    if isinstance(block, KeyValueListBlock):
        return _render_key_value_list(block)
    if isinstance(block, BulletListBlock):
        return _render_bullet_list(block)
    raise TypeError(f"Unsupported block type: {type(block)!r}")


def _render_text_block(block: TextBlock) -> str:
    if block.format == "markdown":
        content = markdown.markdown(_normalize_fenced_code(block.text), extensions=["extra", "sane_lists"])
    else:
        content = f"<p>{html.escape(block.text)}</p>"
    return f'<div class="text-block">{content}</div>'


def _normalize_fenced_code(text: str) -> str:
    """Dedent fenced-code fence markers so python-markdown's fenced_code extension sees them.

    python-markdown requires fence markers (``` or ~~~) to start at column 0.
    Markdown source from HuggingFace often has them indented inside numbered lists.
    """
    import re
    return re.sub(r"^[ \t]+(```|~~~)", r"\1", text, flags=re.MULTILINE)


def _render_metric_table(block: MetricTableBlock, template: str = "standard") -> str:
    if not block.metrics:
        return "<p>No metrics were found in the source model card.</p>"

    if template == "graphical":
        # Render as individual metric cards in a grid
        cards = "\n".join(
            f"""
        <div class="metric-card">
          <div class="metric-value">{metric.value:.3f}</div>
          <div class="metric-name">{html.escape(metric.name)}</div>
          <div class="metric-meaning">{html.escape(metric.meaning)}</div>
        </div>
        """
            for metric in block.metrics
        )
        return f'<div class="metric-cards">\n{cards}\n</div>'
    else:
        # Standard table rendering
        rows = "\n".join(
            f"""
        <tr>
          <td>{html.escape(metric.name)}</td>
          <td class="metric-value">{metric.value:.3f}</td>
          <td>{html.escape(metric.meaning)}</td>
        </tr>
        """
            for metric in block.metrics
        )
        return f"""
<table class="metric-table">
  <thead>
    <tr>
      <th>Metric</th>
      <th>Value</th>
      <th>Meaning</th>
    </tr>
  </thead>
  <tbody>
    {rows}
  </tbody>
</table>
"""


def _render_image_block(block: ImageBlock, output_path: Optional[str]) -> str:
    asset_url = _asset_url(block.path, output_path)
    if not asset_url:
        return ""

    caption_html = f"<figcaption>{html.escape(block.caption)}</figcaption>" if block.caption else ""
    return f"""
<figure class="image-block">
  <img src="{asset_url}" alt="{html.escape(block.alt_text)}">
  {caption_html}
</figure>
"""


def _render_key_value_list(block: KeyValueListBlock) -> str:
    items = "\n".join(
        f"<li><strong>{html.escape(label)}:</strong> {html.escape(value)}</li>"
        for label, value in block.items
    )
    return f"""
<section>
  <h3 class="block-title">{html.escape(block.title)}</h3>
  <ul class="key-value-list">
    {items}
  </ul>
</section>
"""


def _render_bullet_list(block: BulletListBlock) -> str:
    items = "\n".join(f"<li>{html.escape(item)}</li>" for item in block.items)
    return f"""
<section>
  <h3 class="block-title">{html.escape(block.title)}</h3>
  <ul class="bullet-list">
    {items}
  </ul>
</section>
"""


def _asset_url(path: Optional[str], output_path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    if path.startswith("http://") or path.startswith("https://"):
        return html.escape(path, quote=True)

    normalized = _normalize_local_path(path)
    inline_asset = _inline_local_asset(normalized, output_path)
    if inline_asset:
        return inline_asset

    if output_path and os.path.isabs(normalized):
        output_dir = os.path.dirname(os.path.abspath(output_path))
        normalized = os.path.relpath(normalized, output_dir)
    return html.escape(normalized.replace("\\", "/"), quote=True)


def _inline_local_asset(path: str, output_path: Optional[str]) -> Optional[str]:
    asset_path = path
    if not os.path.isabs(asset_path):
        # Prefer resolving relative to CWD (project root) so assets committed
        # alongside the repository are found regardless of the output location.
        cwd_candidate = os.path.join(os.getcwd(), asset_path)
        if os.path.exists(cwd_candidate):
            asset_path = cwd_candidate
        elif output_path:
            asset_path = os.path.join(os.path.dirname(os.path.abspath(output_path)), asset_path)
        else:
            asset_path = cwd_candidate

    if not os.path.exists(asset_path):
        return None

    mime_type, _ = mimetypes.guess_type(asset_path)
    if not mime_type or not mime_type.startswith("image/"):
        return None

    with open(asset_path, "rb") as asset_file:
        encoded = base64.b64encode(asset_file.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _normalize_local_path(path: str) -> str:
    normalized = path.replace("\\", os.sep).replace("/", os.sep)
    return os.path.normpath(normalized)
