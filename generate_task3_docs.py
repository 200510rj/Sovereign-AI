# Complete Day 2 Task 3 Documentation Builder
import os, sys, json, math
from pathlib import Path
from datetime import datetime

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, HRFlowable
)
from reportlab.pdfgen import canvas

DOCS_DIR = Path('day2_task3_documentation')
DOCS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR = DOCS_DIR / 'screenshots'
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

MD_FILE = DOCS_DIR / 'Day_2_Task_3_Mitigation_Hardening_Report.md'
DOCX_FILE = DOCS_DIR / 'Day_2_Task_3_Mitigation_Hardening_Report.docx'
PDF_FILE = DOCS_DIR / 'Day_2_Task_3_Mitigation_Hardening_Report.pdf'

print('Step 1: Writing full Markdown documentation...')
