"""Convert each Day-1 .md file to a styled .docx with REAL rendered diagram images.

- Headings, tables, bullets, code blocks, blockquotes -> native Word elements.
- Every ```mermaid block -> a matplotlib-rendered PNG figure embedded in the docx,
  so diagrams are VISIBLE as true visuals (not code text).
- Plain ``` code blocks (dir tree, ASCII boxes) -> shaded monospaced blocks.

Usage:  python convert_md_to_docx.py
Output: one .docx per .md in the same folder.
"""
import os
import re
import textwrap
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Ellipse

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE_DIR = r"d:\isha\sovereign-ai\day1_documentation"
MD_DIR = os.path.join(BASE_DIR, "md")
DOCX_DIR = os.path.join(BASE_DIR, "docx")
os.makedirs(DOCX_DIR, exist_ok=True)
IMG_DIR = os.path.join(tempfile.gettempdir(), "docx_diagrams")
os.makedirs(IMG_DIR, exist_ok=True)

NAVY = "#0f172a"
BLUE = "#0369a1"
ACCENT = "#0284c7"
LIGHT_BG = "#f1f5f9"

# ---------------------------------------------------------------- helpers: docx styling
def set_cell_shading(cell, color_hex):
    tblCell = cell._tc
    props = tblCell.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex.replace("#", ""))
    props.append(shd)

def set_cell_margins(cell, top=40, left=100, bottom=40, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for m, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{m}")
        el.set(qn("w:w"), str(v))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tcPr.append(mar)

def add_horizontal_line(doc):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "CBD5E1")
    pbdr.append(bottom)
    pPr.append(pbdr)
    return p

def add_header_footer(doc):
    section = doc.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)
    header = section.header
    hp = header.paragraphs[0]
    hp.text = "SIH 2026 \u2014 Day 1 Task 1: Sovereign AI Workbench (PS 26117)"
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for r in hp.runs:
        r.font.size = Pt(8)
        r.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
        r.font.name = "Calibri"
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # "Confidential — MRPL      Page X"
    run1 = fp.add_run("Confidential \u2014 Mangalore Refinery and Petrochemicals Limited (MRPL)    ")
    run1.font.size = Pt(8)
    run1.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
    run1.font.name = "Calibri"
    # PAGE field
    fld1 = OxmlElement("w:fldChar"); fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = "PAGE"
    fld2 = OxmlElement("w:fldChar"); fld2.set(qn("w:fldCharType"), "end")
    r = fp.add_run(); r._r.append(fld1)
    r2 = fp.add_run(); r2._r.append(instr)
    r3 = fp.add_run(); r3._r.append(fld2)
    for rr in (r, r2, r3):
        rr.font.size = Pt(8)
        rr.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

def style_document(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10)
    normal.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    normal.paragraph_format.line_spacing = 1.12
    for name, size, color in [
        ("Heading 1", 17, (0x0F, 0x17, 0x2A)),
        ("Heading 2", 13, (0x03, 0x69, 0xA1)),
        ("Heading 3", 11, (0x33, 0x41, 0x55)),
    ]:
        st = doc.styles[name]
        st.font.name = "Calibri"
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor(*color)
        st.paragraph_format.space_before = Pt(10)
        st.paragraph_format.space_after = Pt(5)

def clean_inline(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text.strip()

def add_rich_paragraph(doc, text, bold_prefix=False):
    """Add paragraph honouring **bold** and `code` with runs."""
    p = doc.add_paragraph()
    # split by bold then code
    tokens = re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            r = p.add_run(tok[2:-2])
            r.bold = True
        elif tok.startswith("`") and tok.endswith("`"):
            r = p.add_run(tok[1:-1])
            r.font.name = "Consolas"
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(0x0F, 0x76, 0x6E)
            r.bold = True
        else:
            # strip links, leftover single-star italics markers
            t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", tok)
            r = p.add_run(t)
    # leftover single * emphasis -> italicize whole? keep simple
    return p

def add_styled_table(doc, rows):
    # drop markdown separator rows
    data = []
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells):
            continue
        data.append(cells)
    if not data:
        return
    ncols = max(len(r) for r in data)
    for r in data:
        while len(r) < ncols:
            r.append("")
    table = doc.add_table(rows=len(data), cols=ncols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            cell = table.cell(i, j)
            cell.text = ""
            pp = cell.paragraphs[0]
            # rich runs inside cell
            tokens = re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", val)
            for tok in tokens:
                if not tok:
                    continue
                if tok.startswith("**") and tok.endswith("**"):
                    rr = pp.add_run(tok[2:-2]); rr.bold = True
                elif tok.startswith("`") and tok.endswith("`"):
                    rr = pp.add_run(tok[1:-1])
                    rr.font.name = "Consolas"; rr.font.size = Pt(8)
                    rr.font.color.rgb = RGBColor(0x0F, 0x76, 0x6E); rr.bold = True
                else:
                    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", tok)
                    rr = pp.add_run(t)
                rr.font.size = Pt(8.5)
                if i == 0:
                    rr.bold = True
                    rr.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                else:
                    rr.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
            set_cell_margins(cell)
            if i == 0:
                set_cell_shading(cell, NAVY)
            elif i % 2 == 0:
                set_cell_shading(cell, "#F8FAFC")
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_code_block(doc, code_text):
    table = doc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    cell = table.cell(0, 0)
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(code_text)
    run.font.name = "Consolas"
    run.font.size = Pt(7.5)
    run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    set_cell_shading(cell, LIGHT_BG)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def add_blockquote(doc, text):
    table = doc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    cell = table.cell(0, 0)
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(clean_inline(text))
    run.italic = True
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(0x02, 0x84, 0xC7)
    set_cell_shading(cell, "#F0F9FF")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def add_diagram_image(doc, img_path, caption):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(img_path, width=Inches(6.1))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run(caption)
    r.italic = True
    r.font.size = Pt(8.5)
    r.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

# ---------------------------------------------------------------- matplotlib helpers
def _box(ax, x, y, w, h, text, face="#ffffff", edge="#0f172a", tcolor="#0f172a",
         fs=7.5, style="round,pad=0.02,rounding_size=0.06", lw=1.6, ls="-"):
    box = FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=style,
                         facecolor=face, edgecolor=edge, linewidth=lw, linestyle=ls)
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tcolor,
            weight="bold", wrap=True, linespacing=1.35)

def _diamond(ax, x, y, w, h, text, face="#fef9c3", edge="#a16207", fs=7):
    diamond = plt.Polygon([[x, y + h / 2], [x + w / 2, y], [x, y - h / 2], [x - w / 2, y]],
                          closed=True, facecolor=face, edgecolor=edge, linewidth=1.6)
    ax.add_patch(diamond)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color="#713f12", weight="bold")

def _stadium(ax, x, y, w, h, text, face="#0f172a", edge="#38bdf8", tcolor="white", fs=7.5):
    box = FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.28",
                         facecolor=face, edgecolor=edge, linewidth=1.8)
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tcolor, weight="bold")

def _arrow(ax, x1, y1, x2, y2, label="", fs=6.5, color="#334155", ls="-", rad=0.0):
    arr = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=12,
                          color=color, linewidth=1.4, linestyle=ls,
                          connectionstyle=f"arc3,rad={rad}", shrinkA=2, shrinkB=4)
    ax.add_patch(arr)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.06, my + 0.08, label, fontsize=fs, color=color,
                ha="center", va="center", style="italic",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#e2e8f0", alpha=0.95))

def _lane(ax, x0, y0, w, h, title, bg="#f8fafc", edge="#cbd5e1"):
    lane = FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0.01,rounding_size=0.12",
                          facecolor=bg, edgecolor=edge, linewidth=1.2)
    ax.add_patch(lane)
    ax.text(x0 + 0.12, y0 + h - 0.28, title, fontsize=8, weight="bold", color="#0f172a", va="top", ha="left")

def _save(fig, name, dpi=200):
    fig.tight_layout()
    path = os.path.join(IMG_DIR, name)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return path

# ---------------------------------------------------------------- 8 diagram renderers
def render_d05_architecture():
    fig, ax = plt.subplots(figsize=(11.5, 13.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 15.2)
    ax.axis("off")
    ax.set_title("Sovereign AI Workbench \u2014 4-Tier Modular Architecture (+ Storage Layer)",
                 fontsize=12, weight="bold", color="#0f172a", pad=14)
    ax.text(5, 14.55, "Single-node, air-gapped deployment  \u2022  UI \u2192 FastAPI Router \u2192 RAG Engine \u2192 Ollama Runtime \u2192 Local Disk",
            ha="center", fontsize=8, color="#475569", style="italic")
    lanes = [
        (1.1, 11.55, 8.6, 2.55, "TIER 1 \u2014 Presentation Layer (Browser UI)", "#f0f9ff", "#38bdf8"),
        (1.1, 8.75, 8.6, 2.35, "TIER 2 \u2014 Application Gateway & Router (FastAPI :8000)", "#eef2ff", "#818cf8"),
        (1.1, 5.55, 8.6, 2.75, "TIER 3 \u2014 Document Processing & Local RAG Vector Engine", "#faf5ff", "#c084fc"),
        (1.1, 2.75, 8.6, 2.35, "TIER 4 \u2014 Local Open-Weight Model Runtime (Ollama)", "#ecfdf5", "#34d399"),
        (1.1, 0.35, 8.6, 1.95, "TIER 5 \u2014 Storage Layer (Local Disk, Air-Gapped)", "#fff7ed", "#fb923c"),
    ]
    for l in lanes:
        _lane(ax, *l)
    # Tier 1 boxes
    _box(ax, 2.6, 12.55, 2.9, 0.85, "Dark-Themed SPA\nVanilla HTML/CSS/JS", face="#1e293b", edge="#38bdf8", tcolor="white", fs=7)
    _box(ax, 5.55, 12.55, 2.5, 0.85, "Knowledge Toggle\nON / OFF", face="#1e293b", edge="#38bdf8", tcolor="white", fs=7)
    _box(ax, 8.25, 12.55, 2.7, 0.85, "Multimodal Upload\nPDF, TXT, PNG, JPG", face="#1e293b", edge="#38bdf8", tcolor="white", fs=7)
    # Tier 2
    _box(ax, 3.7, 9.7, 3.4, 0.85, "FastAPI Server (main.py)\nPort 8000", face="#0f172a", edge="#818cf8", tcolor="white", fs=7)
    _diamond(ax, 7.3, 9.7, 3.0, 1.05, "Task Router\nEngine", fs=7.5)
    # Tier 3
    _box(ax, 2.3, 6.7, 2.3, 0.8, "PDF Parser\n(pypdf)", face="#1e1b4b", edge="#c084fc", tcolor="white", fs=6.5)
    _box(ax, 4.55, 6.7, 2.0, 0.8, "OCR Engine\nGLM-OCR", face="#1e1b4b", edge="#c084fc", tcolor="white", fs=6.5)
    _box(ax, 6.55, 6.7, 1.9, 0.8, "Chunker\n500 char", face="#1e1b4b", edge="#c084fc", tcolor="white", fs=6.5)
    _box(ax, 8.4, 6.7, 1.9, 0.8, "Embedder\nnomic-embed", face="#1e1b4b", edge="#c084fc", tcolor="white", fs=6.5)
    _box(ax, 5.4, 5.95, 4.6, 0.5, "In-Memory Cosine Similarity Search Engine", face="#1e1b4b", edge="#c084fc", tcolor="white", fs=6.5)
    # Tier 4
    _box(ax, 2.4, 3.7, 2.5, 0.8, "Ollama Service\nRuntime :11434", face="#064e3b", edge="#34d399", tcolor="white", fs=6.5)
    _box(ax, 4.7, 3.7, 1.95, 0.8, "qwen3.5:4b\nGeneral+RAG", face="#064e3b", edge="#34d399", tcolor="white", fs=6.5)
    _box(ax, 6.85, 3.7, 2.1, 0.8, "qwen2.5-coder:7b\nCoding", face="#064e3b", edge="#34d399", tcolor="white", fs=6.5)
    _box(ax, 8.85, 3.7, 1.7, 0.8, "glm-ocr:q8_0\nVision OCR", face="#064e3b", edge="#34d399", tcolor="white", fs=6.5)
    # Tier 5
    _box(ax, 3.75, 1.15, 4.2, 0.8, "data/knowledge_base/  (source docs & images)", face="#451a03", edge="#fb923c", tcolor="white", fs=7)
    _box(ax, 7.65, 1.15, 3.0, 0.8, "data/kb_index.json\n(vector index)", face="#451a03", edge="#fb923c", tcolor="white", fs=7)
    # Inter-tier flow arrows (right spine)
    _arrow(ax, 9.15, 11.5, 9.15, 11.15, "")
    ax.text(9.35, 11.32, "HTTP", fontsize=6, color="#0369a1", weight="bold")
    _arrow(ax, 7.3, 9.25, 5.4, 8.35, "")
    ax.text(6.9, 8.85, "route", fontsize=6, color="#4f46e5", style="italic")
    _arrow(ax, 5.4, 5.65, 5.4, 4.15, "")
    ax.text(5.6, 4.9, "vectors", fontsize=6, color="#7c3aed", style="italic")
    _arrow(ax, 3.75, 2.7, 3.75, 2.3, "")
    ax.text(3.95, 2.5, "persist", fontsize=6, color="#9a3412", style="italic")
    # return path (left spine, dashed green = answers) — runs outside the lanes
    _arrow(ax, 0.6, 2.7, 0.6, 12.4, "", color="#059669", ls="--")
    ax.text(0.32, 7.5, "grounded answers +\nsource citations", fontsize=6.5, color="#059669", weight="bold", rotation=90, va="center")
    return _save(fig, "d05_architecture.png")

def render_d06_userflow():
    fig, ax = plt.subplots(figsize=(11.5, 11.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(6.0, 16.6)
    ax.axis("off")
    ax.set_title("User Flow \u2014 Document Upload vs. Chat Query Pipelines", fontsize=12, weight="bold", color="#0f172a", pad=12)
    _stadium(ax, 5, 15.7, 3.6, 0.6, "User opens Workbench Web UI")
    _arrow(ax, 5, 15.4, 5, 14.95, "")
    _diamond(ax, 5, 14.35, 3.4, 1.1, "User Action?")
    ax.text(3.05, 14.35, "Upload File", fontsize=7, weight="bold", color="#0369a1", ha="right")
    ax.text(6.95, 14.35, "Enter Prompt", fontsize=7, weight="bold", color="#0369a1", ha="left")
    # ---- Upload branch (left) ----
    _diamond(ax, 1.9, 13.0, 3.0, 1.0, "File Format?")
    _arrow(ax, 3.9, 14.05, 2.6, 13.5, "")
    _box(ax, 0.85, 11.95, 1.6, 0.7, ".pdf/.txt/.md\npypdf read", face="#e0f2fe", edge="#0284c7", fs=6.5)
    _box(ax, 2.95, 11.95, 1.8, 0.7, ".png/.jpg/.webp\nGLM-OCR", face="#fef3c7", edge="#d97706", fs=6.5)
    _arrow(ax, 1.25, 12.55, 0.95, 12.3, "")
    _arrow(ax, 2.45, 12.55, 2.85, 12.3, "")
    _box(ax, 1.9, 11.05, 2.9, 0.55, "Chunk text \u2192 500-char snippets", face="white", edge="#0284c7", fs=7)
    _box(ax, 1.9, 10.42, 2.9, 0.55, "Embed via nomic-embed-text", face="white", edge="#0284c7", fs=7)
    _box(ax, 1.9, 9.79, 2.9, 0.55, "Append to kb_index.json", face="white", edge="#0284c7", fs=7)
    _stadium(ax, 1.9, 9.05, 3.1, 0.55, "UI: Chunks Indexed \u2713", face="#064e3b", edge="#34d399", fs=7)
    _arrow(ax, 1.9, 11.6, 1.9, 11.33, "")
    _arrow(ax, 1.9, 10.77, 1.9, 10.7, "")
    _arrow(ax, 1.9, 10.14, 1.9, 10.07, "")
    _arrow(ax, 1.9, 9.51, 1.9, 9.33, "")
    # ---- Chat branch (right) ----
    _arrow(ax, 6.1, 14.05, 7.0, 13.5, "")
    _diamond(ax, 7.6, 13.0, 3.2, 1.0, "Coding keywords?")
    _box(ax, 9.15, 12.1, 1.55, 0.65, "qwen2.5\n-coder:7b", face="#ede9fe", edge="#7c3aed", fs=6.5)
    _box(ax, 9.15, 11.35, 1.55, 0.6, "Show code", face="white", edge="#7c3aed", fs=6.5)
    ax.text(8.75, 12.62, "Yes", fontsize=7, weight="bold", color="#7c3aed")
    _arrow(ax, 8.55, 12.75, 9.0, 12.42, "")
    _arrow(ax, 9.15, 11.77, 9.15, 11.65, "")
    _diamond(ax, 6.6, 11.9, 2.9, 1.0, "Knowledge ON?")
    _arrow(ax, 6.75, 12.65, 6.65, 12.4, "No")
    _box(ax, 4.7, 12.35, 2.2, 0.65, "qwen3.5:4b\ngeneral answer", face="#f1f5f9", edge="#64748b", fs=6.5)
    _arrow(ax, 5.75, 12.35, 5.8, 12.35, "OFF")
    _box(ax, 7.6, 10.5, 3.2, 0.6, "Embed query (nomic-embed)", face="white", edge="#0284c7", fs=7)
    _box(ax, 7.6, 9.8, 3.2, 0.6, "Cosine search kb_index.json", face="white", edge="#0284c7", fs=7)
    _arrow(ax, 6.9, 11.4, 7.3, 10.8, "ON")
    _arrow(ax, 7.6, 10.2, 7.6, 10.1, "")
    _diamond(ax, 7.6, 8.95, 3.2, 1.0, "Relevant context?")
    _arrow(ax, 7.6, 9.5, 7.6, 9.45, "")
    _box(ax, 6.0, 7.85, 2.8, 0.7, "Grounded prompt\nTop-5 chunks", face="#e0f2fe", edge="#0284c7", fs=6.5)
    _box(ax, 6.0, 7.05, 2.8, 0.7, "qwen3.5:4b answer\n+ citations", face="#064e3b", edge="#34d399", tcolor="white", fs=6.5)
    _box(ax, 9.0, 7.85, 1.8, 0.7, "Guardrail:\nnot in KB", face="#fee2e2", edge="#dc2626", fs=6.5)
    _box(ax, 9.0, 7.05, 1.8, 0.7, "\"Information\nnot available\"", face="white", edge="#dc2626", fs=6.5)
    ax.text(6.85, 8.55, "Yes", fontsize=7, weight="bold", color="#059669")
    ax.text(8.5, 8.55, "No", fontsize=7, weight="bold", color="#dc2626")
    _arrow(ax, 6.95, 8.6, 6.35, 8.2, "")
    _arrow(ax, 8.3, 8.6, 8.8, 8.2, "")
    _arrow(ax, 6.0, 7.5, 6.0, 7.4, "")
    _arrow(ax, 9.0, 7.5, 9.0, 7.4, "")
    return _save(fig, "d06_userflow.png")

def _sequence_base(title, subtitle, participants, messages, notes=None, alt_range=None, alt_label="",
                   loop_range=None, loop_label=""):
    """Sequence diagram with tight lifelines.

    messages: list of (from_idx, to_idx, label, is_return).
    A message with from_idx == to_idx is rendered as a small self-action
    badge sitting ON that participant's lifeline (no cross-participant arrow).
    alt_range / loop_range: (first_msg_idx, last_msg_idx) wrapped by the box.
    """
    n = len(participants)
    step = 0.62
    h = 1.7 + len(messages) * step + (0.95 if notes else 0.45)
    h = max(h, 5.5)
    fig, ax = plt.subplots(figsize=(11.5, min(h, 14)))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, h + 1.1)
    ax.axis("off")
    ax.set_title(title, fontsize=11.5, weight="bold", color="#0f172a", pad=10)
    ax.text(5, h + 0.72, subtitle, ha="center", fontsize=8, color="#475569", style="italic")
    xs = [0.7 + i * (8.6 / max(n - 1, 1)) for i in range(n)]
    top = h
    for x, p in zip(xs, participants):
        _box(ax, x, top, 1.65, 0.55, p["label"], face=p.get("face", "white"), edge=p.get("edge", "#0f172a"),
             tcolor=p.get("tcolor", "#0f172a"), fs=6.5)
    y_of = [top - 0.85 - step * (k + 1) for k in range(len(messages))]
    life_bot = y_of[-1] - 0.55
    for x in xs:
        ax.plot([x, x], [top - 0.3, life_bot], color="#94a3b8", linewidth=1.1, linestyle="--", alpha=0.9)
    for idx, (fi, ti, label, is_return) in enumerate(messages):
        y = y_of[idx]
        col = "#64748b" if is_return else "#0369a1"
        if fi == ti:
            # self-action badge centred on the lifeline
            badge = FancyBboxPatch((xs[fi] - 1.0, y - 0.18), 2.0, 0.36,
                                   boxstyle="round,pad=0.005,rounding_size=0.1",
                                   facecolor="#eef2ff", edgecolor="#64748b", linewidth=1.1)
            ax.add_patch(badge)
            ax.text(xs[fi], y, f"{idx+1}. {label}", fontsize=6.3, color="#334155", ha="center", va="center",
                    style="italic")
        else:
            _arrow(ax, xs[fi], y, xs[ti], y, "", color=col, ls="--" if is_return else "-")
            mx = (xs[fi] + xs[ti]) / 2
            ax.text(mx, y + 0.17, f"{idx+1}. {label}", fontsize=6.3, color=col, ha="center", va="bottom",
                    style="italic" if is_return else "normal",
                    bbox=dict(boxstyle="round,pad=0.2", fc="#f8fafc", ec="#e2e8f0", alpha=0.97))
    def _span(idxs):
        involved = set()
        for k in idxs:
            involved.add(messages[k][0])
            involved.add(messages[k][1])
        x0 = min(xs[k] for k in involved) - 0.75
        x1 = max(xs[k] for k in involved) + 0.75
        return x0, x1
    if loop_range:
        l0, l1 = loop_range
        y_top_p = y_of[l0] + 0.42
        y_bot_p = y_of[l1] - 0.32
        x0, x1 = _span(range(l0, l1 + 1))
        rect = FancyBboxPatch((x0, y_bot_p), x1 - x0, y_top_p - y_bot_p,
                              boxstyle="round,pad=0.02,rounding_size=0.1",
                              facecolor="#fffbeb", edgecolor="#d97706", linewidth=1.2, linestyle="--", alpha=0.5)
        ax.add_patch(rect)
        ax.text(x0 + 0.08, y_top_p - 0.14, loop_label, fontsize=6.5, weight="bold", color="#92400e")
    if alt_range:
        a0, a1 = alt_range
        y_top_p = y_of[a0] + 0.42
        y_bot_p = y_of[a1] - 0.32
        x0, x1 = _span(range(a0, a1 + 1))
        arect = FancyBboxPatch((x0, y_bot_p), x1 - x0, y_top_p - y_bot_p,
                               boxstyle="round,pad=0.02,rounding_size=0.1",
                               facecolor="#f0fdf4", edgecolor="#16a34a", linewidth=1.2, linestyle="--", alpha=0.5)
        ax.add_patch(arect)
        ax.text(x0 + 0.08, y_top_p - 0.14, alt_label, fontsize=6.5, weight="bold", color="#166534")
    if notes:
        ax.text(5, life_bot - 0.35, notes, ha="center", fontsize=6.8, color="#475569", style="italic",
                bbox=dict(boxstyle="round,pad=0.3", fc="#f8fafc", ec="#e2e8f0"))
    return fig

def render_d06_seq1():
    parts = [
        {"label": "Plant\nEngineer", "face": "#f0f9ff", "edge": "#0284c7"},
        {"label": "Web UI\nindex.html", "face": "#1e293b", "edge": "#38bdf8", "tcolor": "white"},
        {"label": "FastAPI\n/upload", "face": "#0f172a", "edge": "#818cf8", "tcolor": "white"},
        {"label": "Ollama\nglm-ocr:q8_0", "face": "#064e3b", "edge": "#34d399", "tcolor": "white"},
        {"label": "Ollama\nnomic-embed", "face": "#1e1b4b", "edge": "#c084fc", "tcolor": "white"},
        {"label": "Vector Index\nkb_index.json", "face": "#451a03", "edge": "#fb923c", "tcolor": "white"},
    ]
    msgs = [
        (0, 1, "Selects & uploads inspection_sheet.png", False),
        (1, 2, "POST /upload (file payload)", False),
        (2, 2, "Detect image extension (.png)", False),
        (2, 3, "Send image for text extraction", False),
        (3, 2, "Return extracted OCR text", True),
        (2, 2, "Split text into semantic chunks", False),
        (2, 4, "Generate 768-dim embedding", False),
        (4, 2, "Return vector array", True),
        (2, 5, "Append chunk + vector + filename", False),
        (5, 2, "Save updated index", True),
        (2, 1, "JSON success {file, chunk count}", True),
        (1, 0, '"inspection_sheet.png processed (3 chunks)"', True),
    ]
    fig = _sequence_base("Sequence 1 \u2014 Image Upload & GLM-OCR Ingestion Pipeline",
                         "Plant Engineer \u2192 Web UI \u2192 FastAPI \u2192 GLM-OCR \u2192 Embeddings \u2192 kb_index.json",
                         parts, msgs, loop_range=(6, 7), loop_label="loop \u00b7 for each chunk",
                         notes="Result: scanned report becomes searchable alongside PDFs in one unified index.")
    return _save(fig, "d06_seq1.png")

def render_d06_seq2():
    parts = [
        {"label": "Safety\nOfficer", "face": "#f0f9ff", "edge": "#0284c7"},
        {"label": "Web UI\nindex.html", "face": "#1e293b", "edge": "#38bdf8", "tcolor": "white"},
        {"label": "FastAPI\n/chat", "face": "#0f172a", "edge": "#818cf8", "tcolor": "white"},
        {"label": "Ollama\nnomic-embed", "face": "#1e1b4b", "edge": "#c084fc", "tcolor": "white"},
        {"label": "KB Index\nkb_index.json", "face": "#451a03", "edge": "#fb923c", "tcolor": "white"},
        {"label": "Ollama\nqwen3.5:4b", "face": "#064e3b", "edge": "#34d399", "tcolor": "white"},
    ]
    msgs = [
        (0, 1, '"What to check during pump inspection?" (KB ON)', False),
        (1, 2, "POST /chat {message, knowledge: true}", False),
        (2, 3, "Embed user query string", False),
        (3, 2, "Return query vector", True),
        (2, 4, "Cosine similarity over stored vectors", False),
        (4, 2, "Top-5 chunks (test_sop.txt, 0.9421)", True),
        (2, 5, "Grounded prompt + Top-5 context + query", False),
        (5, 2, "Factual answer (strictly from context)", True),
        (2, 1, "{answer, sources:[{file, score}]}", True),
        (1, 0, "Grounded answer + source pill badges", True),
    ]
    fig = _sequence_base("Sequence 2 \u2014 Grounded RAG Query (Knowledge ON)",
                         "alt branch: high similarity \u2192 grounded answer  |  low similarity \u2192 anti-hallucination fallback",
                         parts, msgs, alt_range=(6, 9),
                         alt_label="alt \u00b7 High match: grounded answer  /  else \u201cnot available in KB\u201d",
                         notes='Low/zero similarity \u2192 { answer: "That information is not available in the knowledge base.", sources: [] }.')
    return _save(fig, "d06_seq2.png")

def render_d06_seq3():
    parts = [
        {"label": "Automation\nEngineer", "face": "#f0f9ff", "edge": "#0284c7"},
        {"label": "Web UI\nindex.html", "face": "#1e293b", "edge": "#38bdf8", "tcolor": "white"},
        {"label": "FastAPI\n/chat", "face": "#0f172a", "edge": "#818cf8", "tcolor": "white"},
        {"label": "Model Router\nEngine", "face": "#fef9c3", "edge": "#a16207"},
        {"label": "Ollama\nqwen2.5-coder:7b", "face": "#ede9fe", "edge": "#7c3aed", "tcolor": "#4c1d95"},
    ]
    msgs = [
        (0, 1, '"Write python fn to parse sensor logs"', False),
        (1, 2, "POST /chat {message, knowledge: false}", False),
        (2, 3, 'Analyze keywords ("python","function","parse")', False),
        (3, 2, "Keyword match \u2192 route: CODING", True),
        (2, 4, "Send prompt to qwen2.5-coder:7b", False),
        (4, 2, "Return synthesized Python snippet", True),
        (2, 1, '{route:"coding", model, answer}', True),
        (1, 0, "Syntax-highlighted code block", True),
    ]
    fig = _sequence_base("Sequence 3 \u2014 Code Generation Task Routing",
                         "Keyword router dispatches coding prompts to the specialist qwen2.5-coder:7b model",
                         parts, msgs,
                         notes="General / grounded queries stay on qwen3.5:4b \u2014 only code intent hits the coder model.")
    return _save(fig, "d06_seq3.png")

def render_d07_l0():
    fig, ax = plt.subplots(figsize=(11.5, 6.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(1.4, 7.4)
    ax.axis("off")
    ax.set_title("DFD Level 0 \u2014 Context Diagram (System Boundary)", fontsize=12, weight="bold", color="#0f172a", pad=12)
    ax.text(5, 6.75, "External entities: Plant User  \u2022  Local Disk Storage  \u2022  Local Ollama Runtime",
            ha="center", fontsize=8, color="#475569", style="italic")
    _box(ax, 1.5, 3.8, 2.2, 1.0, "Plant Engineer\n/ User", face="#f0f9ff", edge="#0284c7", fs=8)
    circ = Circle((5, 3.8), 1.35, facecolor="#0f172a", edgecolor="#38bdf8", linewidth=2)
    ax.add_patch(circ)
    ax.text(5, 3.8, "0.0\nSovereign AI\nWorkbench\nSystem", ha="center", va="center", fontsize=8.5, weight="bold", color="white")
    _box(ax, 8.5, 5.2, 2.3, 0.95, "Local Disk Storage\ndata/", face="#451a03", edge="#fb923c", tcolor="white", fs=8)
    _box(ax, 8.5, 2.3, 2.3, 0.95, "Local Ollama\nModel Runtime", face="#064e3b", edge="#34d399", tcolor="white", fs=8)
    _arrow(ax, 2.6, 4.3, 3.75, 4.2, "Files: PDF,PNG,TXT", fs=6.5)
    _arrow(ax, 2.6, 3.5, 3.75, 3.6, "Queries+settings", fs=6.5)
    _arrow(ax, 3.75, 3.2, 2.6, 3.0, "Answers + code", fs=6.5, color="#059669")
    _arrow(ax, 3.9, 2.9, 2.6, 2.65, "Citations+scores", fs=6.5, color="#059669")
    _arrow(ax, 6.3, 4.3, 7.35, 5.0, "Store files+index", fs=6.5, color="#9a3412")
    _arrow(ax, 7.35, 4.7, 6.3, 3.9, "Load vectors", fs=6.5, color="#9a3412")
    _arrow(ax, 6.3, 3.3, 7.35, 2.6, "Prompt+images", fs=6.5, color="#047857")
    _arrow(ax, 7.35, 2.25, 6.3, 3.0, "OCR+vectors+answers", fs=6.5, color="#047857")
    return _save(fig, "d07_l0.png")

def render_d07_l1():
    fig, ax = plt.subplots(figsize=(11.5, 9.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(3.2, 11.4)
    ax.axis("off")
    ax.set_title("DFD Level 1 \u2014 System Process Overview", fontsize=12, weight="bold", color="#0f172a", pad=12)
    _box(ax, 1.5, 10.4, 2.2, 0.7, "Plant User", face="#f0f9ff", edge="#0284c7", fs=8)
    # processes as rounded boxes (left-centre column)
    _box(ax, 3.0, 8.9, 2.9, 0.85, "1.0  Multimodal Ingestion\n& Parsing", face="#0f172a", edge="#818cf8", tcolor="white", fs=7)
    _box(ax, 3.0, 7.5, 2.9, 0.85, "2.0  Chunking & Embedding\nVector Store", face="#0f172a", edge="#818cf8", tcolor="white", fs=7)
    _box(ax, 3.0, 6.1, 2.9, 0.85, "3.0  Task Routing &\nCosine Retrieval", face="#0f172a", edge="#818cf8", tcolor="white", fs=7)
    _box(ax, 3.0, 4.7, 2.9, 0.85, "4.0  Local Model\nInference", face="#0f172a", edge="#818cf8", tcolor="white", fs=7)
    # data stores (right column)
    _box(ax, 7.6, 8.9, 3.4, 0.85, "D1: Knowledge Base Files\ndata/knowledge_base/", face="white", edge="#fb923c", fs=7)
    _box(ax, 7.6, 7.5, 3.4, 0.85, "D2: Vector Index Store\ndata/kb_index.json", face="white", edge="#fb923c", fs=7)
    # runtime (bottom-right)
    _box(ax, 7.6, 4.7, 3.4, 0.95, "Local Ollama Models\nOCR \u2022 Embed \u2022 LLM", face="#064e3b", edge="#34d399", tcolor="white", fs=7.5)

    def _tag(x, y, text, color="#334155"):
        ax.text(x, y, text, fontsize=6.5, color=color, ha="center", va="center", style="italic",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#e2e8f0", alpha=0.97))

    # flows
    _arrow(ax, 1.9, 10.05, 2.4, 9.32, "Upload PDF/image")
    _arrow(ax, 4.45, 8.9, 5.9, 8.9, "Save raw file", color="#9a3412")
    _arrow(ax, 4.0, 8.55, 6.2, 5.15, "", color="#047857", rad=0.2)
    _arrow(ax, 6.6, 5.0, 4.3, 8.45, "", color="#047857", rad=0.2)
    _arrow(ax, 3.0, 8.45, 3.0, 7.95, "Clean text")
    _arrow(ax, 4.45, 7.5, 5.9, 7.5, "Save chunks+vectors", color="#9a3412")
    _arrow(ax, 4.1, 7.05, 6.1, 5.1, "", rad=-0.15)
    _arrow(ax, 6.6, 4.85, 4.4, 6.9, "", rad=-0.15)
    _arrow(ax, 1.15, 10.05, 1.9, 6.35, "", rad=0.25)
    _arrow(ax, 1.35, 10.0, 2.0, 4.95, "", rad=-0.22)
    _arrow(ax, 5.9, 7.05, 4.45, 5.9, "", color="#9a3412")
    _arrow(ax, 3.0, 5.65, 3.0, 5.15, "Top-5 context")
    _arrow(ax, 4.45, 4.7, 5.9, 4.7, "Prompt payload")
    _arrow(ax, 5.9, 4.45, 4.45, 4.45, "LLM answer")
    _arrow(ax, 1.7, 5.15, 1.0, 10.0, "Response+citations", color="#059669", rad=-0.25)
    # hand-staggered labels (auto mid-point labels would pile up in the middle band)
    _tag(0.45, 8.75, "User prompt")
    _tag(0.45, 7.9, "Settings")
    _tag(4.62, 7.55, "Image payload", "#047857")
    _tag(5.95, 7.2, "OCR text", "#047857")
    _tag(4.5, 6.62, "Read vectors", "#9a3412")
    _tag(5.85, 6.28, "Text snippets")
    _tag(4.62, 5.68, "Dense vectors")
    return _save(fig, "d07_l1.png")

def render_d07_l2():
    fig, ax = plt.subplots(figsize=(11.5, 8.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(1.0, 9.2)
    ax.axis("off")
    ax.set_title("DFD Level 2 \u2014 Process 1.0: Multimodal Ingestion Pipeline", fontsize=12, weight="bold", color="#0f172a", pad=12)
    _stadium(ax, 5, 8.3, 3.0, 0.6, "Raw Upload File")
    _arrow(ax, 5, 8.0, 5, 7.55, "")
    _diamond(ax, 5, 6.95, 3.2, 1.0, "Format Classifier")
    _box(ax, 1.8, 5.6, 2.6, 0.85, "1.1 PDF Parser\n(pypdf Reader)", face="#e0f2fe", edge="#0284c7", fs=7)
    _box(ax, 5.0, 5.6, 2.6, 0.85, "1.2 OCR Dispatcher\n(GLM-OCR)", face="#fef3c7", edge="#d97706", fs=7)
    _box(ax, 8.2, 5.6, 2.6, 0.85, "1.3 Text Reader\n(Direct UTF-8)", face="#f1f5f9", edge="#64748b", fs=7)
    _arrow(ax, 4.2, 6.6, 2.4, 6.05, ".pdf", fs=7)
    _arrow(ax, 5.0, 6.45, 5.0, 6.05, ".png/.jpg", fs=7)
    _arrow(ax, 5.8, 6.6, 7.6, 6.05, ".txt/.md", fs=7)
    _box(ax, 5, 4.35, 4.4, 0.8, "1.4 Text Normalizer (strip fences)", face="white", edge="#0f172a", fs=7.5)
    _arrow(ax, 1.8, 5.15, 3.6, 4.6, "text", fs=6.5)
    _arrow(ax, 5.0, 5.15, 5.0, 4.75, "text", fs=6.5)
    _arrow(ax, 8.2, 5.15, 6.4, 4.6, "raw", fs=6.5)
    _box(ax, 5, 3.3, 4.6, 0.8, "1.5 Semantic Chunker (500 / overlap 50)", face="#ede9fe", edge="#7c3aed", fs=7.5)
    _arrow(ax, 5, 3.95, 5, 3.7, "")
    _stadium(ax, 5, 2.2, 5.2, 0.7, "Clean Chunk Array \u2192 Process 2.0", face="#064e3b", edge="#34d399", fs=8)
    _arrow(ax, 5, 2.9, 5, 2.55, "")
    ax.text(5, 1.75, "Every path converges on normalized text before chunking \u2014 no fragmented silos.",
            ha="center", fontsize=7.5, color="#475569", style="italic")
    return _save(fig, "d07_l2.png")

def render_generic_fallback(mermaid_text, tag):
    """Generic visible fallback:first line as title + up to 12 steps as numbered lane."""
    lines = [l.strip() for l in mermaid_text.strip().splitlines() if l.strip() and not l.strip().startswith("%%")]
    title = (lines[0] if lines else "Diagram")[:90]
    steps = [l for l in lines[1:] if not l.startswith("classDef") and not l.startswith("class ")][:12]
    fig, ax = plt.subplots(figsize=(11, 3 + len(steps) * 0.65))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3 + len(steps) * 0.65)
    ax.axis("off")
    ax.set_title(f"Diagram \u2014 {title}", fontsize=11, weight="bold", color="#0f172a", pad=12)
    y = 2 + len(steps) * 0.65
    ax.text(5, y, "Auto-rendered step view (source: Mermaid block)", ha="center", fontsize=8, color="#475569", style="italic")
    for i, s in enumerate(steps):
        yy = y - 0.8 - i * 0.65
        _box(ax, 5, yy, 9.0, 0.5, f"Step {i+1}: {s[:120]}", face="#f8fafc", edge="#0284c7", fs=6.5)
        if i:
            _arrow(ax, 5, yy + 0.55, 5, yy + 0.28, "")
    return _save(fig, f"fallback_{tag}.png")

def render_mermaid_to_image(mermaid_text, fig_tag, hint=""):
    t = mermaid_text
    try:
        if "Tier1" in t or "Presentation Layer" in t:
            return render_d05_architecture(), "Figure \u2014 System Architecture: 4-tier air-gapped design (UI \u2192 FastAPI \u2192 RAG engine \u2192 Ollama \u2192 disk)"
        if "ActionChoice" in t:
            return render_d06_userflow(), "Figure \u2014 User flow: upload pipeline (left) vs chat query pipeline (right)"
        if "inspection_sheet" in t:
            return render_d06_seq1(), "Figure \u2014 Sequence: image upload & GLM-OCR ingestion pipeline"
        if "Knowledge ON" in t and "test_sop" in t:
            return render_d06_seq2(), "Figure \u2014 Sequence: grounded RAG query execution (Knowledge ON)"
        if "qwen2.5-coder" in t and ("Router" in t or "CODING" in t):
            return render_d06_seq3(), "Figure \u2014 Sequence: code-generation task routing to qwen2.5-coder:7b"
        if "0.0" in t and "Sovereign AI" in t:
            return render_d07_l0(), "Figure \u2014 DFD Level 0 context diagram (system boundary & external entities)"
        if "1.0" in t and "Multimodal Ingestion" in t:
            return render_d07_l1(), "Figure \u2014 DFD Level 1: four system processes, stores D1/D2, Ollama runtime"
        if "Format Classifier" in t or "1.1 PDF Parser" in t:
            return render_d07_l2(), "Figure \u2014 DFD Level 2: Process 1.0 multimodal ingestion pipeline detail"
        return render_generic_fallback(t, fig_tag), "Figure \u2014 Diagram step view (rendered from Mermaid source)"
    except Exception as e:
        print(f"  [diagram render failed, using fallback: {e}]")
        return render_generic_fallback(t, fig_tag), "Figure \u2014 Diagram step view (rendered from Mermaid source)"

# ---------------------------------------------------------------- markdown -> docx
def build_docx_from_md(md_path, docx_path):
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    doc = Document()
    style_document(doc)
    add_header_footer(doc)
    # Cover title from first H1
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if m:
        title = doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = title.add_run(clean_inline(m.group(1).strip()))
        r.bold = True
        r.font.size = Pt(20)
        r.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        sub = doc.add_paragraph()
        r2 = sub.add_run(os.path.basename(md_path) + "  \u2022  SIH 2026 \u2014 Sovereign AI Workbench (PS 26117)  \u2022  MRPL")
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
        add_horizontal_line(doc)

    lines = content.splitlines()
    i = 0
    fig_count = 0
    in_code = False
    is_mermaid = False
    code_buf = []
    in_table = False
    table_buf = []
    first_h1_skipped = False

    def flush_table():
        nonlocal table_buf, in_table
        if table_buf:
            add_styled_table(doc, table_buf)
        table_buf = []
        in_table = False

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith("```"):
            if in_code:
                code_text = "\n".join(code_buf)
                if is_mermaid:
                    fig_count += 1
                    tag = os.path.splitext(os.path.basename(md_path))[0] + f"_fig{fig_count}"
                    print(f"  rendering diagram {fig_count} ...")
                    img, caption = render_mermaid_to_image(code_text, tag)
                    add_diagram_image(doc, img, f"{caption}  [source: Mermaid block {fig_count}]")
                else:
                    if code_text.strip():
                        add_code_block(doc, code_text)
                code_buf = []
                in_code = False
                is_mermaid = False
            else:
                flush_table()
                in_code = True
                is_mermaid = "mermaid" in s.lower()
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue
        if s.startswith("|"):
            in_table = True
            table_buf.append(line)
            i += 1
            continue
        elif in_table:
            flush_table()
        if not s:
            i += 1
            continue
        if re.match(r"^\s*---+\s*$", s) or re.match(r"^\s*\*\*\*+\s*$", s):
            add_horizontal_line(doc)
            i += 1
            continue
        if s.startswith(">"):
            q = s.lstrip(">").strip()
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith(">"):
                q += " " + lines[j].strip().lstrip(">").strip()
                j += 1
            add_blockquote(doc, q)
            i = j
            continue
        if line.startswith("# "):
            if not first_h1_skipped:
                first_h1_skipped = True
                i += 1
                continue
            doc.add_heading(clean_inline(line[2:]), level=1)
            i += 1
            continue
        elif line.startswith("## "):
            doc.add_heading(clean_inline(line[3:]), level=2)
            i += 1
            continue
        elif line.startswith("### "):
            doc.add_heading(clean_inline(line[4:]), level=3)
            i += 1
            continue
        elif line.startswith("#### "):
            p = doc.add_heading(level=4)
            p.add_run(clean_inline(line[5:])).bold = True
            i += 1
            continue
        elif s.startswith("- ") or s.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            p.clear()
            # rich runs
            tokens = re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", s[2:])
            for tok in tokens:
                if not tok:
                    continue
                if tok.startswith("**") and tok.endswith("**"):
                    r = p.add_run(tok[2:-2]); r.bold = True
                elif tok.startswith("`") and tok.endswith("`"):
                    r = p.add_run(tok[1:-1]); r.font.name = "Consolas"; r.font.size = Pt(9)
                    r.font.color.rgb = RGBColor(0x0F, 0x76, 0x6E); r.bold = True
                else:
                    r = p.add_run(re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", tok))
            i += 1
            continue
        elif re.match(r"^\s*\d+\.\s+", line):
            mm = re.match(r"^\s*(\d+\.)\s+(.*)", line)
            p = doc.add_paragraph(style="List Number")
            p.clear()
            r = p.add_run(mm.group(1) + " ")
            r.bold = True
            tokens = re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", mm.group(2))
            for tok in tokens:
                if not tok:
                    continue
                if tok.startswith("**") and tok.endswith("**"):
                    rr = p.add_run(tok[2:-2]); rr.bold = True
                elif tok.startswith("`") and tok.endswith("`"):
                    rr = p.add_run(tok[1:-1]); rr.font.name = "Consolas"; rr.font.size = Pt(9)
                    rr.font.color.rgb = RGBColor(0x0F, 0x76, 0x6E); rr.bold = True
                else:
                    p.add_run(re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", tok))
            i += 1
            continue
        else:
            add_rich_paragraph(doc, s)
            i += 1
    flush_table()
    doc.save(docx_path)
    print(f"Generated DOCX: {docx_path} ({fig_count} diagram(s) embedded)")

def main():
    mds = sorted([f for f in os.listdir(MD_DIR) if f.endswith(".md")])
    print(f"Found {len(mds)} markdown files in {MD_DIR}")
    for md in mds:
        build_docx_from_md(os.path.join(MD_DIR, md), os.path.join(DOCX_DIR, md.replace(".md", ".docx")))

if __name__ == "__main__":
    main()

