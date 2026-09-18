import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically add 'Page X of Y' and header/footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * inch - 36, "SIH 2026 — Day 1 Task 1: Sovereign AI Workbench (PS 26117)")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Footer (all pages)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 54, 36, page_str)
        self.drawString(54, 36, "Confidential — Mangalore Refinery and Petrochemicals Limited (MRPL)")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 8.5 * inch - 54, 48)

        self.restoreState()


def clean_markdown_inline(text):
    """Converts basic markdown inline styling to ReportLab XML tags."""
    if not text:
        return ""
    # Replace markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'<b>\1</b>', text)
    # Replace bold **text** or __text__ -> <b>text</b>
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__([^_]+)__', r'<b>\1</b>', text)
    # Replace italic *text* or _text_ -> <i>text</i>
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    # Replace inline code `code` -> <font name="Courier" color="#0f766e">code</font>
    text = re.sub(r'`([^`]+)`', r'<font name="Courier" size="8.5" color="#0f766e"><b>\1</b></font>', text)
    # Clean up html br tags if any
    text = text.replace('<br/>', ' ').replace('<br>', ' ')
    # Escape standalone & if not already XML entity
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|#\d+;)', '&amp;', text)
    return text.strip()


def render_mermaid_as_table(mermaid_text, styles):
    """Converts mermaid flowchart / sequence syntax into a visually attractive ReportLab Table card."""
    lines = mermaid_text.strip().splitlines()
    diag_type = lines[0].strip() if lines else "Diagram"

    parsed_steps = []
    
    for line in lines[1:]:
        line_s = line.strip()
        if not line_s or line_s.startswith('%%') or line_s.startswith('subgraph') or line_s.startswith('end'):
            continue
        
        # Sequence diagram parser
        if '->>' in line_s or '-->>' in line_s:
            parts = re.split(r'->>|-->>', line_s)
            sender = parts[0].strip()
            rest = parts[1].split(':', 1)
            receiver = rest[0].strip()
            msg = rest[1].strip() if len(rest) > 1 else ""
            parsed_steps.append((f"{sender} ➔ {receiver}", msg))
        # Flowchart parser
        elif '-->' in line_s:
            parts = line_s.split('-->')
            from_node = clean_node_label(parts[0])
            to_node = clean_node_label(parts[1])
            parsed_steps.append((from_node, f"➔ {to_node}"))
        elif '[' in line_s and ']' in line_s:
            label = clean_node_label(line_s)
            if label:
                parsed_steps.append(("Component / Module", label))

    if not parsed_steps:
        # Fallback to displaying code block if non-parseable
        code_text = mermaid_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return Paragraph(f"<font name='Courier' size='8' color='#1e293b'>{code_text.replace('\n', '<br/>')}</font>", styles['CodeBlock'])

    # Build Visual Diagram Card Table
    table_data = [[
        Paragraph(f"<b>📊 Visual Diagram Flow: {diag_type.upper()}</b>", styles['DiagramHeader']),
        Paragraph("", styles['DiagramHeader'])
    ]]
    
    for idx, (col1, col2) in enumerate(parsed_steps[:15]): # Cap steps for space
        step_num = f"<font color='#0284c7'><b>Step {idx+1}</b></font>"
        p1 = Paragraph(f"<b>{clean_markdown_inline(col1)}</b>", styles['TableCell'])
        p2 = Paragraph(f"{clean_markdown_inline(col2)}", styles['TableCell'])
        table_data.append([p1, p2])

    t = Table(table_data, colWidths=[2.5 * inch, 4.5 * inch])
    t.setStyle(TableStyle([
        ('SPAN', (0,0), (1,0)),
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (1,0), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f8fafc'), colors.white]),
    ]))
    return t


def clean_node_label(raw):
    """Strips mermaid node id tags like A[Label] -> Label."""
    m = re.search(r'\[["\']?([^"\'\]]+)["\']?\]', raw)
    if m:
        return m.group(1)
    m2 = re.search(r'\((["\']?[^"\'\)]+["\']?)\)', raw)
    if m2:
        return m2.group(1)
    # Remove graph attributes
    raw = re.sub(r'classDef|style|fill:|stroke:', '', raw)
    return raw.strip('; ').strip()


def parse_markdown_to_flowables(md_content, styles):
    flowables = []
    lines = md_content.splitlines()
    in_code_block = False
    is_mermaid = False
    code_block_lines = []
    in_table = False
    table_lines = []

    def flush_table(t_lines):
        if not t_lines:
            return None
        rows = []
        for line in t_lines:
            if re.match(r'^\s*\|?\s*:?-+:?\s*\|', line):
                continue
            cells = [c.strip() for c in line.strip('|').split('|')]
            rows.append(cells)
        
        if not rows:
            return None

        table_data = []
        num_cols = max(len(r) for r in rows)
        for r_idx, row in enumerate(rows):
            formatted_row = []
            for c_idx in range(num_cols):
                cell_text = row[c_idx] if c_idx < len(row) else ""
                style = styles['TableHeader'] if r_idx == 0 else styles['TableCell']
                formatted_row.append(Paragraph(clean_markdown_inline(cell_text), style))
            table_data.append(formatted_row)

        col_width = (7.0 * inch) / num_cols
        t = Table(table_data, colWidths=[col_width]*num_cols)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        return t

    i = 0
    while i < len(lines):
        line = lines[i]

        # Code block / Mermaid block handler
        if line.strip().startswith('```'):
            if in_code_block:
                code_text = "\n".join(code_block_lines)
                if is_mermaid:
                    diag_flowable = render_mermaid_as_table(code_text, styles)
                    flowables.append(diag_flowable)
                else:
                    code_text_esc = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    p_code = Paragraph(f"<font name='Courier' size='8' color='#1e293b'>{code_text_esc.replace('\n', '<br/>')}</font>", styles['CodeBlock'])
                    flowables.append(p_code)
                flowables.append(Spacer(1, 8))
                code_block_lines = []
                in_code_block = False
                is_mermaid = False
            else:
                if in_table:
                    t_flowable = flush_table(table_lines)
                    if t_flowable:
                        flowables.append(t_flowable)
                        flowables.append(Spacer(1, 10))
                    table_lines = []
                    in_table = False
                in_code_block = True
                is_mermaid = 'mermaid' in line.lower()
            i += 1
            continue

        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        # Table handler
        if line.strip().startswith('|'):
            in_table = True
            table_lines.append(line)
            i += 1
            continue
        elif in_table:
            t_flowable = flush_table(table_lines)
            if t_flowable:
                flowables.append(t_flowable)
                flowables.append(Spacer(1, 10))
            table_lines = []
            in_table = False

        if not line.strip():
            i += 1
            continue

        # Horizontal Rule
        if re.match(r'^\s*---+\s*$', line) or re.match(r'^\s*\*\*\*+\s*$', line):
            flowables.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0'), spaceAfter=8, spaceBefore=8))
            i += 1
            continue

        # Blockquote
        if line.strip().startswith('>'):
            quote_text = line.strip().lstrip('>').strip()
            while i + 1 < len(lines) and lines[i+1].strip().startswith('>'):
                i += 1
                quote_text += " " + lines[i].strip().lstrip('>').strip()
            flowables.append(Paragraph(clean_markdown_inline(quote_text), styles['Blockquote']))
            flowables.append(Spacer(1, 6))
            i += 1
            continue

        # Headings
        if line.startswith('# '):
            flowables.append(Paragraph(clean_markdown_inline(line[2:]), styles['Heading1_Custom']))
            flowables.append(Spacer(1, 8))
        elif line.startswith('## '):
            flowables.append(Paragraph(clean_markdown_inline(line[3:]), styles['Heading2_Custom']))
            flowables.append(Spacer(1, 6))
        elif line.startswith('### '):
            flowables.append(Paragraph(clean_markdown_inline(line[4:]), styles['Heading3_Custom']))
            flowables.append(Spacer(1, 4))
        elif line.startswith('#### '):
            flowables.append(Paragraph(clean_markdown_inline(line[5:]), styles['Heading4_Custom']))
            flowables.append(Spacer(1, 4))

        # Bullet List Items
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            item_text = line.strip()[2:]
            flowables.append(Paragraph(f"• {clean_markdown_inline(item_text)}", styles['BulletItem']))
            flowables.append(Spacer(1, 3))

        # Numbered List Items
        elif re.match(r'^\s*\d+\.\s+', line):
            m = re.match(r'^\s*(\d+\.)\s+(.*)', line)
            num_str, item_text = m.group(1), m.group(2)
            flowables.append(Paragraph(f"<b>{num_str}</b> {clean_markdown_inline(item_text)}", styles['NumberedItem']))
            flowables.append(Spacer(1, 3))

        # Standard Paragraph
        else:
            flowables.append(Paragraph(clean_markdown_inline(line), styles['Normal_Custom']))
            flowables.append(Spacer(1, 5))

        i += 1

    if in_table:
        t_flowable = flush_table(table_lines)
        if t_flowable:
            flowables.append(t_flowable)
            flowables.append(Spacer(1, 10))

    return flowables


def build_pdf_from_md(md_file_path, pdf_file_path):
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    doc = SimpleDocTemplate(
        pdf_file_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    base_styles = getSampleStyleSheet()

    styles = {
        'Heading1_Custom': ParagraphStyle(
            'H1', parent=base_styles['Normal'],
            fontName='Helvetica-Bold', fontSize=17, leading=21,
            textColor=colors.HexColor('#0f172a'), spaceBefore=10, spaceAfter=6
        ),
        'Heading2_Custom': ParagraphStyle(
            'H2', parent=base_styles['Normal'],
            fontName='Helvetica-Bold', fontSize=12.5, leading=16,
            textColor=colors.HexColor('#0369a1'), spaceBefore=8, spaceAfter=5
        ),
        'Heading3_Custom': ParagraphStyle(
            'H3', parent=base_styles['Normal'],
            fontName='Helvetica-Bold', fontSize=10.5, leading=14,
            textColor=colors.HexColor('#334155'), spaceBefore=6, spaceAfter=4
        ),
        'Heading4_Custom': ParagraphStyle(
            'H4', parent=base_styles['Normal'],
            fontName='Helvetica-Bold', fontSize=9.5, leading=13,
            textColor=colors.HexColor('#475569'), spaceBefore=5, spaceAfter=3
        ),
        'Normal_Custom': ParagraphStyle(
            'Body', parent=base_styles['Normal'],
            fontName='Helvetica', fontSize=9, leading=13,
            textColor=colors.HexColor('#1e293b')
        ),
        'BulletItem': ParagraphStyle(
            'Bullet', parent=base_styles['Normal'],
            fontName='Helvetica', fontSize=8.5, leading=12.5,
            leftIndent=12, textColor=colors.HexColor('#1e293b')
        ),
        'NumberedItem': ParagraphStyle(
            'Numbered', parent=base_styles['Normal'],
            fontName='Helvetica', fontSize=8.5, leading=12.5,
            leftIndent=12, textColor=colors.HexColor('#1e293b')
        ),
        'Blockquote': ParagraphStyle(
            'Quote', parent=base_styles['Normal'],
            fontName='Helvetica-Oblique', fontSize=8.5, leading=12,
            textColor=colors.HexColor('#0284c7'), leftIndent=12,
            backColor=colors.HexColor('#f0f9ff'), borderPadding=5
        ),
        'CodeBlock': ParagraphStyle(
            'Code', parent=base_styles['Normal'],
            fontName='Courier', fontSize=7.5, leading=10,
            backColor=colors.HexColor('#f1f5f9'), borderPadding=5,
            leftIndent=8
        ),
        'TableHeader': ParagraphStyle(
            'TH', parent=base_styles['Normal'],
            fontName='Helvetica-Bold', fontSize=8, leading=11,
            textColor=colors.white
        ),
        'TableCell': ParagraphStyle(
            'TD', parent=base_styles['Normal'],
            fontName='Helvetica', fontSize=7.5, leading=10.5,
            textColor=colors.HexColor('#1e293b')
        ),
        'DiagramHeader': ParagraphStyle(
            'DH', parent=base_styles['Normal'],
            fontName='Helvetica-Bold', fontSize=8.5, leading=11,
            textColor=colors.white
        )
    }

    flowables = parse_markdown_to_flowables(md_content, styles)
    doc.build(flowables, canvasmaker=NumberedCanvas)
    print(f"Generated PDF: {pdf_file_path}")


def main():
    base_dir = r"d:\isha\sovereign-ai\day1_documentation"
    md_dir = os.path.join(base_dir, "md")
    pdf_dir = os.path.join(base_dir, "pdf")
    os.makedirs(pdf_dir, exist_ok=True)
    md_files = [f for f in os.listdir(md_dir) if f.endswith('.md')]
    
    print(f"Found {len(md_files)} markdown files in {md_dir}")
    for md_file in sorted(md_files):
        md_path = os.path.join(md_dir, md_file)
        pdf_name = md_file.replace('.md', '.pdf')
        pdf_path = os.path.join(pdf_dir, pdf_name)
        build_pdf_from_md(md_path, pdf_path)

if __name__ == '__main__':
    main()
