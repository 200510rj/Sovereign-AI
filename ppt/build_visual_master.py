import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os

prs = pptx.Presentation('ppt/SIH2026 PPT Format.pptx')

# Colors
C_NAVY_DARK = RGBColor(15, 23, 42)
C_NAVY_MID  = RGBColor(30, 41, 59)
C_BLUE_PRI  = RGBColor(37, 99, 235)
C_TEAL_ACC  = RGBColor(13, 148, 136)
C_EMERALD   = RGBColor(16, 185, 129)
C_ORANGE    = RGBColor(234, 88, 12)
C_MUTED     = RGBColor(100, 116, 139)
C_BG_CARD   = RGBColor(248, 250, 252)
C_BORDER    = RGBColor(226, 232, 240)
C_WHITE     = RGBColor(255, 255, 255)

def set_slide_header(slide, title_text, subtitle_text=''):
    for shape in slide.shapes:
        if shape.name == 'Title 1' and shape.has_text_frame:
            tf = shape.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            p.text = title_text
            p.font.name = 'Arial'
            p.font.size = Pt(19)
            p.font.bold = True
            p.font.color.rgb = C_NAVY_DARK
            if subtitle_text:
                p2 = tf.add_paragraph()
                p2.text = subtitle_text
                p2.font.name = 'Arial'
                p2.font.size = Pt(10.5)
                p2.font.bold = False
                p2.font.color.rgb = C_BLUE_PRI
            return

def remove_placeholder_box(slide, name='TextBox 8'):
    for shape in list(slide.shapes):
        if shape.name == name:
            sp = shape._element
            sp.getparent().remove(sp)

# =========================================================================
# SLIDE 1: TITLE PAGE
# =========================================================================
s1 = prs.slides[0]
for shape in s1.shapes:
    if shape.has_text_frame and 'TITLE PAGE' in shape.text_frame.text:
        shape.text_frame.clear()
        p = shape.text_frame.paragraphs[0]
        p.text = 'KAVACH'
        p.font.name = 'Arial'
        p.font.size = Pt(36)
        p.font.bold = True
        p.font.color.rgb = C_NAVY_DARK
        p2 = shape.text_frame.add_paragraph()
        p2.text = 'Sovereign Agentic AI Workbench for Confidential Industrial Work'
        p2.font.name = 'Arial'
        p2.font.size = Pt(14)
        p2.font.color.rgb = C_BLUE_PRI
    elif shape.has_text_frame and 'Problem Statement ID' in shape.text_frame.text:
        tf = shape.text_frame
        tf.clear()
        
        meta = [
            ('Problem Statement ID', 'SIH26117', C_ORANGE, True),
            ('Theme', 'Smart Automation', C_NAVY_DARK, False),
            ('PS Category', 'Software', C_NAVY_DARK, False),
            ('Organization', 'Mangalore Refinery & Petrochemicals Ltd. (MRPL)', C_TEAL_ACC, True),
            ('Team ID', '[TEAM ID]', C_BLUE_PRI, False),
            ('Team Name', '[TEAM NAME]', C_BLUE_PRI, False)
        ]
        for label, val, col, is_b in meta:
            p = tf.add_paragraph()
            p.text = f'{label}: '
            p.font.name = 'Arial'
            p.font.size = Pt(12)
            p.font.bold = True
            p.font.color.rgb = C_MUTED
            
            run = p.add_run()
            run.text = val
            run.font.name = 'Arial'
            run.font.size = Pt(12)
            run.font.bold = is_b
            run.font.color.rgb = col
        
        p_tag = tf.add_paragraph()
        p_tag.text = '"Claude/Codex-grade intelligence. Zero data leaves the fence."'
        p_tag.font.name = 'Arial'
        p_tag.font.size = Pt(11)
        p_tag.font.italic = True
        p_tag.font.color.rgb = C_EMERALD

# =========================================================================
# SLIDE 2: PROPOSED SOLUTION (EMBEDDED HD VISUAL DIAGRAM)
# =========================================================================
s2 = prs.slides[1]
set_slide_header(s2, 'PROPOSED SOLUTION: KAVACH SOVEREIGN WORKBENCH', 'From Confidential Industrial Data to Verified Deliverable — 100% On-Premise')
remove_placeholder_box(s2)

if os.path.exists('ppt/rendered_diagrams/slide2_solution_hd.png'):
    s2.shapes.add_picture('ppt/rendered_diagrams/slide2_solution_hd.png', Inches(0.5), Inches(1.3), Inches(12.33), Inches(5.35))

# =========================================================================
# SLIDE 3: TECHNICAL APPROACH (EMBEDDED HD LAYER STACK)
# =========================================================================
s3 = prs.slides[2]
set_slide_header(s3, 'TECHNICAL APPROACH: AIR-GAPPED SYSTEM ARCHITECTURE', 'End-to-End Multimodal Layer Stack with Zero External Data Egress')
remove_placeholder_box(s3)

if os.path.exists('ppt/rendered_diagrams/slide3_architecture_hd.png'):
    s3.shapes.add_picture('ppt/rendered_diagrams/slide3_architecture_hd.png', Inches(0.5), Inches(1.3), Inches(12.33), Inches(5.35))

# =========================================================================
# SLIDE 4: FEASIBILITY AND VIABILITY (QUADRANT CARDS)
# =========================================================================
s4 = prs.slides[3]
set_slide_header(s4, 'FEASIBILITY, RISK MITIGATION & SCALABILITY ROADMAP', 'Practical On-Premise Deployment Validated for Industrial Infrastructure')
remove_placeholder_box(s4)

f_cards = [
    ('⚙️ Technical Feasibility', [
        'Open-weight models deployable locally today via Ollama runtime.',
        'Runs efficiently on standard workstations (Intel i7/i9, 16-32GB RAM).',
        'In-memory cosine vector store eliminates database setup burden.'
    ]),
    ('🚀 Deployment Feasibility', [
        'Standalone MVP operable on single industrial PC or GPU workstation.',
        'Seamlessly scales to multi-GPU server clusters without code change.',
        '100% offline installation; air-gapped LAN deployment ready.'
    ]),
    ('🛡️ Operational Feasibility & Risk Strategy', [
        'Risk: CPU latency ➔ Mitigation: 4-bit/8-bit quantization (Q8_0/Q4_K_M).',
        'Risk: Document noise ➔ Mitigation: GLM-OCR structured text filtering.',
        'Risk: Hallucination ➔ Mitigation: Strict grounded prompt with source citations.'
    ]),
    ('📈 Scalability & Future Growth', [
        'Modular model swapping: upgrade to 14B/32B models as hardware scales.',
        'Extendable tool catalogue: add Python sandbox, SQL connectors, CAD viewers.',
        'Enterprise scale: Single PC ➔ On-Prem Server ➔ Multi-User Refinery Cluster.'
    ])
]

for idx, (head, bullets) in enumerate(f_cards):
    col = idx % 2
    row = idx // 2
    x_pos = Inches(0.6 + col * 6.1)
    y_pos = Inches(1.4 + row * 2.2)
    
    card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x_pos, y_pos, Inches(5.9), Inches(2.05))
    card.fill.solid()
    card.fill.fore_color.rgb = C_BG_CARD
    card.line.color.rgb = C_BORDER
    tf = card.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = head
    p.font.name = 'Arial'
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = C_NAVY_DARK
    
    for bullet in bullets:
        bp = tf.add_paragraph()
        bp.text = f'• {bullet}'
        bp.font.name = 'Arial'
        bp.font.size = Pt(9.5)
        bp.font.color.rgb = C_MUTED

t_box = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(5.8), Inches(12.1), Inches(0.95))
t_box.fill.solid()
t_box.fill.fore_color.rgb = C_NAVY_DARK
t_box.line.color.rgb = C_NAVY_DARK
tf = t_box.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = 'DEPLOYMENT MATURITY TIMELINE:'
p.font.name = 'Arial'
p.font.size = Pt(9)
p.font.bold = True
p.font.color.rgb = C_EMERALD

p2 = tf.add_paragraph()
p2.text = '[MVP PHASE: Single Workstation / Local PC]  ➔  [PRODUCTION PHASE: On-Premise GPU Server]  ➔  [ENTERPRISE: Multi-User Air-Gapped Cluster]'
p2.font.name = 'Arial'
p2.font.size = Pt(10)
p2.font.bold = True
p2.font.color.rgb = C_WHITE

# =========================================================================
# SLIDE 5: IMPACT AND BENEFITS (EMBEDDED HD COMPARISON DIAGRAM)
# =========================================================================
s5 = prs.slides[4]
set_slide_header(s5, 'IMPACT, BENEFICIARIES & VALUE FOR MRPL REFINERY', 'Tangible Operational, Safety & Economic Gains Across Industrial Operations')
remove_placeholder_box(s5)

if os.path.exists('ppt/rendered_diagrams/slide5_workflow_hd.png'):
    s5.shapes.add_picture('ppt/rendered_diagrams/slide5_workflow_hd.png', Inches(0.5), Inches(1.3), Inches(12.33), Inches(5.35))

# =========================================================================
# SLIDE 6: RESEARCH AND REFERENCES
# =========================================================================
s6 = prs.slides[5]
set_slide_header(s6, 'RESEARCH, DIFFERENTIATION MATRIX & REFERENCES', 'Academic Foundations, Model Benchmarks & Competitive Differentiators')
remove_placeholder_box(s6)

caps = ['Open-Weight LLMs', 'Local Inference', 'Agent Orchestration', 'Grounded RAG', 'Multimodal Vision', 'GLM-OCR Engine', 'Sandboxed Tools', 'Real Deliverables']
for idx, cap in enumerate(caps):
    c_x = Inches(0.6 + (idx % 4) * 3.05)
    c_y = Inches(1.35 + (idx // 4) * 0.45)
    badge = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_x, c_y, Inches(2.95), Inches(0.38))
    badge.fill.solid()
    badge.fill.fore_color.rgb = C_NAVY_DARK
    badge.line.color.rgb = C_NAVY_DARK
    tf = badge.text_frame
    p = tf.paragraphs[0]
    p.text = cap
    p.font.name = 'Arial'
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = C_WHITE
    p.alignment = PP_ALIGN.CENTER

matrix_box = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(2.35), Inches(12.1), Inches(2.3))
matrix_box.fill.solid()
matrix_box.fill.fore_color.rgb = C_BG_CARD
matrix_box.line.color.rgb = C_BORDER
tf = matrix_box.text_frame
tf.word_wrap = True

p = tf.paragraphs[0]
p.text = 'COMPETITIVE DIFFERENTIATION: KAVACH vs. GENERIC CLOUD COPILOTS'
p.font.name = 'Arial'
p.font.size = Pt(10)
p.font.bold = True
p.font.color.rgb = C_NAVY_DARK

features = [
    '• 100% On-Premise Execution: [KAVACH: YES (Local HW)] vs [Cloud Copilots: NO (Remote Data Egress)]',
    '• Strict Air-Gapped Network Operation: [KAVACH: YES (No Internet Needed)] vs [Cloud Copilots: NO (Always Online)]',
    '• Multi-Model Dynamic Task Routing: [KAVACH: YES (Specialist Coder/OCR)] vs [Cloud Copilots: NO (Single Monolith)]',
    '• Scanned Document & Image OCR: [KAVACH: YES (Integrated GLM-OCR)] vs [Cloud Copilots: ⚠️ Limited/Paid Cloud Addon]',
    '• Verified Real File Deliverables: [KAVACH: YES (DOCX, PPTX, XLSX, Code)] vs [Cloud Copilots: ❌ Chatbot Text Only]',
    '• Network Audit & Zero-Egress Proof: [KAVACH: YES (Tamper-Proof Logs)] vs [Cloud Copilots: ❌ Third-Party Blackbox]'
]
for feat in features:
    p = tf.add_paragraph()
    p.text = feat
    p.font.name = 'Arial'
    p.font.size = Pt(9)
    p.font.color.rgb = C_MUTED

ref_box = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(4.75), Inches(12.1), Inches(1.95))
ref_box.fill.solid()
ref_box.fill.fore_color.rgb = C_NAVY_MID
ref_box.line.color.rgb = C_NAVY_MID
tf = ref_box.text_frame
tf.word_wrap = True

p = tf.paragraphs[0]
p.text = 'KEY RESEARCH & BENCHMARK REFERENCES:'
p.font.name = 'Arial'
p.font.size = Pt(10)
p.font.bold = True
p.font.color.rgb = C_EMERALD

refs_list = [
    '• Qwen 3.5 & Qwen 2.5-Coder: Open-Weight Large Language Models for Reasoning & Code (Alibaba Cloud Research, 2024-2025)',
    '• GLM-OCR: Generalized Multimodal Model for Visual Document Understanding and Text Extraction (Zhipu AI, 2025)',
    '• Nomic Embed Text: High-Dimensional Contextual Vector Representations for Dense Retrieval (Nussbaum et al., 2024)',
    '• Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis et al., NeurIPS Research Standards)',
    '• Mangalore Refinery and Petrochemicals Limited (MRPL) — PS 26117 On-Premise Industrial AI Workbench Requirements'
]
for r in refs_list:
    p = tf.add_paragraph()
    p.text = r
    p.font.name = 'Arial'
    p.font.size = Pt(8.5)
    p.font.color.rgb = RGBColor(226, 232, 240)

# DELETE SLIDE 7
rId = prs.slides._sldIdLst[6].rId
prs.part.drop_rel(rId)
del prs.slides._sldIdLst[6]

output_file = 'ppt/SIH2026_KAVACH_Visual_Master.pptx'
prs.save(output_file)
print(f'Successfully built {output_file} with {len(prs.slides)} slides!')
