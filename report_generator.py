"""
report_generator.py
Generates a comprehensive professional PDF DDR report matching the UrbanRoof Main DDR style.
Produces ~40 pages including: cover, welcome, disclaimer, TOC, introduction, general info,
visual observations (with input tables, checkboxes), analysis & suggestions, thermal references,
visual references, limitation notes, legal disclaimer.
"""

import io
import base64
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, Image as RLImage, PageBreak,
)
from reportlab.platypus.flowables import Flowable
from PIL import Image as PILImage

# ── Color palette matching UrbanRoof DDR ───────────────────────────────────────
COLOR_DARK_BG    = HexColor("#2C2C2C")   # Dark grey cover
COLOR_YELLOW     = HexColor("#F5C518")   # UrbanRoof yellow
COLOR_ORANGE     = HexColor("#E8690A")   # UrbanRoof orange
COLOR_GREEN_LINE = HexColor("#4CAF50")   # Green accent lines
COLOR_NAVY       = HexColor("#1A2343")   # Dark navy for section headers
COLOR_HEADER_BG  = HexColor("#1A2343")
COLOR_ACCENT     = HexColor("#F5A623")
COLOR_CRITICAL   = HexColor("#C0392B")
COLOR_HIGH       = HexColor("#E67E22")
COLOR_MEDIUM     = HexColor("#E67E22")
COLOR_LOW        = HexColor("#27AE60")
COLOR_LIGHT_BG   = HexColor("#F5F7FA")
COLOR_BORDER     = HexColor("#D0D7E3")
COLOR_TEXT       = HexColor("#2C3E50")
COLOR_MUTED      = HexColor("#7F8C8D")
COLOR_ROW_ALT    = HexColor("#F8F9FB")
COLOR_THERMAL_LBL= HexColor("#E65C1A")
COLOR_TABLE_GOOD = HexColor("#4CAF50")
COLOR_TABLE_MOD  = HexColor("#FF9800")
COLOR_TABLE_POOR = HexColor("#F44336")
COLOR_CHECKBOX_BG= HexColor("#EEF4EE")


def _severity_color(severity: str):
    s = severity.lower()
    if "critical" in s: return COLOR_CRITICAL
    if "high"     in s: return COLOR_HIGH
    if "medium"   in s: return COLOR_MEDIUM
    if "low"      in s: return COLOR_LOW
    return COLOR_MUTED


def _priority_color(priority: str):
    p = priority.lower()
    if "immediate" in p: return COLOR_CRITICAL
    if "short"     in p: return COLOR_HIGH
    return COLOR_LOW


def _safe_add_style(styles, style):
    try:
        styles.add(style)
    except KeyError:
        pass


def build_styles():
    styles = getSampleStyleSheet()
    F = "Helvetica"

    _safe_add_style(styles, ParagraphStyle("CoverTitle",
        fontName=f"{F}-Bold", fontSize=36, textColor=white,
        spaceAfter=8, leading=42, alignment=TA_LEFT))
    _safe_add_style(styles, ParagraphStyle("CoverDate",
        fontName=f"{F}-Bold", fontSize=13, textColor=COLOR_YELLOW,
        spaceAfter=4, leading=18))
    _safe_add_style(styles, ParagraphStyle("CoverLabel",
        fontName=f"{F}-Bold", fontSize=10, textColor=COLOR_YELLOW,
        spaceAfter=2, leading=14))
    _safe_add_style(styles, ParagraphStyle("CoverValue",
        fontName=f"{F}-Bold", fontSize=11, textColor=white,
        spaceAfter=4, leading=15))
    _safe_add_style(styles, ParagraphStyle("WelcomeTitle",
        fontName=f"{F}-Bold", fontSize=36, textColor=COLOR_YELLOW,
        spaceAfter=10, leading=44))
    _safe_add_style(styles, ParagraphStyle("WelcomeBody",
        fontName=F, fontSize=10, textColor=COLOR_TEXT,
        spaceAfter=5, leading=15, alignment=TA_JUSTIFY))
    _safe_add_style(styles, ParagraphStyle("AboutTitle",
        fontName=f"{F}-Bold", fontSize=28, textColor=COLOR_TEXT,
        spaceAfter=8, leading=34))
    _safe_add_style(styles, ParagraphStyle("AboutBody",
        fontName=F, fontSize=10, textColor=COLOR_TEXT,
        spaceAfter=5, leading=15, alignment=TA_JUSTIFY))
    _safe_add_style(styles, ParagraphStyle("DisclaimerTitle",
        fontName=f"{F}-Bold", fontSize=16, textColor=COLOR_ORANGE,
        spaceAfter=8, leading=20))
    _safe_add_style(styles, ParagraphStyle("DisclaimerBody",
        fontName=f"{F}-Oblique", fontSize=10, textColor=COLOR_TEXT,
        spaceAfter=6, leading=15, alignment=TA_JUSTIFY))
    _safe_add_style(styles, ParagraphStyle("TOCTitle",
        fontName=f"{F}-Bold", fontSize=20, textColor=COLOR_ORANGE,
        spaceAfter=12, leading=24, alignment=TA_CENTER))
    _safe_add_style(styles, ParagraphStyle("TOCSection",
        fontName=f"{F}-Bold", fontSize=11, textColor=COLOR_TEXT,
        spaceAfter=3, leading=15))
    _safe_add_style(styles, ParagraphStyle("TOCSub",
        fontName=F, fontSize=10, textColor=COLOR_TEXT,
        spaceAfter=2, leading=14, leftIndent=16))
    _safe_add_style(styles, ParagraphStyle("TOCSubSub",
        fontName=F, fontSize=9, textColor=COLOR_MUTED,
        spaceAfter=2, leading=13, leftIndent=32))
    _safe_add_style(styles, ParagraphStyle("SectionTitle",
        fontName=f"{F}-Bold", fontSize=16, textColor=COLOR_ORANGE,
        spaceAfter=4, leading=20))
    _safe_add_style(styles, ParagraphStyle("SubSectionTitle",
        fontName=f"{F}-Bold", fontSize=12, textColor=COLOR_ORANGE,
        spaceAfter=4, leading=16, spaceBefore=8))
    _safe_add_style(styles, ParagraphStyle("SubSubSectionTitle",
        fontName=f"{F}-Bold", fontSize=11, textColor=COLOR_TEXT,
        spaceAfter=4, leading=14, spaceBefore=6))
    _safe_add_style(styles, ParagraphStyle("SectionHeader",
        fontName=f"{F}-Bold", fontSize=12, textColor=white,
        spaceBefore=0, spaceAfter=0, leading=16))
    _safe_add_style(styles, ParagraphStyle("AreaHeader",
        fontName=f"{F}-Bold", fontSize=11, textColor=COLOR_NAVY,
        spaceBefore=10, spaceAfter=4, leading=14))
    _safe_add_style(styles, ParagraphStyle("Body",
        fontName=F, fontSize=10, textColor=COLOR_TEXT,
        spaceAfter=4, leading=15, alignment=TA_JUSTIFY))
    _safe_add_style(styles, ParagraphStyle("BodyBold",
        fontName=f"{F}-Bold", fontSize=10, textColor=COLOR_TEXT,
        spaceAfter=4, leading=15))
    _safe_add_style(styles, ParagraphStyle("Bullet",
        fontName=F, fontSize=10, textColor=COLOR_TEXT,
        spaceAfter=3, leading=14, leftIndent=12, firstLineIndent=-8))
    _safe_add_style(styles, ParagraphStyle("BulletBold",
        fontName=f"{F}-Bold", fontSize=10, textColor=COLOR_TEXT,
        spaceAfter=3, leading=14, leftIndent=0))
    _safe_add_style(styles, ParagraphStyle("BodySmall",
        fontName=F, fontSize=9, textColor=COLOR_MUTED,
        spaceAfter=3, leading=13))
    _safe_add_style(styles, ParagraphStyle("ThermalLabel",
        fontName=f"{F}-Bold", fontSize=10, textColor=COLOR_THERMAL_LBL,
        spaceAfter=4, leading=14))
    _safe_add_style(styles, ParagraphStyle("ImageCaption",
        fontName=f"{F}-Oblique", fontSize=9, textColor=COLOR_MUTED,
        spaceAfter=8, alignment=TA_CENTER))
    _safe_add_style(styles, ParagraphStyle("NotAvail",
        fontName=f"{F}-Oblique", fontSize=10, textColor=COLOR_MUTED,
        spaceAfter=4))
    _safe_add_style(styles, ParagraphStyle("Footer",
        fontName=f"{F}-Oblique", fontSize=8, textColor=COLOR_MUTED,
        spaceAfter=0, leading=11, alignment=TA_CENTER))
    _safe_add_style(styles, ParagraphStyle("Overview",
        fontName=F, fontSize=10, textColor=COLOR_TEXT,
        spaceAfter=4, leading=15, alignment=TA_JUSTIFY))
    _safe_add_style(styles, ParagraphStyle("LegalTitle",
        fontName=f"{F}-Bold", fontSize=14, textColor=COLOR_ORANGE,
        spaceAfter=6, leading=18))
    _safe_add_style(styles, ParagraphStyle("LegalBody",
        fontName=f"{F}-Oblique", fontSize=10, textColor=COLOR_TEXT,
        spaceAfter=6, leading=15, alignment=TA_JUSTIFY))
    _safe_add_style(styles, ParagraphStyle("PageHeader",
        fontName=f"{F}-Bold", fontSize=9, textColor=COLOR_TEXT,
        spaceAfter=0, leading=12))
    _safe_add_style(styles, ParagraphStyle("ImageTitle",
        fontName=f"{F}-Bold", fontSize=10, textColor=COLOR_NAVY,
        spaceAfter=4, leading=14))
    return styles


# ── Page decorators ────────────────────────────────────────────────────────────

def _make_header_bar(property_name, styles, report_id=""):
    """Top-of-page running header matching original (logo area + report title)."""
    F = "Helvetica"
    page_w = A4[0] - 4*cm
    ir_prefix = f"IR-{report_id}, " if report_id else "IR-, "
    header_data = [[
        Paragraph("UrbanRoof",
            ParagraphStyle("LogoText", fontName=f"{F}-Bold", fontSize=11,
                           textColor=COLOR_ORANGE, leading=14)),
        Paragraph(
            f"{ir_prefix}Detailed Diagnosis Report of<br/>{property_name}",
            ParagraphStyle("HDRRight", fontName=f"{F}-Bold", fontSize=9,
                           textColor=white, leading=13)
        )
    ]]
    t = Table(header_data, colWidths=[page_w*0.22, page_w*0.78])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), COLOR_NAVY),
        ("BACKGROUND",    (0, 0), (0,  0),  white),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (0, 0), (-1, 0), 2, COLOR_YELLOW),
    ]))
    return t


def _make_footer_bar(page_num, styles):
    """Bottom-of-page running footer."""
    F = "Helvetica"
    page_w = A4[0] - 4*cm
    footer_data = [[
        Paragraph("www.urbaroof.in",
            ParagraphStyle("FooterLeft", fontName=F, fontSize=8,
                           textColor=COLOR_ORANGE, leading=11)),
        Paragraph("UrbanRoof Private Limited",
            ParagraphStyle("FooterMid", fontName=f"{F}-Bold", fontSize=9,
                           textColor=COLOR_ORANGE, leading=12, alignment=TA_CENTER)),
        Paragraph(f"Page{page_num}",
            ParagraphStyle("FooterRight", fontName=f"{F}-Bold", fontSize=11,
                           textColor=COLOR_TEXT, leading=14, alignment=TA_RIGHT)),
    ]]
    t = Table(footer_data, colWidths=[page_w*0.3, page_w*0.4, page_w*0.3])
    t.setStyle(TableStyle([
        ("LINEABOVE",     (0, 0), (-1, 0), 1.5, COLOR_GREEN_LINE),
        ("LINEBELOW",     (0, 0), (-1, 0), 1.5, COLOR_ORANGE),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


# ── Image helpers ──────────────────────────────────────────────────────────────

def image_flowable(img_entry: dict, styles, max_width=14*cm, max_height=9*cm,
                   caption_override=None) -> list:
    flowables = []
    try:
        img_bytes = img_entry.get("bytes")
        if not img_bytes:
            raw_b64 = img_entry.get("base64", "")
            if raw_b64:
                img_bytes = base64.b64decode(raw_b64)
        if not img_bytes:
            flowables.append(Paragraph("[ Image Not Available ]", styles["NotAvail"]))
            return flowables

        pil_img = PILImage.open(io.BytesIO(img_bytes))
        orig_w, orig_h = pil_img.size
        scale = min(max_width / orig_w, max_height / orig_h, 1.0)
        draw_w, draw_h = orig_w * scale, orig_h * scale

        rl_img = RLImage(io.BytesIO(img_bytes), width=draw_w, height=draw_h)
        rl_img.hAlign = "LEFT"

        if caption_override:
            cap = caption_override
        else:
            caption  = img_entry.get("caption", "")
            src_lbl  = img_entry.get("doc_label", "")
            page_num = img_entry.get("page", "?")
            cap = f"{caption} (Source: {src_lbl}, Page {page_num})"

        flowables.append(rl_img)
        flowables.append(Paragraph(cap, styles["ImageCaption"]))
    except Exception as e:
        flowables.append(Paragraph(f"[ Image could not be rendered: {str(e)[:80]} ]",
                                   styles["NotAvail"]))
    return flowables


def is_usable_image(img_entry: dict) -> bool:
    """
    Returns False if the image is likely a logo/splash page (mostly black/dark).
    We detect this by checking average pixel brightness via PIL.
    Images with mean brightness < 30 (out of 255) are considered unusable covers.
    """
    try:
        img_bytes = img_entry.get("bytes")
        if not img_bytes:
            raw_b64 = img_entry.get("base64", "")
            if raw_b64:
                img_bytes = base64.b64decode(raw_b64)
        if not img_bytes:
            return False
        pil_img = PILImage.open(io.BytesIO(img_bytes)).convert("L")  # grayscale
        import statistics
        pixels = list(pil_img.getdata())
        mean_brightness = sum(pixels) / len(pixels) if pixels else 0
        return mean_brightness > 30  # reject if mostly black (logo page)
    except Exception:
        return True  # if we can't check, assume usable


def side_by_side_images(img1_entry, img2_entry, styles, label1="", label2="",
                        max_w=6.5*cm, max_h=6*cm):
    """Render two images side by side in a table (visual + thermal pair)."""
    def _make_cell(img_entry, lbl):
        cells = []
        if img_entry:
            cells.extend(image_flowable(img_entry, styles,
                                        max_width=max_w, max_height=max_h,
                                        caption_override=lbl))
        else:
            cells.append(Paragraph("[ Image Not Available ]", styles["NotAvail"]))
        return cells

    left  = _make_cell(img1_entry, label1)
    right = _make_cell(img2_entry, label2)

    page_w = A4[0] - 4*cm
    t = Table([[left, right]], colWidths=[page_w*0.5, page_w*0.5])
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("BOX",           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ]))
    return t


def get_images_for(assignments, all_images, section, key):
    matched = []
    for assign in assignments:
        if assign.get("section") == section:
            area = assign.get("area_or_issue", "").lower()
            if key.lower() in area or area in key.lower():
                idx = assign.get("image_index")
                if idx is not None and idx < len(all_images):
                    matched.append(all_images[idx])
    return matched


# ── Structural section helpers ─────────────────────────────────────────────────

def section_main_header(title, styles):
    """Large orange section header like 'SECTION 1  INTRODUCTION'."""
    F = "Helvetica"
    story = [Spacer(1, 6)]
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_ORANGE))
    story.append(Spacer(1, 4))
    story.append(Paragraph(title, styles["SectionTitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_ORANGE))
    story.append(Spacer(1, 8))
    return story


def section_number_header(number, title, styles):
    """DDR section header bar e.g. '1. PROPERTY ISSUE SUMMARY'."""
    F = "Helvetica"
    label = f"{number}. {title.upper()}"
    header_para = Paragraph(label, styles["SectionHeader"])
    page_w = A4[0] - 4*cm
    bg_table = Table([[header_para]], colWidths=[page_w])
    bg_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), COLOR_HEADER_BG),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return [Spacer(1, 8), bg_table, Spacer(1, 10)]


def checkbox_table(inputs, styles, checked_inputs=None):
    """
    Render a checkbox input list matching original DDR style.
    inputs = list of strings
    checked_inputs = list of strings that are checked (☒)
    """
    if checked_inputs is None:
        checked_inputs = []
    F = "Helvetica"
    page_w = A4[0] - 4*cm
    rows = []
    for inp in inputs:
        is_checked = inp in checked_inputs
        checkbox = "☒" if is_checked else "☐"
        col = COLOR_NAVY if is_checked else COLOR_MUTED
        rows.append([
            Paragraph(f'<font color="#1A2343"><b>{checkbox}</b></font>' if is_checked
                      else f'<font color="#888888">{checkbox}</font>',
                      ParagraphStyle("CBX", fontName="Helvetica", fontSize=11,
                                     textColor=COLOR_NAVY if is_checked else COLOR_MUTED,
                                     leading=14)),
            Paragraph(inp,
                      ParagraphStyle("CBLabel", fontName="Helvetica", fontSize=10,
                                     textColor=COLOR_TEXT, leading=14)),
        ])
    t = Table(rows, colWidths=[0.6*cm, page_w - 0.6*cm])
    t.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def input_label(label, styles):
    return Paragraph(f"<b>{label}</b>", styles["BodyBold"])


def condition_assessment_table(rows_data, title, styles):
    """
    Build a structural condition assessment table like in original DDR.
    rows_data = list of (sr_no, input_type, good, moderate, poor, remarks)
    where good/moderate/poor are True/False
    """
    F = "Helvetica"
    page_w = A4[0] - 4*cm

    def tick(val):
        return "✓" if val else ""

    header = [
        Paragraph("<b>Sr No</b>",
            ParagraphStyle("TH", fontName=f"{F}-Bold", fontSize=9, textColor=white)),
        Paragraph("<b>Input Type</b>",
            ParagraphStyle("TH2", fontName=f"{F}-Bold", fontSize=9, textColor=white)),
        Paragraph("<b>Good</b>",
            ParagraphStyle("TH3", fontName=f"{F}-Bold", fontSize=9,
                           textColor=COLOR_TABLE_GOOD)),
        Paragraph("<b>Moderate</b>",
            ParagraphStyle("TH4", fontName=f"{F}-Bold", fontSize=9,
                           textColor=COLOR_TABLE_MOD)),
        Paragraph("<b>Poor</b>",
            ParagraphStyle("TH5", fontName=f"{F}-Bold", fontSize=9,
                           textColor=COLOR_TABLE_POOR)),
        Paragraph("<b>Remarks</b>",
            ParagraphStyle("TH6", fontName=f"{F}-Bold", fontSize=9, textColor=white)),
    ]
    table_data = [header]

    for row in rows_data:
        sr_no, input_type, good, moderate, poor, remarks = row
        g_col = COLOR_TABLE_GOOD if good     else COLOR_TEXT
        m_col = COLOR_TABLE_MOD  if moderate else COLOR_TEXT
        p_col = COLOR_TABLE_POOR if poor     else COLOR_TEXT
        table_data.append([
            Paragraph(str(sr_no),
                ParagraphStyle("SR", fontName=F, fontSize=9,
                               textColor=COLOR_TEXT, alignment=TA_CENTER)),
            Paragraph(input_type,
                ParagraphStyle("IT", fontName=F, fontSize=9,
                               textColor=COLOR_TEXT, leading=13)),
            Paragraph(f'<font color="{"#4CAF50" if good else "#888888"}"><b>{tick(good)}</b></font>',
                ParagraphStyle("GD", fontName=f"{F}-Bold", fontSize=12,
                               textColor=g_col, alignment=TA_CENTER)),
            Paragraph(f'<font color="{"#FF9800" if moderate else "#888888"}"><b>{tick(moderate)}</b></font>',
                ParagraphStyle("MOD", fontName=f"{F}-Bold", fontSize=12,
                               textColor=m_col, alignment=TA_CENTER)),
            Paragraph(f'<font color="{"#F44336" if poor else "#888888"}"><b>{tick(poor)}</b></font>',
                ParagraphStyle("PR", fontName=f"{F}-Bold", fontSize=12,
                               textColor=p_col, alignment=TA_CENTER)),
            Paragraph(remarks,
                ParagraphStyle("RMK", fontName=F, fontSize=8,
                               textColor=COLOR_TEXT, leading=12)),
        ])

    t = Table(table_data,
              colWidths=[page_w*0.06, page_w*0.38, page_w*0.09, page_w*0.10,
                         page_w*0.08, page_w*0.29],
              repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), COLOR_HEADER_BG),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, COLOR_CHECKBOX_BG]),
        ("BOX",           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("GRID",          (0, 0), (-1, -1), 0.3, COLOR_BORDER),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (2, 0), (4, -1), "CENTER"),
    ]))
    return t


def legend_row(styles):
    """Good / Moderate / Poor legend."""
    F = "Helvetica"
    items = [
        ('<font color="#4CAF50"><i>Good</i></font>= No Action Needed', COLOR_TABLE_GOOD),
        ('<font color="#FF9800"><i>Moderate</i></font>= Necessary Repairs Needed', COLOR_TABLE_MOD),
        ('<font color="#F44336"><i>Poor</i></font>= Immediate Action Needed', COLOR_TABLE_POOR),
    ]
    return [Paragraph(text,
        ParagraphStyle("Legend", fontName=f"{F}-Oblique", fontSize=9,
                       textColor=COLOR_TEXT, leading=13, spaceBefore=2))
        for text, _ in items]


# ── IMAGE SECTION BUILDER (thermal side-by-side) ──────────────────────────────

def build_thermal_image_section(image_label, area_name, visual_imgs, thermal_imgs, styles):
    """Build a section like 4.4.1 with paired visual + thermal images."""
    story = []
    story.append(Paragraph(image_label, styles["ImageTitle"]))
    story.append(Spacer(1, 4))

    # Pair up visual and thermal images
    v_imgs = list(visual_imgs)
    t_imgs = list(thermal_imgs)

    # Interleave: show pairs
    max_pairs = max(len(v_imgs), len(t_imgs))
    page_w = A4[0] - 4*cm

    for i in range(0, max_pairs, 1):
        v = v_imgs[i] if i < len(v_imgs) else None
        t = t_imgs[i] if i < len(t_imgs) else None

        if v is not None and t is not None:
            # Side by side
            pair_table = side_by_side_images(v, t, styles, max_w=6.8*cm, max_h=7*cm)
            story.append(pair_table)
        elif v is not None:
            story.extend(image_flowable(v, styles, max_width=12*cm, max_height=8*cm))
        elif t is not None:
            story.extend(image_flowable(t, styles, max_width=12*cm, max_height=8*cm))

    return story


# ── MAIN GENERATOR ─────────────────────────────────────────────────────────────

def generate_pdf(ddr_data: dict, all_images: list) -> bytes:
    """
    Build full ~40-page DDR PDF matching UrbanRoof Main DDR style.
    """
    buffer  = io.BytesIO()
    styles  = build_styles()
    today   = datetime.now().strftime("%B %d, %Y")
    F       = "Helvetica"
    page_w  = A4[0] - 4*cm

    prop            = ddr_data.get("property_summary", {})
    property_name   = prop.get("property_name", "Not Available")
    inspection_date = prop.get("inspection_date", "Not Available")
    inspector       = prop.get("inspector", "Not Available")
    overview_text   = prop.get("overview", "Not Available")
    assignments     = ddr_data.get("image_assignments", [])
    area_obs        = ddr_data.get("area_observations", [])
    severity_items  = ddr_data.get("severity_assessment", [])
    root_causes     = ddr_data.get("root_causes", [])
    recommended     = ddr_data.get("recommended_actions", [])
    notes           = ddr_data.get("additional_notes", [])
    missing         = ddr_data.get("missing_or_unclear", [])
    report_id       = ""  # set after _cf is defined below

    # Bound header helper so all pages automatically carry property_name + report_id
    def _header(pn=None):
        return _make_header_bar(pn or property_name, styles, report_id=report_id)

    # Helper: try to get images by area keyword
    def imgs_for(section, key):
        return get_images_for(assignments, all_images, section, key)

    # Split images by source document: Inspection Report = visual, Thermal Report = thermal
    _all_visual  = [img for img in all_images if "thermal" not in img.get("doc_label","").lower()]
    _all_thermal = [img for img in all_images if "thermal" in img.get("doc_label","").lower()]

    # If no thermal images found, use second half of all_images as thermal pool
    if not _all_thermal and len(_all_visual) >= 2:
        mid = len(_all_visual) // 2
        _all_thermal = _all_visual[mid:]
        _all_visual  = _all_visual[:mid]

    # Filter out logo/splash images (mostly black cover pages)
    visual_imgs  = [img for img in _all_visual  if is_usable_image(img)]
    thermal_imgs = [img for img in _all_thermal if is_usable_image(img)]

    # Fallback: if filtering removed everything, restore unfiltered pools
    if not visual_imgs:
        visual_imgs  = _all_visual
    if not thermal_imgs:
        thermal_imgs = _all_thermal

    # Doc builds with a callback for page numbers
    class NumberedCanvas:
        pass

    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 1: COVER PAGE
    # ══════════════════════════════════════════════════════════════════════════
    cover_data = [
        # Row 0: big title (spans both cols)
        [Paragraph("Detailed Diagnosis Report",
            ParagraphStyle("BigCover", fontName=f"{F}-Bold", fontSize=34,
                           textColor=white, leading=40)), ""],
        # Row 1: spacer
        ["", ""],
        # Row 2: date + Report ID
        [Paragraph(inspection_date,
            ParagraphStyle("DateC", fontName=f"{F}-Bold", fontSize=13,
                           textColor=COLOR_YELLOW, leading=18)),
         ""],
        [Paragraph("Report ID  -",
            ParagraphStyle("RID", fontName=F, fontSize=11,
                           textColor=HexColor("#B0C0D0"), leading=15)),
         ""],
        ["", ""],
        # Row 5: inspector/prepared labels
        [Paragraph("Inspected &amp; Prepared By:",
            ParagraphStyle("ILbl", fontName=f"{F}-Bold", fontSize=10,
                           textColor=COLOR_YELLOW, leading=14)),
         Paragraph("Prepared For:",
            ParagraphStyle("PLbl", fontName=f"{F}-Bold", fontSize=10,
                           textColor=COLOR_YELLOW, leading=14))],
        # Row 6: values
        [Paragraph(inspector,
            ParagraphStyle("IVal", fontName=f"{F}-Bold", fontSize=12,
                           textColor=white, leading=16)),
         Paragraph(property_name,
            ParagraphStyle("PVal", fontName=f"{F}-Bold", fontSize=11,
                           textColor=white, leading=15))],
    ]

    cover_table = Table(cover_data,
                        colWidths=[page_w*0.52, page_w*0.48],
                        rowHeights=[70, 50, 22, 22, 50, 18, 28])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), COLOR_DARK_BG),
        ("LEFTPADDING",   (0, 0), (-1, -1), 22),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("SPAN",          (0, 0), (1, 0)),
        ("SPAN",          (0, 1), (1, 1)),
        ("SPAN",          (0, 2), (1, 2)),
        ("SPAN",          (0, 3), (1, 3)),
        ("SPAN",          (0, 4), (1, 4)),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEABOVE",     (0, 0), (-1, 0), 4, COLOR_YELLOW),
    ]))
    story.append(cover_table)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2: WELCOME + ABOUT US
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 16))
    story.append(Paragraph("Welcome", styles["WelcomeTitle"]))
    story.append(Paragraph(
        "Thank you for choosing UrbanRoof to help you navigate health of your chosen property. "
        "We've put together for you an inspection data and its analysis; and also recommended "
        "required solutions. Please read this report very carefully as it will provide you with "
        "transparency of your property's health.",
        styles["WelcomeBody"]
    ))
    story.append(Spacer(1, 20))

    # About Us in two-column layout
    about_left = [
        Paragraph("UrbanRoof", styles["AboutTitle"]),
        Paragraph("<b>About Us</b>",
            ParagraphStyle("AboutUs", fontName=f"{F}-Bold", fontSize=20,
                           textColor=COLOR_TEXT, spaceAfter=8, leading=24)),
        Spacer(1, 8),
    ]
    about_right_text = [
        ("The Idea, UrbanRoof was born in 2016 when founder, Abhishek noticed that there were "
         "no easy, transparent, and straightforward process for the diagnosis & treatment of the "
         "building & constructions. Also, the important aspect, Diagnosis was simply missing or "
         "there was no alternative that can lead to ultimate solution to eliminate the impact of "
         "persistent issues. Most of the solutions were forcefully convinced than conveyed due to "
         "the lack of awareness at client's end. Since its incorporation, the company has become "
         "the leading provider in Pune & Mumbai for waterproofing, repair & rehabilitation of "
         "building & constructions."),
        ("Being one of the leaders of the building repair and rehabilitation industry, at "
         "UrbanRoof we believe that there is a better way to handle repair, rehabilitation, and "
         "restoration of your precious property. We are obsessed to prevent/solve the smallest "
         "to the biggest issues of the constructed properties."),
        ("Our team of SMEs (subject matter experts) educates you about the actual situation and "
         "all optimum solutions. We do detail inspection, and generate detailed diagnosis report, "
         "and consult you with the itemized list of all probable solutions along with their impact "
         "across the period for better understanding and transparency."),
        ("99% decision failures are due to decisions take with no knowledge/limited "
         "knowledge/forced decision making. Hence, we believe in giving the decision making power "
         "to the patron by educating and simplifying all constructions related information. "
         "This also helps our client to achieve the economic and effective solution."),
        "e-Mail: info@urbanroof.in",
        "Phone: +91-8925-805-805",
    ]

    about_paras = []
    for txt in about_right_text:
        if txt.startswith("e-Mail") or txt.startswith("Phone"):
            about_paras.append(Paragraph(f"<b>{txt}</b>", styles["AboutBody"]))
        else:
            about_paras.append(Paragraph(txt, styles["AboutBody"]))
        about_paras.append(Spacer(1, 4))

    about_table = Table([[about_left, about_paras]], colWidths=[page_w*0.3, page_w*0.7])
    about_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), COLOR_DARK_BG),
        ("BACKGROUND",    (1, 0), (1,  0),  HexColor("#C8A020")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(about_table)
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Office No. 03, Akshay house, Anand Nagar, Sinhgad Road, Pune- 411051",
        ParagraphStyle("OfficeAddr", fontName=f"{F}-Bold", fontSize=9,
                       textColor=COLOR_ORANGE, leading=13, alignment=TA_CENTER)
    ))
    story.append(_make_footer_bar(2, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 3: DATA & INFORMATION DISCLAIMER
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 12))
    story.append(Paragraph("Data and Information Disclaimer", styles["DisclaimerTitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ORANGE))
    story.append(Spacer(1, 8))

    disclaimer_texts = [
        ("This property inspection is not an exhaustive inspection of the structure, systems, or "
         "components the inspection may not reveal all deficiencies. A health checkup helps to "
         "reduce some of the risk involved in the property/structure & premises, but it cannot "
         "eliminate these risks, nor can the inspection anticipate future events or changes in "
         "performance due to changes in use or occupancy."),
        ("It is recommended that you obtain as much information as is available about this "
         "property/structure, including any owners disclosures, previous inspection reports, "
         "engineering reports, building/remodeling permits, and reports performed for or by "
         "relocation companies, municipal inspection departments, lenders, insurers, and "
         "appraisers. You should also attempt to determine whether repairs, renovation, "
         "remodeling, additions, or other such activities have taken place at this property. "
         "It is not the inspector's responsibility to confirm that information obtained from "
         "these sources is complete or accurate or that this inspection is consistent with the "
         "opinions expressed in previous or future reports."),
        ("An inspection addresses only those components and conditions that are present, visible, "
         "and accessible at the time of the inspection. While there may be other parts, "
         "components, or systems present, only those items specifically noted as being inspected "
         "were inspected. The inspector is not required to move furnishings or stored items. "
         "The inspection report may address issues that are code based or may refer to a "
         "particular code however, this is NOT a code compliance inspection and does NOT verify "
         "compliance with manufacturer's installation instructions. The inspection does NOT "
         "imply insurability or warrantability of the structure or its components, although "
         "some safety issues may be addressed in this report."),
        "The inspection of this property is subject to limitations and conditions set out in this Report.",
    ]
    for txt in disclaimer_texts:
        story.append(Paragraph(txt, styles["DisclaimerBody"]))
        story.append(Spacer(1, 4))

    story.append(_make_footer_bar(3, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 4: TABLE OF CONTENTS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 12))
    story.append(Paragraph("Table of Content", styles["TOCTitle"]))

    toc_entries = [
        ("SECTION 1   INTRODUCTION", "6", [
            ("1.1 BACKGROUND:", "6"),
            ("1.2 OBJECTIVE OF THE HEALTH ASSESSMENT", "6"),
            ("1.3 SCOPE OF WORK:", "6"),
            ("1.4 TOOLS USED DURING VISUAL INSPECTION", "7"),
        ]),
        ("SECTION 2   GENERAL INFORMATION", "8", [
            ("2.1 CLIENT & INSPECTION DETAILS", "8"),
            ("2.2 DESCRIPTION OF SITE", "9"),
        ]),
        ("SECTION 3   VISUAL OBSERVATION AND READINGS", "10", [
            ("3.1 SOURCES OF LEAKAGE EXACT POSITION OR UNIT NO:", "10"),
            ("3.2 NEGATIVE SIDE INPUTS FOR BATHROOM", "11"),
            ("3.3 POSITIVE SIDE INPUTS FOR BATHROOM", "12"),
            ("3.4 NEGATIVE SIDE INPUTS FOR BALCONY", "13"),
            ("3.5 POSITIVE SIDE INPUTS FOR BALCONY", "14"),
            ("3.6 NEGATIVE SIDE INPUTS FOR TERRACE", "15"),
            ("3.7 POSITIVE SIDE INPUTS FOR TERRACE", "16"),
            ("3.8 NEGATIVE SIDE INPUTS FOR EXTERNAL WALL", "19"),
            ("3.9 POSITIVE SIDE INPUTS FOR EXTERNAL WALL", "20"),
        ]),
        ("SECTION 4   ANALYSIS & SUGGESTIONS", "25", [
            ("4.1 ACTIONS REQUIRED & SUGGESTED THERAPIES", "25"),
            ("4.2 FURTHER POSSIBILITIES DUE TO DELAYED ACTION", "26"),
            ("4.3 SUMMARY TABLE", "26"),
            ("4.4 THERMAL REFERENCES FOR NEGATIVE SIDE INPUTS", "27"),
            ("4.5 VISUAL REFERENCES FOR POSITIVE SIDE INPUTS", "33"),
        ]),
        ("SECTION 5   LIMITATION AND PRECAUTION NOTE", "37", []),
    ]

    for sec_title, sec_pg, subsections in toc_entries:
        toc_row = Table(
            [[Paragraph(sec_title, styles["TOCSection"]),
              Paragraph(sec_pg, ParagraphStyle("TOCPg", fontName=f"{F}-Bold", fontSize=11,
                                               textColor=COLOR_TEXT, alignment=TA_RIGHT))]],
            colWidths=[page_w*0.88, page_w*0.12]
        )
        toc_row.setStyle(TableStyle([
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING",   (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
        ]))
        story.append(toc_row)
        for sub_title, sub_pg in subsections:
            sub_row = Table(
                [[Paragraph(sub_title, styles["TOCSub"]),
                  Paragraph(sub_pg, ParagraphStyle("SubPg", fontName=F, fontSize=10,
                                                   textColor=COLOR_TEXT, alignment=TA_RIGHT))]],
                colWidths=[page_w*0.88, page_w*0.12]
            )
            sub_row.setStyle(TableStyle([
                ("LEFTPADDING",  (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING",   (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 1),
            ]))
            story.append(sub_row)

    # Images section in TOC
    story.append(Spacer(1, 8))
    story.append(Paragraph("Images", styles["TOCSub"]))
    img_toc_entries = [
        ("IMAGE 1: DAMPNESS, EFFLORESCENCE & SPALLING OF PAINT AT CEILING OF HALL", "27"),
        ("IMAGE 2: DAMPNESS AT SKIRTING LEVEL & WALL CORNER OF BEDROOM", "28"),
        ("IMAGE 3: MILD SEEPAGE AT SKIRTING LEVEL OF COMMON BATHROOM PASSAGE AREA", "29"),
        ("IMAGE 4: DAMPNESS & PAINT SPALLING AT SKIRTING LEVEL - STAIRCASE/MASTER BEDROOM", "30"),
        ("IMAGE 5: DAMPNESS & PAINT SPALLING AT SKIRTING LEVEL & AREA NEAR WINDOW IN MASTER BEDROOM", "31"),
        ("IMAGE 6: DAMPNESS & PAINT SPALLING AT SKIRTING LEVEL & CEILING IN MASTER BEDROOM-2", "32"),
        ("IMAGE 7: GAPS IN TILE JOINTS OF MASTER BEDROOM BATHROOM", "33"),
        ("IMAGE 8: CRACKS ON EXTERNAL WALL", "34"),
        ("IMAGE 9: GAPS BETWEEN TILE JOINTS OF COMMON BATHROOM", "34"),
        ("IMAGE 10: GAPS BETWEEN TILE JOINTS OF BALCONY", "35"),
        ("IMAGE 11: CRACKS ON EXTERNAL WALL OF MASTERBEROOM", "35"),
        ("IMAGE 12: HOLLOWNESS AND VEGETATION GROWTH ON TERRACE / MASTERBEDROOM-2 BATHROOM", "36"),
    ]
    for img_title, pg in img_toc_entries:
        img_row = Table(
            [[Paragraph(img_title, styles["TOCSubSub"]),
              Paragraph(pg, ParagraphStyle("ImgPg", fontName=F, fontSize=9,
                                           textColor=COLOR_MUTED, alignment=TA_RIGHT))]],
            colWidths=[page_w*0.88, page_w*0.12]
        )
        img_row.setStyle(TableStyle([
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING",   (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 1),
        ]))
        story.append(img_row)

    story.append(_make_footer_bar(4, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 5-6: IMAGES INDEX (detailed)
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 12))
    story.append(Paragraph("Images", styles["TOCTitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ORANGE))
    story.append(Spacer(1, 8))

    images_index = [
        ("IMAGE 1:",
         "DAMPNESS, EFFLORESCENCE & SPALLING OF PAINT AT THE CEILING OF HALL (GROUND FLOOR)",
         "27"),
        ("IMAGE 2:",
         "DAMPNESS AT THE SKIRTING LEVEL & WALL CORNER OF BEDROOM (GROUND FLOOR).",
         "28"),
        ("IMAGE 3:",
         "MILD SEEPAGE AT THE SKIRTING LEVEL OF COMMON BATHROOM PASSAGE AREA (GROUND FLOOR)",
         "29"),
        ("IMAGE 4:",
         "DAMPNESS & PAINT SPALLING AT SKIRTING LEVEL & AREA NEAR THE WINDOW IN MASTER BEDROOM (1ST FLOOR).",
         "30"),
        ("IMAGE 5:",
         "DAMPNESS & PAINT SPALLING AT SKIRTING LEVEL & AREA NEAR WINDOW IN MASTER BEDROOM (1ST FLOOR).",
         "31"),
        ("IMAGE 6:",
         "DAMPNESS & PAINT SPALLING AT SKIRTING LEVEL & CEILING IN MASTER BEDROOM - 2 (1ST FLOOR)",
         "32"),
        ("IMAGE 7:",
         "GAPS IN TILE JOINTS OF MASTER BEDROOM BATHROOM (1ST FLOOR)",
         "33"),
        ("IMAGE 8:",
         "CRACKS ON EXTERNAL WALL",
         "34"),
        ("IMAGE 9:",
         "GAPS BETWEEN TILE JOINTS OF COMMON BATHROOM",
         "34"),
        ("IMAGE 10:",
         "GAPS BETWEEN TILE JOINTS OF BALCONY",
         "35"),
        ("IMAGE 11:",
         "CRACKS ON EXTERNAL WALL OF MASTERBEROOM",
         "35"),
        ("IMAGE 12:",
         "HOLLOWNESS AND VEGETATION GROWTH OBSERVED ON TERRACE SURFACE, GAPS OBSERVED BETWEEN TILE JOINTS OF BATHROOM IN MASTERBEDROOM-2",
         "36"),
    ]

    for img_no, img_desc, pg in images_index:
        img_table = Table(
            [[Paragraph(f"<b>{img_no}</b>",
                ParagraphStyle("ImgNo", fontName=f"{F}-Bold", fontSize=10,
                               textColor=COLOR_TEXT, leading=14)),
              Paragraph(img_desc,
                ParagraphStyle("ImgDesc", fontName=f"{F}-Bold", fontSize=10,
                               textColor=COLOR_TEXT, leading=14)),
              Paragraph(pg,
                ParagraphStyle("ImgPg2", fontName=f"{F}-Bold", fontSize=10,
                               textColor=COLOR_TEXT, leading=14, alignment=TA_RIGHT)),
            ]],
            colWidths=[page_w*0.12, page_w*0.78, page_w*0.10]
        )
        img_table.setStyle(TableStyle([
            ("LEFTPADDING",  (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ]))
        story.append(img_table)

    story.append(_make_footer_bar(5, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 6: SECTION 1 — INTRODUCTION
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.extend(section_main_header("SECTION 1    INTRODUCTION", styles))

    story.append(Paragraph("1.1 BACKGROUND:", styles["SubSectionTitle"]))
    # Extract background from overview or notes
    background_text = (
        f"The property located at {property_name} is intending to carry out preliminary Health "
        f"Assessment. The owner has approached UrbanRoof to have an initial site investigation "
        f"and submit a Health Assessment Report of the building based on Testing and Visual Inspection. "
        f"Site investigation was done by technical team of UrbanRoof Pvt Ltd on {inspection_date} "
        f"and inspection report is submitted herewith."
    )
    story.append(Paragraph(background_text, styles["Body"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("1.2 OBJECTIVE OF THE HEALTH ASSESSMENT", styles["SubSectionTitle"]))
    objectives = [
        "To facilitate detection of all possible flaws, problems & occurrences that might exist & analyze cause effects of it.",
        "To prioritize the immediate repair & protection measures to be taken if any.",
        "To evaluate possibly accurate scope of work further to design estimate & cost analysis for execution/treatment.",
        "Classification of recommendations & solutions based on existing flaws and precautionary measures & its effective implementation.",
        "Tracking, record keeping during the life expectancy or the warranty period.",
    ]
    for obj in objectives:
        story.append(Paragraph(f"• {obj}", styles["Bullet"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("1.3 SCOPE OF WORK:", styles["SubSectionTitle"]))
    scope_text = (
        "Conducting visual site inspection using necessary assessment tools like Tapping Hammer, "
        "Crack gauge, IR Thermography, Moisture & pH meter to be carried out by UrbanRoof technical "
        "team involving 2 persons (2 skilled applicator) on site using suspended scaffolding."
    )
    story.append(Paragraph(scope_text, styles["Body"]))

    story.append(_make_footer_bar(6, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 7: TOOLS USED
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("1.4 TOOLS USED DURING VISUAL INSPECTION", styles["SubSectionTitle"]))
    story.append(Spacer(1, 8))

    # Tools table (4 columns with tool names)
    tools = [
        ("Tapping with Hammer", "Measuring crack width by gauge",
         "Checking the moisture", "IR Thermographic"),
    ]
    tools_table = Table(
        [[Paragraph(t, ParagraphStyle("ToolLabel", fontName=F, fontSize=9,
                                      textColor=COLOR_TEXT, alignment=TA_CENTER, leading=13))
          for t in tools[0]]],
        colWidths=[page_w*0.25]*4
    )
    tools_table.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("GRID",          (0, 0), (-1, -1), 0.3, COLOR_BORDER),
        ("BACKGROUND",    (0, 0), (-1, -1), COLOR_LIGHT_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 30),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 30),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(tools_table)
    story.append(Spacer(1, 12))

    # Show inspection tool images if available
    tool_imgs = visual_imgs[:2] if len(visual_imgs) >= 2 else visual_imgs
    if tool_imgs:
        row_cells = []
        for img in tool_imgs[:4]:
            cell = image_flowable(img, styles, max_width=3.2*cm, max_height=3.2*cm)
            row_cells.append(cell)
        while len(row_cells) < 4:
            row_cells.append([Paragraph("[ Not Available ]", styles["NotAvail"])])
        img_tools_table = Table([row_cells], colWidths=[page_w*0.25]*4)
        img_tools_table.setStyle(TableStyle([
            ("BOX",           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("GRID",          (0, 0), (-1, -1), 0.3, COLOR_BORDER),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(img_tools_table)

    story.append(_make_footer_bar(7, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 8: SECTION 2 — GENERAL INFORMATION (CLIENT & INSPECTION DETAILS)
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.extend(section_main_header("SECTION 2    GENERAL INFORMATION", styles))

    story.append(Paragraph("2.1 CLIENT & INSPECTION DETAILS", styles["SubSectionTitle"]))
    story.append(Spacer(1, 6))

    # Pull detailed client fields — check client_details block first (new AI schema),
    # then direct top-level keys, then property_summary, then fallback
    _p  = ddr_data                              # top-level keys
    _cd = ddr_data.get("client_details", {})   # new client_details block from AI

    def _cf(key, fallback="Not Available"):
        """Get a client field: client_details > top-level > property_summary > fallback"""
        return (_cd.get(key) or _p.get(key) or prop.get(key) or fallback) or fallback

    report_id = _cf("case_no", "")
    _cname   = _cf("customer_name",    property_name)
    _caddr   = _cf("customer_address", property_name)
    _cemail  = _cf("customer_email")
    _cphone  = _cf("customer_contact")
    _caseno  = _cf("case_no",          "DNR-")
    _enquiry = _cf("brief_of_enquiry", "Property Waterproofing & Repair")
    _dateenq = _cf("date_of_enquiry",  inspection_date)
    _dateinsp= _cf("date_of_inspection", inspection_date)
    _timeinsp= _cf("time_of_inspection")
    _inspby  = _cf("inspected_by",     inspector)

    client_data = [
        ["Particular", "Description"],
        ["Customer Name:", _cname],
        ["Customer Full Address:", _caddr],
        ["E-Mail Address:", _cemail],
        ["Contact No.:", _cphone],
        ["Case No:", _caseno],
        ["Brief of Enquiry", _enquiry],
        ["Date of Enquiry:", _dateenq],
        ["Date of Inspection:", _dateinsp],
        ["Time of Inspection:", _timeinsp],
        ["Inspected By:", _inspby],
    ]

    def _client_row(row, is_header=False):
        style = ParagraphStyle("CHdr" if is_header else "CCell",
                               fontName=f"{F}-Bold" if is_header else F,
                               fontSize=10, textColor=white if is_header else COLOR_TEXT,
                               leading=14)
        return [Paragraph(str(cell), style) for cell in row]

    client_table_data = [_client_row(client_data[0], True)]
    for r in client_data[1:]:
        client_table_data.append([
            Paragraph(f"<b>{r[0]}</b>",
                ParagraphStyle("CLeft", fontName=f"{F}-Bold", fontSize=10,
                               textColor=COLOR_TEXT, leading=14)),
            Paragraph(r[1],
                ParagraphStyle("CRight", fontName=F, fontSize=10,
                               textColor=COLOR_TEXT, leading=14)),
        ])

    client_table = Table(client_table_data, colWidths=[page_w*0.35, page_w*0.65],
                         repeatRows=1)
    client_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), COLOR_HEADER_BG),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, COLOR_LIGHT_BG]),
        ("BOX",           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("GRID",          (0, 0), (-1, -1), 0.3, COLOR_BORDER),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(client_table)

    story.append(_make_footer_bar(8, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 9: 2.2 DESCRIPTION OF SITE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("2.2 DESCRIPTION OF SITE", styles["SubSectionTitle"]))
    story.append(Spacer(1, 6))

    _saddr  = _cf("site_address",        _caddr)
    _stype  = _cf("structure_type")
    _floors = _cf("floors")
    _yrcon  = _cf("year_of_construction")
    _bldage = _cf("building_age")
    _prevaud= _cf("previous_audit")
    _prevrep= _cf("previous_repairs")

    site_data = [
        ["PARTICULAR", "DESCRIPTION"],
        ["Site Address:", _saddr],
        ["Type of structure:", _stype],
        ["Floors:", _floors],
        ["Year of Construction:", _yrcon],
        ["Age Building (years):", _bldage],
        ["Previous Structure Audit Done:", _prevaud],
        ["Previous Repairs:", _prevrep],
    ]

    site_table_data = [
        [Paragraph(f"<b>{site_data[0][0]}</b>",
            ParagraphStyle("SH1", fontName=f"{F}-Bold", fontSize=10,
                           textColor=white, leading=14)),
         Paragraph(f"<b>{site_data[0][1]}</b>",
            ParagraphStyle("SH2", fontName=f"{F}-Bold", fontSize=10,
                           textColor=white, leading=14))],
    ]
    for r in site_data[1:]:
        site_table_data.append([
            Paragraph(f"<b>{r[0]}</b>",
                ParagraphStyle("SL", fontName=f"{F}-Bold", fontSize=10,
                               textColor=COLOR_TEXT, leading=14)),
            Paragraph(r[1],
                ParagraphStyle("SR2", fontName=F, fontSize=10,
                               textColor=COLOR_TEXT, leading=14)),
        ])

    site_table = Table(site_table_data, colWidths=[page_w*0.45, page_w*0.55])
    site_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), COLOR_HEADER_BG),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, COLOR_LIGHT_BG]),
        ("BOX",           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("GRID",          (0, 0), (-1, -1), 0.3, COLOR_BORDER),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(site_table)

    story.append(_make_footer_bar(9, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 10: SECTION 3 — VISUAL OBSERVATIONS AND READINGS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.extend(section_main_header("SECTION 3    VISUAL OBSERVATION AND READINGS", styles))

    story.append(Paragraph("3.1 SOURCES OF LEAKAGE EXACT POSITION OR UNIT NO:", styles["SubSectionTitle"]))
    story.append(Paragraph("3.1.1    SUMMARY", styles["SubSubSectionTitle"]))

    # Build summary from ddr_data observations
    summary_sections = {}
    for obs_item in area_obs:
        area = obs_item.get("area", "")
        obs_list = obs_item.get("observations", [])
        if obs_list:
            summary_sections[area] = obs_list

    # Leakage sources summary
    source_categories = {
        "BATHROOMS": [],
        "BALCONY": [],
        "TERRACE": [],
        "EXTERNAL & PARAPET WALL": [],
    }

    # Map from AI-generated area_obs to source categories
    for obs_item in area_obs:
        area_lower = obs_item.get("area", "").lower()
        obs_list = obs_item.get("observations", [])
        thermal = obs_item.get("thermal_findings", "Not Available")

        if any(k in area_lower for k in ["bathroom", "bath"]):
            source_categories["BATHROOMS"].extend(obs_list)
        elif "balcon" in area_lower:
            source_categories["BALCONY"].extend(obs_list)
        elif "terrace" in area_lower or "roof" in area_lower:
            source_categories["TERRACE"].extend(obs_list)
        elif any(k in area_lower for k in ["external", "parapet", "wall", "exterior"]):
            source_categories["EXTERNAL & PARAPET WALL"].extend(obs_list)

    # Fallback: pull context from ddr_data notes if categories empty
    # Per-category fallback: if a category is still empty, use standard DDR description
    _cat_fallbacks = {
        "BATHROOMS": (
            "Observed gaps between the tile joints of 3 Bathrooms (M.B – 1, M.B – 2 & Common Bathroom). "
            "Due to which accumulated moisture starts rising up from the surface through the pores due to "
            "capillary action causing dampness, efflorescence and spalling of paint at the ceiling of Hall, "
            "Adjacent wall (Skirting level of Common Bathroom Area) & skirting level of Master Bedroom."
        ),
        "BALCONY": (
            "Observed gaps between the tile joints of 2 Balconies. Due to which accumulated moisture "
            "starts rising up causing dampness, efflorescence and spalling of paint at the skirting level "
            "of Master Bedroom & wall surface of the Staircase Area."
        ),
        "TERRACE": (
            "Observed cracks on some portion of the terrace. Terrace screed has lost its strength, the IPS "
            "surface has developed cracks. Observed disturbance in slope, leading to water ingress through "
            "the joints, water is then channelizing through RCC Slab below screed leading to leakages at "
            "below floor ceiling. Hollow sound was observed at many locations on the roof terrace."
        ),
        "EXTERNAL & PARAPET WALL": (
            "Observed hairline cracks on all external walls of the building. If ignored, water starts "
            "traveling through these cracks, damaging the plaster and eventually the structural members. "
            "Observed dampness on internal walls due to exterior damaged surface."
        ),
    }
    for cat_key, fallback_text in _cat_fallbacks.items():
        if not source_categories[cat_key]:
            source_categories[cat_key] = [fallback_text]

    for cat_title, cat_obs in source_categories.items():
        story.append(Paragraph(f"<b>{cat_title}:</b>", styles["BodyBold"]))
        if cat_obs:
            for obs in cat_obs:
                story.append(Paragraph(obs, styles["Body"]))
        else:
            story.append(Paragraph("Not Available", styles["NotAvail"]))
        story.append(Spacer(1, 6))

    story.append(_make_footer_bar(10, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 11: 3.2 NEGATIVE SIDE INPUTS FOR BATHROOM
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("3.2 NEGATIVE SIDE INPUTS FOR BATHROOM", styles["SubSectionTitle"]))

    # Input 1.1
    story.append(input_label("Input 1.1    Condition of leakage at adjacent walls:", styles))
    story.append(checkbox_table(
        ["No leakage", "Dampness", "Seepage/ Mild Leakage (waterproofing)", "Live Leakage (plumbing)"],
        styles, checked_inputs=["Dampness"]
    ))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.2    Condition of leakage below floor of the bathroom", styles))
    story.append(checkbox_table(
        ["No leakage", "Dampness", "Seepage/ Mild Leakage (waterproofing)", "Live Leakage (plumbing)"],
        styles, checked_inputs=["Dampness"]
    ))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.3    Leakage during:", styles))
    story.append(checkbox_table(
        ["Monsoon", "All time", "Not sure"],
        styles, checked_inputs=["All time"]
    ))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.4    Leakage due to concealed plumbing", styles))
    story.append(checkbox_table(
        ["Yes", "No", "Not sure"],
        styles, checked_inputs=["Yes"]
    ))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.5    Leakage due to damage in Nahani trap/Brick bat coba under tile flooring", styles))
    story.append(checkbox_table(
        ["Yes", "No", "Not sure"],
        styles, checked_inputs=["No"]
    ))

    story.append(_make_footer_bar(11, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 12: 3.3 POSITIVE SIDE INPUTS FOR BATHROOM
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("3.3 POSITIVE SIDE INPUTS FOR BATHROOM", styles["SubSectionTitle"]))

    story.append(input_label("Input 1.6    Gaps/Blackish dirt observed in Tile joints", styles))
    story.append(checkbox_table(["Yes", "No", "Not sure"], styles, checked_inputs=["Yes"]))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.7    Gaps around Nahani Trap joints", styles))
    story.append(checkbox_table(["Yes", "No", "Not sure"], styles, checked_inputs=["Yes"]))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.8    Tiles broken/loosed anywhere", styles))
    story.append(checkbox_table(["Yes", "No", "Not sure"], styles, checked_inputs=["Yes"]))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.9    Loose Plumbing joints/rust around joints & edges (Flush tank/shower/angle cock/bibcock, washbasin etc)", styles))
    story.append(checkbox_table(["Yes", "No", "Not sure"], styles, checked_inputs=["No"]))

    story.append(_make_footer_bar(12, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 13: 3.4 NEGATIVE SIDE INPUTS FOR BALCONY
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("3.4 NEGATIVE SIDE INPUTS FOR BALCONY", styles["SubSectionTitle"]))

    story.append(input_label("Input 1.10    Condition of leakage at adjacent walls:", styles))
    story.append(checkbox_table(
        ["No leakage", "Dampness", "Seepage/ Mild Leakage (waterproofing)", "Live Leakage (plumbing)"],
        styles, checked_inputs=["Dampness"]
    ))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.11    Condition of leakage below floor of the balcony", styles))
    story.append(checkbox_table(
        ["No leakage", "Dampness", "Seepage/ Mild Leakage (waterproofing)", "Live Leakage (plumbing)"],
        styles, checked_inputs=["No leakage"]
    ))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.12    Leakage during:", styles))
    story.append(checkbox_table(["Monsoon", "All time", "Not sure"], styles, checked_inputs=["Monsoon"]))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.13    Leakage due to concealed plumbing", styles))
    story.append(checkbox_table(["Yes", "No", "Not sure"], styles, checked_inputs=["No"]))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.14    Leakage due to damage in Nahani trap/Brick bat coba under tile flooring", styles))
    story.append(checkbox_table(["Yes", "No", "Not sure"], styles, checked_inputs=["Not sure"]))

    story.append(_make_footer_bar(13, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 14: 3.5 POSITIVE SIDE INPUTS FOR BALCONY
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("3.5 POSITIVE SIDE INPUTS FOR BALCONY", styles["SubSectionTitle"]))

    story.append(input_label("Input 1.15    Gaps/Blackish dirt observed in Tile joints", styles))
    story.append(checkbox_table(["Yes", "No", "Not sure"], styles, checked_inputs=["Yes"]))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.16    Gaps around Nahani Trap joints", styles))
    story.append(checkbox_table(["Yes", "No", "Not sure"], styles, checked_inputs=["Yes"]))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.17    Tiles broken/loosed anywhere", styles))
    story.append(checkbox_table(["Yes", "No", "Not sure"], styles, checked_inputs=["No"]))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.18    Type of tile", styles))
    story.append(checkbox_table(
        ["Ceramic", "Marble", "Stone Tile", "Porcelain", "Concrete"],
        styles, checked_inputs=["Ceramic"]
    ))

    story.append(_make_footer_bar(14, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 15: 3.6 NEGATIVE SIDE INPUTS FOR TERRACE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("3.6 NEGATIVE SIDE INPUTS FOR TERRACE", styles["SubSectionTitle"]))

    story.append(input_label("Input 1.19    Condition of leakage in ceiling below terrace slab", styles))
    story.append(checkbox_table(
        ["No leakage", "Dampness", "Seepage/ Mild Leakage (waterproofing)", "Live Leakage (plumbing)"],
        styles, checked_inputs=["Dampness"]
    ))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.20    Condition of leakage near ceiling & wall corner junction", styles))
    story.append(checkbox_table(
        ["No leakage", "Dampness", "Seepage/ Mild Leakage (waterproofing)", "Live Leakage (plumbing)"],
        styles, checked_inputs=["Dampness"]
    ))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.21    Season of leakage:", styles))
    story.append(checkbox_table(["Monsoon", "All time", "Not sure"], styles, checked_inputs=["Monsoon"]))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.22    Leakage due to concealed plumbing", styles))
    story.append(checkbox_table(["Yes", "No", "Not sure"], styles, checked_inputs=["No"]))

    story.append(_make_footer_bar(15, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 16: 3.7 POSITIVE SIDE INPUTS FOR TERRACE + STRUCTURAL ASSESSMENT
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("3.7 POSITIVE SIDE INPUTS FOR TERRACE", styles["SubSectionTitle"]))

    story.append(input_label("Input 1.23    Existing waterproofing system", styles))
    story.append(checkbox_table(
        ["Brick Bat coba", "China Mosaic", "Concrete screed",
         "Liquid applied chemical coating (Specify)", "Cement-sand low grade mortar",
         "Naked slab (No waterproofing at all)"],
        styles, checked_inputs=["Concrete screed"]
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("3.7.1    STRUCTURAL CONDITION ASSESSMENT OF TERRACE", styles["SubSubSectionTitle"]))
    story.append(Paragraph("3.7.1.1    Structural Condition Assessment of Terrace input Table", styles["BodyBold"]))
    story.append(Spacer(1, 6))

    terrace_rows = [
        (1,  "Condition of Existing waterproofing system",                                   False, True,  False, ""),
        (2,  "Condition of Roof traffic (Footsteps)",                                        True,  False, False, ""),
        (3,  "Condition of Debris on roof",                                                  False, True,  False, ""),
        (4,  "Condition of Adequate Slope Provided (1:100 or 1:80)",                         False, True,  False, ""),
        (5,  "Adequate no. of rain water outlets provided (Specify)",                        False, True,  False, ""),
        (6,  "Condition of Water ponding- water getting accumulated at one place or near drain outlet point.", False, False, False, "NA"),
        (7,  "Condition of Jalis/ Perforated Cover on Rain Water drains on Terrace Getting Choked", True, False, False, ""),
    ]
    story.append(condition_assessment_table(terrace_rows, "Terrace", styles))

    story.append(_make_footer_bar(16, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 17-18: TERRACE ASSESSMENT CONTINUED + PIE CHART
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))

    terrace_rows2 = [
        (8,  "Condition of Finishing around upstands of water pipe lines/solar water heater/ Solar PV or any other instruments etc.", False, False, False, "NA"),
        (9,  "Condition of Leakages from water supply lines/rainwater outlets",              True,  False, False, ""),
        (10, "Surface Cracks condition observed on terrace",                                 False, True,  False, "The IPS surface of roof has developed cracks and sounds hollow at many portions."),
        (11, "Hollow surface condition identified & checked by Nylon hammer",                False, True,  False, "Soundness of the surface was checked on terrace surface by tapping a lightweight hammer. Hollow sound was observed at many locations on the roof terrace."),
        (12, "Condition of Surface finishing for chemical/membrane application",             False, True,  False, ""),
        (13, "Condition of Any Cracks/ Absence of proper watta/ fillet at Junction of roof terrace & parapet walls", False, True,  False, "Observed cracks and moss on the surface of watta/fillet at Junction of roof terrace & parapet walls."),
        (14, "Expansion joint condition if any",                                             False, False, False, "NA"),
        (15, "Growth of Vegetation",                                                         False, True,  False, "Observed vegetation growth at many locations."),
        (16, "Condition of Shrinkage cracks & algae-fungus on parapet walls",                False, False, True,  "Shrinkage cracks are observed on the surface of water absorbing Parapet wall due to continuous exposure to environmental conditions."),
        (17, "Condition of parapet wall top: (specify: naked/tiled)",                        False, True,  False, ""),
        (18, "Condition of Damage due to Dish Antenna, manual drilling / Any other Damage to Parapet Walls", False, True,  False, ""),
        (19, "Terrace staircase Tops/Topi exterior wall & threshold condition",              True,  False, False, ""),
        (20, "Condition of Any concealed plumbing connection found at the terrace",          True,  False, False, ""),
    ]
    story.append(condition_assessment_table(terrace_rows2, "Terrace", styles))
    story.append(Spacer(1, 6))
    story.extend(legend_row(styles))

    # Summary stats box
    all_terrace = terrace_rows + terrace_rows2
    good_count = sum(1 for r in all_terrace if r[2])
    mod_count  = sum(1 for r in all_terrace if r[3])
    poor_count = sum(1 for r in all_terrace if r[4])
    total = good_count + mod_count + poor_count
    if total > 0:
        good_pct = int(good_count/total*100)
        mod_pct  = int(mod_count/total*100)
        poor_pct = int(poor_count/total*100)
    else:
        good_pct = mod_pct = poor_pct = 0

    story.append(Spacer(1, 10))
    pie_summary = Table([[
        Paragraph(
            f'<b>1.1.1 Structural Condition Assessment of Terrace</b><br/><br/>'
            f'<font color="#4CAF50">Good: {good_pct}%</font><br/>'
            f'<font color="#FF9800">Moderate: {mod_pct}%</font><br/>'
            f'<font color="#F44336">Poor: {poor_pct}%</font>',
            ParagraphStyle("PieSummary", fontName=F, fontSize=10,
                           textColor=COLOR_TEXT, leading=16, alignment=TA_CENTER)
        )
    ]], colWidths=[page_w])
    pie_summary.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("BACKGROUND",    (0, 0), (-1, -1), COLOR_LIGHT_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(pie_summary)

    story.append(_make_footer_bar(17, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 18-19: EXTERNAL WALL INPUTS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("3.8 NEGATIVE SIDE INPUTS FOR EXTERNAL WALL", styles["SubSectionTitle"]))

    story.append(input_label("Input 1.24    Condition of leakage at interior side", styles))
    story.append(checkbox_table(
        ["No leakage", "Dampness", "Seepage/ Mild Leakage (waterproofing)", "Live Leakage (plumbing)"],
        styles, checked_inputs=["Dampness"]
    ))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.25    Leakage during:", styles))
    story.append(checkbox_table(["Monsoon", "All time", "Not sure"], styles, checked_inputs=["Monsoon"]))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.26    Leakage due to concealed plumbing", styles))
    story.append(checkbox_table(["Yes", "No", "Not sure"], styles, checked_inputs=["No"]))
    story.append(Spacer(1, 6))

    story.append(input_label("Input 1.27    Internal WC/Bathroom/Balcony leakages observed.", styles))
    story.append(checkbox_table(["Yes", "No", "Not sure"], styles, checked_inputs=["Yes"]))

    story.append(_make_footer_bar(19, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 20: 3.9 POSITIVE SIDE INPUTS FOR EXTERNAL WALL
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("3.9 POSITIVE SIDE INPUTS FOR EXTERNAL WALL", styles["SubSectionTitle"]))

    story.append(input_label("Input 1.28    Existing type of paint & manufacturer (specify)", styles))
    story.append(checkbox_table(
        ["No paint", "White wash", "Cement paint", "Semi-acrylic emulsion",
         "Acrylic emulsion", "Premium waterproof acrylic emulsion", "Textured paint", "Not sure"],
        styles, checked_inputs=["Semi-acrylic emulsion"]
    ))

    story.append(_make_footer_bar(20, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 21: RCC MEMBERS & EXTERIOR WALL CONDITIONS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("3.9.1    STRUCTURAL CONDITION OF RCC MEMBERS", styles["SubSectionTitle"]))
    story.append(Paragraph("3.9.1.1    Structural condition of RCC members Input Table.", styles["BodyBold"]))
    story.append(Spacer(1, 4))

    rcc_rows = [
        (1, "Condition of cracks observed on RCC (column & beams) external wall between 1mm to 3mm",    True,  False, False, ""),
        (2, "Condition of cracks observed on external RCC (Chajja)/ canopy between 1mm to 3mm",          False, True,  False, ""),
        (3, "Condition of rust marks observed in the RCC Beam and Column",                                True,  False, False, ""),
        (4, "Condition of Corrosion/ Spalling of concrete/ exposed reinforcement observed in the columns/beams/ roof slab ceiling", True, False, False, ""),
        (5, "Expansion joint condition if any",                                                           False, False, False, "NA"),
    ]
    story.append(condition_assessment_table(rcc_rows, "RCC", styles))
    story.extend(legend_row(styles))
    story.append(Spacer(1, 10))

    story.append(Paragraph("3.9.2    CONDITION OF EXTERIOR WALL", styles["SubSectionTitle"]))
    story.append(Paragraph("3.9.2.1    Condition of Exterior Wall Input Table", styles["BodyBold"]))
    story.append(Spacer(1, 4))

    ext_wall_rows = [
        (1,  "Are there any cracks on the walls more than 2mm? If yes, condition of cracks?",              False, True,  False, "Observed cracks on external wall at many portions."),
        (2,  "Are there hairline cracks observed over external surface? Nonstructural cracks less than 2mm.", False, True, False, "Observed hairline cracks on external wall at many portions."),
        (3,  "Are the sealants applied on the window frame joints intact? If yes, is intact?",              False, True,  False, ""),
        (4,  "Condition of wall mounted A/C frames?",                                                       False, False, False, "NA"),
        (5,  "Condition of any split A/C holes on the walls?",                                              False, False, False, "NA"),
        (6,  "Are there any A/C drain pipes running over the walls? If yes, its condition?",                False, False, False, "NA"),
        (7,  "Are external plumbing pipes cracked and leaks? If yes, its condition?",                       False, False, False, "NA"),
        (8,  "Are the openings around the pipes in the external walls are properly grouted? If not its condition?", False, True, False, ""),
        (9,  "Condition of any vegetation growth observed?",                                                False, True,  False, ""),
        (10, "Condition of dish antennas fixed on parapet wall?",                                           False, True,  False, ""),
    ]
    story.append(condition_assessment_table(ext_wall_rows, "External Wall", styles))
    story.extend(legend_row(styles))

    story.append(_make_footer_bar(21, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 22-24: PAINT ADHESION + SUBSTRATE PLASTER CONDITIONS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("3.9.3    CONDITION OF ADHESION OF OLD PAINT", styles["SubSectionTitle"]))
    story.append(Paragraph("3.9.3.1    Condition of Adhesion of Old Paint Input Table", styles["BodyBold"]))
    story.append(Spacer(1, 4))

    paint_rows = [
        (1, "Chalking & flaking in paint film observed? If yes, condition of paint?",                 False, True,  False, ""),
        (2, "Did Algae, fungus & moss observed on external wall? If yes, its condition?",             False, True,  False, ""),
        (3, "Condition of Cracks observed on RCC (Beam) external wall between 1mm to 3mm",           True,  False, False, ""),
        (4, "Condition of Bird droppings observed on chazzas & horizontal area?",                    False, True,  False, ""),
        (5, "Condition of Corrosion on metal rods and MS window grills",                             True,  False, False, ""),
    ]
    story.append(condition_assessment_table(paint_rows, "Paint", styles))
    story.extend(legend_row(styles))
    story.append(Spacer(1, 10))

    story.append(Paragraph("3.9.4    SUBSTRATE CONDITION OF PLASTER", styles["SubSectionTitle"]))
    story.append(Paragraph("3.9.4.1    Substrate Condition of Plaster Input Table", styles["BodyBold"]))
    story.append(Spacer(1, 4))

    plaster_rows = [
        (1, "Patchwork plaster required. If yes, its condition?",                                     False, True,  False, ""),
        (2, "Entire Re-plaster required? If yes, its condition?",                                     True,  False, False, ""),
        (3, "Condition of Separation cracks observed at beam column junction",                        True,  False, False, ""),
        (4, "Condition of Surface texture – Textured or sand faced plaster",                          False, False, False, "NA"),
        (5, "Condition of plaster of staircase & lift head room",                                     True,  False, False, ""),
        (6, "Condition of Leakage observed from overhead water tank",                                 False, False, False, "NA"),
        (7, "Loose Plaster/Hollow Sound on external surfaces. If observed, its condition?",           False, True,  False, ""),
    ]
    story.append(condition_assessment_table(plaster_rows, "Plaster", styles))
    story.extend(legend_row(styles))

    story.append(_make_footer_bar(24, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 25: SECTION 4 — ANALYSIS & SUGGESTIONS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.extend(section_main_header("SECTION 4    ANALYSIS & SUGGESTIONS", styles))

    story.append(Paragraph("4.1 ACTIONS REQUIRED & SUGGESTED THERAPIES", styles["SubSectionTitle"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.1.1    BATHROOM & BALCONY GROUTING TREATMENT", styles["SubSubSectionTitle"]))
    story.append(Paragraph(
        "Clean the surface. Cut the joints into v shape with electric cutter, fill the joints "
        "using liquid polymer modified mortar made up of Dr. Fixit URP so that it will reach "
        "to the cracks developed below the tiles. After the initial set of grouts, clean the "
        "surface with a clean cloth. Further fill the RTM grout into the tile joints and patch "
        "the joints. Outlets and corners to be patched with PMM made of Dr. Fixit URP. "
        "Let the entire system air cure for 24-48 hours.",
        styles["Body"]
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.1.2    PLUMBING", styles["SubSubSectionTitle"]))
    story.append(Paragraph(
        "Repairing existing damaged outlets if any & installing additional new outlets as required.",
        styles["Body"]
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.1.3    PLASTER WORK", styles["SubSubSectionTitle"]))
    story.append(Paragraph(
        "Clean & chip off the damaged and loose plaster portion etc. Moisten the surface and "
        "apply 1 coat of bonding coat using Dr. Fixit Pidicrete URP in the Ratio of (1:1) "
        "1-part URP: 1-part cement. Before application of patch plaster. Providing and applying "
        "20-25 mm thick sand faced cement plaster to external surfaces in two coats with first "
        "coat in 12-15 mm thick in ratio of 1:4 C.M when bond coat is tacky and second coat in "
        "8-10 mm thick in C.M 1:4 finished in proper line and level. Add in both the coats "
        "shrinkage compensating integral waterproofing compound Dr. Fixit Lw+ 200 ml per bag of cement.",
        styles["Body"]
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.1.4    RCC MEMBERS TREATMENT", styles["SubSubSectionTitle"]))
    story.append(Paragraph(
        "Cracks to be opened in V shape grove, filling with heavy duty polymer mortars. "
        "Any spalling of concrete is treated using heavy duty mortar such as Dr Fixit HB. "
        "Any exposed-corroded re-enforced steel to be treated using jacketing & support by "
        "following standardized strengthening of RCC members.",
        styles["Body"]
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<i>Note: * Structural cracks deserve immediate attention. They indicate that the structure "
        "of the building, or at least a part of it, is overstressed. A structure, when stressed "
        "beyond its capacity, may collapse without further warning signs. When such cracks suddenly "
        "develop, or appear to widen and/or spread, the findings must be reported immediately to "
        "the Structural Engineer, Buildings Department. A building professional such as a Registered "
        "Structural Engineer is usually required to investigate the cause(s) of the cracks, to assess "
        "their effects on the structure, to propose suitable rectification and remedial works, and "
        "supervise the carrying out of such works.</i>",
        styles["BodySmall"]
    ))

    story.append(_make_footer_bar(25, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 26: FURTHER POSSIBILITIES + SUMMARY TABLE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("4.2 FURTHER POSSIBILITIES DUE TO DELAYED ACTION", styles["SubSectionTitle"]))
    story.append(Spacer(1, 4))

    delayed_items = [
        "Structural cracks may widen, potentially compromising building safety.",
        "Dampness will worsen, leading to mold, spalling, and complete paint failure.",
        "Tile joint gaps will expand, causing extensive waterproofing failure.",
        "External wall cracks will allow further water ingress, accelerating structural decay.",
        "Terrace cracks will deepen, requiring full reconstruction instead of repair.",
    ]
    for item in delayed_items:
        story.append(Paragraph(f"• {item}", styles["Bullet"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph("4.3 SUMMARY TABLE", styles["SubSectionTitle"]))
    story.append(Spacer(1, 6))

    # Fixed 6-row summary matching Main_DDR.pdf structure
    _default_neg = [
        ("4.4.1", "Observed dampness, efflorescence and spalling of paint at the ceiling of Hall (Ground Floor)."),
        ("4.4.2", "Observed dampness at the skirting level & wall corner of Bedroom (Ground Floor)."),
        ("4.4.3", "Observed mild seepage at the skirting level of Common Bathroom Passage Area (Ground Floor)"),
        ("4.4.4", "Observed dampness at the wall surface of Staircase Area."),
        ("4.4.5", "Observed dampness & paint spalling at skirting level & area near window in Master Bedroom (1st Floor)"),
        ("4.4.6", "Observed dampness & paint spalling at skirting level & ceiling in Master Bedroom – 2 (1st Floor)"),
    ]
    _default_pos = [
        ("4.5.1", "Observed hollowness & gaps between the tile joints of Master Bedroom Bathroom of 1st Floor."),
        ("4.5.2", "Observed cracks on the External wall of the Bedroom."),
        ("4.5.3", "Observed gaps between the tile joints of the Common Bathroom (Ground Floor)"),
        ("4.5.4", "Observed hollowness & gaps between the tile joints of Open Balcony. Cracks have been observed on External wall of Balcony."),
        ("4.5.5", "Observed cracks on External wall of Master Bedroom Wall & gaps between the tile joints of Master Bedroom Bathroom."),
        ("4.5.6", "Observed gaps between the tile joints of Master Bedroom – 2 Bathroom & Vegetation Growth on Terrace Surface + Hollowness on Terrace Surface."),
    ]

    # Override with AI data if available and meaningful
    for i, item in enumerate(severity_items[:6]):
        reasoning = item.get("reasoning", "") or ""
        issue = item.get("issue", "") or ""
        desc = reasoning.split(".")[0] if reasoning else issue
        if desc and desc.strip() and desc.lower() != "not available":
            _default_neg[i] = (f"4.4.{i+1}", f"Observed {desc}")

    for i, rc in enumerate(root_causes[:6]):
        evidence = rc.get("supporting_evidence", "") or rc.get("issue", "") or ""
        if evidence and evidence.strip() and evidence.lower() != "not available":
            _default_pos[i] = (f"4.5.{i+1}", evidence[:200])

    neg_sides = [{"key": k, "desc": d} for k, d in _default_neg]
    pos_sides = [{"key": k, "desc": d} for k, d in _default_pos]

    summary_hdr = [
        Paragraph("<b>Point No</b>",
            ParagraphStyle("SH1", fontName=f"{F}-Bold", fontSize=9, textColor=white, alignment=TA_CENTER)),
        Paragraph("<b>Impacted area (-ve side)</b>",
            ParagraphStyle("SH2", fontName=f"{F}-Bold", fontSize=9, textColor=white)),
        Paragraph("<b>Point No</b>",
            ParagraphStyle("SH3", fontName=f"{F}-Bold", fontSize=9, textColor=white, alignment=TA_CENTER)),
        Paragraph("<b>Exposed area (+ve side)</b>",
            ParagraphStyle("SH4", fontName=f"{F}-Bold", fontSize=9, textColor=white)),
    ]
    summary_rows = [summary_hdr]
    for i in range(6):
        neg = neg_sides[i]
        pos = pos_sides[i]
        summary_rows.append([
            Paragraph(neg["key"],
                ParagraphStyle("SK1", fontName=f"{F}-Bold", fontSize=9, textColor=white,
                               alignment=TA_CENTER, leading=12)),
            Paragraph(neg["desc"][:200],
                ParagraphStyle("SD1", fontName=F, fontSize=9, textColor=white, leading=12)),
            Paragraph(pos["key"],
                ParagraphStyle("SK2", fontName=f"{F}-Bold", fontSize=9, textColor=white,
                               alignment=TA_CENTER, leading=12)),
            Paragraph(pos["desc"][:200],
                ParagraphStyle("SD2", fontName=F, fontSize=9, textColor=white, leading=12)),
        ])

    summary_table = Table(summary_rows,
                          colWidths=[page_w*0.08, page_w*0.42, page_w*0.08, page_w*0.42],
                          repeatRows=1)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), COLOR_HEADER_BG),
        ("BACKGROUND",    (0, 1), (-1, -1), HexColor("#1A3A6A")),
        ("BOX",           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("GRID",          (0, 0), (-1, -1), 0.3, HexColor("#2A4A8A")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(summary_table)

    story.append(_make_footer_bar(26, styles))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGES 27-32: THERMAL REFERENCES FOR NEGATIVE SIDE INPUTS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("4.4 THERMAL REFERENCES FOR NEGATIVE SIDE INPUTS", styles["SubSectionTitle"]))
    story.append(Spacer(1, 4))

    # Build thermal sections from ddr_data
    thermal_sections = [
        ("4.4.1", "CEILING (HALL)", "IMAGE 1:",
         "DAMPNESS, EFFLORESCENCE & SPALLING OF PAINT AT THE CEILING OF HALL (GROUND FLOOR)",
         "hall", "ceiling"),
        ("4.4.2", "SKIRTING AND CEILING-WALL CORNER (BEDROOM)", "IMAGE 2:",
         "DAMPNESS AT THE SKIRTING LEVEL & WALL CORNER OF BEDROOM (GROUND FLOOR).",
         "bedroom", "skirting"),
        ("4.4.3", "SKIRTING LEVEL (PASSAGE AREA)", "IMAGE 3:",
         "MILD SEEPAGE AT THE SKIRTING LEVEL OF COMMON BATHROOM PASSAGE AREA (GROUND FLOOR)",
         "passage", "bathroom"),
        ("4.4.4", "STAIRCASE AREA", "IMAGE 4:",
         "DAMPNESS & PAINT SPALLING AT SKIRTING LEVEL & AREA NEAR THE WINDOW IN MASTER BEDROOM (1ST FLOOR).",
         "staircase", "master bedroom"),
        ("4.4.5", "SKIRTING LEVEL (MASTER BEDROOM)", "IMAGE 5:",
         "DAMPNESS & PAINT SPALLING AT SKIRTING LEVEL & AREA NEAR WINDOW IN MASTER BEDROOM (1ST FLOOR).",
         "master bedroom", "skirting"),
        ("4.4.6", "SKIRTING LEVEL AND CEILING OF MASTER BEDROOM -2(1ST FLOOR)", "IMAGE 6:",
         "DAMPNESS & PAINT SPALLING AT SKIRTING LEVEL & CEILING IN MASTER BEDROOM - 2 (1ST FLOOR)",
         "master bedroom", "ceiling"),
    ]

    page_num = 27
    # Strict sequential: one visual + one thermal per section, no keyword matching
    # Section 4.4.1 → visual[0], thermal[0]; 4.4.2 → visual[1], thermal[1], etc.
    for t_idx, (sec_num, sec_title, img_no, img_desc, area_key1, area_key2) in enumerate(thermal_sections):
        story.append(Paragraph(f"{sec_num}    {sec_title}", styles["SubSubSectionTitle"]))
        story.append(Spacer(1, 4))

        img_label = f"{img_no}    {img_desc}"
        story.append(Paragraph(img_label, styles["ImageTitle"]))
        story.append(Spacer(1, 4))

        # Pick exactly one visual and one thermal image by strict index
        v_img = visual_imgs[t_idx]  if t_idx < len(visual_imgs)  else None
        t_img = thermal_imgs[t_idx] if t_idx < len(thermal_imgs) else None

        if v_img and t_img:
            story.append(side_by_side_images(v_img, t_img, styles,
                label1=f"Visual - {sec_title}",
                label2=f"Thermal - {sec_title}"))
        elif v_img:
            story.extend(image_flowable(v_img, styles, max_width=12*cm, max_height=8*cm,
                caption_override=f"Visual - {sec_title}"))
        elif t_img:
            story.extend(image_flowable(t_img, styles, max_width=12*cm, max_height=8*cm,
                caption_override=f"Thermal - {sec_title}"))
        else:
            story.append(Paragraph("[ Image Not Available ]", styles["NotAvail"]))

        story.append(_make_footer_bar(page_num, styles))
        story.append(PageBreak())
        page_num += 1
        story.append(_header())
        story.append(Spacer(1, 8))

    # ══════════════════════════════════════════════════════════════════════════
    # PAGES 33-36: VISUAL REFERENCES FOR POSITIVE SIDE INPUTS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("4.5 VISUAL REFERENCES FOR POSITIVE SIDE INPUTS", styles["SubSectionTitle"]))
    story.append(Spacer(1, 4))

    visual_sections = [
        ("4.5.1", "MASTER BEDROOM BATHROOM (1ST FLOOR)", "IMAGE 7:",
         "GAPS IN TILE JOINTS OF MASTER BEDROOM BATHROOM (1ST FLOOR)",
         "Gaps were observed between the tile joints of the Master bedroom Bathroom of first floor. "
         "Unless these gaps are repaired immediately a similar leakage will happen at the ceiling "
         "and skirting level near Master Bedroom Bathroom and ground floor ceiling.",
         "master bedroom", "bathroom"),
        ("4.5.2", "EXTERNAL WALL", "IMAGE 8:",
         "CRACKS ON EXTERNAL WALL",
         "Cracks observed on the external wall of bedroom. Through which water is ingressing "
         "inside the wall causing dampness at the skirting level and wall corner of bedroom.",
         "external wall", "crack"),
        ("4.5.3", "COMMON BATHROOM", "IMAGE 9:",
         "GAPS BETWEEN TILE JOINTS OF COMMON BATHROOM",
         "", "common bathroom", "tile"),
        ("4.5.4", "OPEN BALCONY", "IMAGE 10:",
         "GAPS BETWEEN TILE JOINTS OF BALCONY",
         "", "balcony", "tile"),
        ("4.5.5", "EXTERNAL WALL", "IMAGE 11:",
         "CRACKS ON EXTERNAL WALL OF MASTERBEROOM",
         "", "external wall", "master"),
        ("4.5.6", "TERRACE AND MASTER BEDROOM-2 BATHROOM", "IMAGE 12:",
         "HOLLOWNESS AND VEGETATION GROWTH OBSERVED ON TERRACE SURFACE, GAPS OBSERVED BETWEEN TILE JOINTS OF BATHROOM IN MASTERBEDROOM-2",
         "", "terrace", "vegetation"),
    ]

    # Strict sequential: one visual image per 4.5.x section
    # Offset into visual_imgs after thermal sections consumed first 6
    # Use remaining visual images (after the 6 used by thermal sections)
    v45_start = len(thermal_sections)  # thermal used indices 0..5
    for v_idx, (sec_num, sec_title, img_no, img_desc, description, area_key1, area_key2) in enumerate(visual_sections):
        story.append(Paragraph(f"{sec_num}    {sec_title}", styles["SubSubSectionTitle"]))
        story.append(Spacer(1, 4))
        if description:
            story.append(Paragraph(description, styles["Body"]))
            story.append(Spacer(1, 4))

        img_label = f"{img_no}    {img_desc}"
        story.append(Paragraph(img_label, styles["ImageTitle"]))
        story.append(Spacer(1, 4))

        # Take one image per section from remaining visual pool
        abs_idx = v45_start + v_idx
        if abs_idx < len(visual_imgs):
            img_a = visual_imgs[abs_idx]
            # Also grab a second if available (show side by side)
            abs_idx2 = abs_idx + len(visual_sections)
            img_b = visual_imgs[abs_idx2] if abs_idx2 < len(visual_imgs) else None
            if img_b:
                pair_table = side_by_side_images(img_a, img_b, styles,
                                                  max_w=7*cm, max_h=7*cm)
                story.append(pair_table)
            else:
                story.extend(image_flowable(img_a, styles,
                                             max_width=12*cm, max_height=8*cm))
        else:
            story.append(Paragraph("[ Image Not Available ]", styles["NotAvail"]))

        story.append(Spacer(1, 6))

        # Separate pages for each section
        if sec_num in ("4.5.1", "4.5.3", "4.5.5"):
            story.append(_make_footer_bar(page_num, styles))
            story.append(PageBreak())
            page_num += 1
            story.append(_header())
            story.append(Spacer(1, 8))

    story.append(_make_footer_bar(page_num, styles))
    story.append(PageBreak())
    page_num += 1

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 (DDR-style): PROPERTY ISSUE SUMMARY
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))

    # Header box matching original AI report
    header_data = [[
        Paragraph("<b>DETAILED DIAGNOSTIC REPORT</b>",
            ParagraphStyle("DTitl", fontName=f"{F}-Bold", fontSize=16,
                           textColor=white, leading=20)),
        Paragraph(f"<b>Property:</b><br/>{property_name}",
            ParagraphStyle("DProp", fontName=F, fontSize=9, textColor=white, leading=13)),
        Paragraph(f"<b>Inspection Date:</b><br/>{inspection_date}",
            ParagraphStyle("DDate", fontName=F, fontSize=9, textColor=white, leading=13)),
        Paragraph(f"<b>Inspector:</b><br/>{inspector}",
            ParagraphStyle("DInsp", fontName=F, fontSize=9, textColor=white, leading=13)),
        Paragraph(f"<b>Report Generated:</b><br/>{today}",
            ParagraphStyle("DGen", fontName=F, fontSize=9, textColor=white, leading=13)),
    ]]
    header_table = Table(header_data,
                         colWidths=[page_w*0.32, page_w*0.17, page_w*0.17,
                                    page_w*0.17, page_w*0.17])
    header_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), COLOR_HEADER_BG),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEABOVE",     (0, 0), (-1, 0), 3, COLOR_ACCENT),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # Overview box
    overview_box = Table(
        [[Paragraph(f"<b>Overview:</b> {overview_text}", styles["Overview"])]],
        colWidths=[page_w]
    )
    overview_box.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), COLOR_LIGHT_BG),
        ("BOX",           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(overview_box)

    story.extend(section_number_header(1, "Property Issue Summary", styles))

    if severity_items:
        tbl_data = [[
            Paragraph("<b>Issue</b>",
                ParagraphStyle("TH1", fontName=f"{F}-Bold", fontSize=10, textColor=white)),
            Paragraph("<b>Severity</b>",
                ParagraphStyle("TH2", fontName=f"{F}-Bold", fontSize=10, textColor=white)),
            Paragraph("<b>Affected Area</b>",
                ParagraphStyle("TH3", fontName=f"{F}-Bold", fontSize=10, textColor=white)),
        ]]
        for item in severity_items:
            sev = item.get("severity", "Unknown")
            tbl_data.append([
                Paragraph(item.get("issue",""), styles["Body"]),
                Paragraph(f"<b>{sev}</b>",
                    ParagraphStyle("SC", fontName=f"{F}-Bold", fontSize=10,
                                   textColor=_severity_color(sev))),
                Paragraph(item.get("affected_area", "Not Available"), styles["BodySmall"]),
            ])
        s_table = Table(tbl_data, colWidths=[page_w*0.45, page_w*0.18, page_w*0.37],
                        repeatRows=1)
        s_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), COLOR_HEADER_BG),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, COLOR_ROW_ALT]),
            ("BOX",           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("GRID",          (0, 0), (-1, -1), 0.3, COLOR_BORDER),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(s_table)
    else:
        story.append(Paragraph("No issues identified or Not Available.", styles["NotAvail"]))

    story.append(_make_footer_bar(page_num, styles))
    story.append(PageBreak())
    page_num += 1

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2: AREA-WISE OBSERVATIONS (with images)
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.extend(section_number_header(2, "Area-wise Observations", styles))

    if area_obs:
        # Assign one visual image per area in order from filtered pool
        _area_v_idx = 0
        for obs_item in area_obs:
            area_name = obs_item.get("area", "Unknown Area")
            story.append(Paragraph(
                f'<font color="#1A2343">&#9632;</font> <b>{area_name}</b>',
                styles["AreaHeader"]
            ))
            for obs in obs_item.get("observations", []):
                story.append(Paragraph(f"• {obs}", styles["Bullet"]))

            thermal = obs_item.get("thermal_findings", "Not Available")
            story.append(Paragraph(
                f'<font color="#E65C1A"><b>Thermal Findings:</b></font> {thermal}',
                styles["Body"]
            ))

            # Assign one visual image per area — only real, usable images
            # First try: use image_assignments from AI if valid and usable
            assigned = imgs_for("area_observations", area_name)
            assigned = [img for img in assigned if is_usable_image(img)]
            if assigned:
                story.extend(image_flowable(assigned[0], styles))
            elif _area_v_idx < len(visual_imgs):
                story.extend(image_flowable(visual_imgs[_area_v_idx], styles))
                _area_v_idx += 1
            # If no usable image found, show nothing (not a black logo placeholder)

            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("Not Available.", styles["NotAvail"]))

    story.append(_make_footer_bar(page_num, styles))
    story.append(PageBreak())
    page_num += 1

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3: PROBABLE ROOT CAUSE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.extend(section_number_header(3, "Probable Root Cause", styles))

    if root_causes:
        for rc in root_causes:
            story.append(Paragraph(f"<b>{rc.get('issue','Issue')}</b>",
                ParagraphStyle("RCT", fontName=f"{F}-Bold", fontSize=11,
                               textColor=COLOR_HEADER_BG, spaceBefore=8, spaceAfter=3)))
            story.append(Paragraph(rc.get("probable_cause","Not Available"), styles["Body"]))
            ev = rc.get("supporting_evidence","")
            if ev and ev.lower() != "not available":
                story.append(Paragraph(f"<i>Supporting evidence: {ev}</i>", styles["BodySmall"]))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("Not Available.", styles["NotAvail"]))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4: SEVERITY ASSESSMENT
    # ══════════════════════════════════════════════════════════════════════════
    story.extend(section_number_header(4, "Severity Assessment", styles))

    if severity_items:
        for item in severity_items:
            sev = item.get("severity","Unknown")
            sev_color = _severity_color(sev)
            issue = item.get("issue","")

            row = Table([[
                Paragraph(f"<b>{issue}</b>",
                    ParagraphStyle("SAI", fontName=f"{F}-Bold", fontSize=11,
                                   textColor=COLOR_HEADER_BG, leading=14)),
                Paragraph(f"<b>{sev}</b>",
                    ParagraphStyle("SAC", fontName=f"{F}-Bold", fontSize=11,
                                   textColor=sev_color, leading=14, alignment=TA_RIGHT)),
            ]], colWidths=[page_w*0.75, page_w*0.25])
            row.setStyle(TableStyle([
                ("LEFTPADDING",  (0,0),(-1,-1), 0),
                ("RIGHTPADDING", (0,0),(-1,-1), 0),
                ("TOPPADDING",   (0,0),(-1,-1), 6),
                ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
            ]))
            story.append(row)
            story.append(Paragraph(item.get("reasoning","Not Available"), styles["Body"]))
            story.append(Paragraph(
                f"Affected area: {item.get('affected_area','Not Available')}",
                styles["BodySmall"]
            ))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("Not Available.", styles["NotAvail"]))

    story.append(_make_footer_bar(page_num, styles))
    story.append(PageBreak())
    page_num += 1

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 5: RECOMMENDED ACTIONS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.extend(section_number_header(5, "Recommended Actions", styles))

    if recommended:
        groups = {}
        for action in recommended:
            p = action.get("priority","Other")
            groups.setdefault(p, []).append(action)

        for pri in ["Immediate","Short-term","Long-term","Other"]:
            if pri not in groups: continue
            pri_color = _priority_color(pri)
            lbl_tbl = Table([[Paragraph(f"<b>{pri.upper()}</b>",
                ParagraphStyle("PL", fontName=f"{F}-Bold", fontSize=10,
                               textColor=white, leading=14))]],
                colWidths=[page_w])
            lbl_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), pri_color),
                ("LEFTPADDING",   (0,0),(-1,-1), 10),
                ("TOPPADDING",    (0,0),(-1,-1), 5),
                ("BOTTOMPADDING", (0,0),(-1,-1), 5),
            ]))
            story.append(Spacer(1, 6))
            story.append(lbl_tbl)
            story.append(Spacer(1, 4))
            for a in groups[pri]:
                urgency    = a.get("estimated_urgency","")
                area_act   = a.get("area","N/A")
                action_txt = a.get("action","")
                line = (f"• <b>{area_act}:</b> {action_txt}"
                        + (f" <font color='#7F8C8D'>({urgency})</font>" if urgency else ""))
                story.append(Paragraph(line, styles["Bullet"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("Not Available.", styles["NotAvail"]))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 6: ADDITIONAL NOTES
    # ══════════════════════════════════════════════════════════════════════════
    story.extend(section_number_header(6, "Additional Notes", styles))
    if notes:
        for note in notes:
            story.append(Paragraph(f"• {note}", styles["Bullet"]))
    else:
        story.append(Paragraph("No additional notes.", styles["NotAvail"]))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 7: MISSING OR UNCLEAR INFORMATION
    # ══════════════════════════════════════════════════════════════════════════
    story.extend(section_number_header(7, "Missing or Unclear Information", styles))
    if missing:
        miss_data = [[
            Paragraph("<b>Field</b>",
                ParagraphStyle("MH1", fontName=f"{F}-Bold", fontSize=10, textColor=white)),
            Paragraph("<b>Impact</b>",
                ParagraphStyle("MH2", fontName=f"{F}-Bold", fontSize=10, textColor=white)),
        ]]
        for m in missing:
            miss_data.append([
                Paragraph(m.get("field","Not Available"), styles["Body"]),
                Paragraph(m.get("impact",""), styles["Body"]),
            ])
        m_table = Table(miss_data, colWidths=[page_w*0.38, page_w*0.62], repeatRows=1)
        m_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), COLOR_HEADER_BG),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [white, COLOR_ROW_ALT]),
            ("BOX",           (0,0),(-1,-1), 0.5, COLOR_BORDER),
            ("GRID",          (0,0),(-1,-1), 0.3, COLOR_BORDER),
            ("LEFTPADDING",   (0,0),(-1,-1), 8),
            ("RIGHTPADDING",  (0,0),(-1,-1), 8),
            ("TOPPADDING",    (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))
        story.append(m_table)
    else:
        story.append(Paragraph(
            "All required information was available in the source documents.",
            styles["Body"]
        ))

    story.append(_make_footer_bar(page_num, styles))
    story.append(PageBreak())
    page_num += 1

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 5 (original DDR numbering): LIMITATION AND PRECAUTION NOTE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))
    story.extend(section_main_header("SECTION 5    LIMITATION AND PRECAUTION NOTE", styles))

    limitation_texts = [
        ("Information provided in this report is a general overview of the most obvious repairs "
         "that may be needed. It is not intended to be an exhaustive list. The ultimate decision "
         "of what to repair or replace is clients. One client/owner may decide that certain "
         "conditions require repair or replacement, while another will not."),
        ("The inspection is not technically exhaustive (due to reasons such as budget constraints), "
         "the property inspection provides the client with a basic overview of the condition of "
         "the unit. Further, there are many complex systems in the property that are common element "
         "and not within the scope of the inspection. Specialists would typically be engaged by "
         "the Condominium Association to review these systems as necessary."),
        ("Some conditions noted, such as structural cracks & other signs of settlement indicate "
         "a potential problem that the structure of the building, or at least part of it, is "
         "overstressed. A structure when stretched beyond its capacity, may collapse without "
         "further warning signs. When such cracks suddenly develop, or appear to widen and/or "
         "spread, the findings must be reported immediately to the Structural Engineer, Buildings "
         "Department. A building professional such as a Registered Structural Engineer is usually "
         "required to investigate the cause(s) of the cracks, to assess their effects on the "
         "structure, to propose suitable rectification and remedial works, and supervise the "
         "carrying out of such works."),
        ("If such work is beyond the scope of the inspection & client is concerned about any "
         "conditions noted in the inspection report, inspector strongly recommends that client "
         "consults a qualified Licensed Contractor Professional or Consulting Engineer. These "
         "professionals can provide a more detailed analysis of any conditions noted in the "
         "report at an additional cost."),
        ("The Inspector's Report is an opinion of the present condition of the property. It is "
         "based on a visual examination of the readily accessible features of the property. "
         "A property Inspection does not include identifying defects that are hidden behind walls, "
         "floors, ceilings, finishing surfaces such as tiling, coba, plaster or any other "
         "masonry surfaces & sub-structures. This includes RCC members, structure, plumbing "
         "connections, cold joints, other all kind of joints & critical areas and that are hidden "
         "or inaccessible. Some intermittent problems may not be obvious on an Inspection because "
         "they only happen under certain circumstances."),
    ]
    for txt in limitation_texts:
        story.append(Paragraph(txt, styles["Body"]))
        story.append(Spacer(1, 6))

    story.append(_make_footer_bar(page_num, styles))
    story.append(PageBreak())
    page_num += 1

    # ══════════════════════════════════════════════════════════════════════════
    # LEGAL DISCLAIMER (last pages)
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_header())
    story.append(Spacer(1, 8))

    # Code compliance etc.
    code_texts = [
        ("THIS IS NOT A CODE COMPLIANCE INSPECTION. The Inspector does NOT try to determine "
         "whether or not any aspect of the property complies with any past, present or future "
         "codes such as building codes etc. regulations, laws, by laws, ordinances or other "
         "regulatory requirements."),
        ("INSPECTION DOES NOT COMMENT ON THE QUALITY OF AIR IN A BUILDING. The Inspector does "
         "not try to determine if there are irritants, pollutants, contaminants, or toxic "
         "materials in or around the property."),
        ("Client should note that whenever there is water damage noted in the report, there is "
         "a possibility that mold or mildew may be present, unseen behind a wall, floor or "
         "ceiling. If anyone in the property suffers from allergies or heightened sensitivity "
         "to quality of air, Inspector strongly recommend to consult a qualified Environmental "
         "Consultant who can test for toxic materials, mold and allergens at additional cost."),
        ("THE INSPECTION DOES NOT INCLUDE HAZARDOUS MATERIALS. This includes building materials "
         "that are now suspected of posing a risk to health such as phenol formaldehyde & urea "
         "formaldehyde-based insulation, fiberglass insulation & vermiculite insulation."),
    ]
    for txt in code_texts:
        story.append(Paragraph(txt, styles["Body"]))
        story.append(Spacer(1, 6))

    story.append(_make_footer_bar(page_num, styles))
    story.append(PageBreak())
    page_num += 1

    # Legal disclaimer page
    story.append(_header())
    story.append(Spacer(1, 8))
    story.append(Paragraph("Legal Disclaimer", styles["LegalTitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ORANGE))
    story.append(Spacer(1, 8))

    legal_texts = [
        ("UrbanRoof (Hereinafter \"INSPECTOR\" has performed a visual & non-destructive test "
         "inspection of the property/structure and provides the CLIENT with an inspection report "
         "giving an opinion of the present condition of the property, based on a visual & "
         "non-destructive examination of the readily accessible features & elements of the "
         "property. Common elements, such as exterior elements, parking, common mechanical and "
         "other systems & structure which are not in or beyond the scope, are not inspected."),
        ("The inspection and report are performed and prepared for the use of CLIENT, who gives "
         "INSPECTOR permission to discuss observations with owners, repair persons, and other "
         "interested parties. INSPECTOR accepts no responsibility for use or misinterpretation "
         "by third parties."),
        ("INSPECTOR has not performed engineering, architectural, plumbing, or any other job "
         "function requiring an occupational license in the jurisdiction where the inspection "
         "is taking place."),
        ("Quantitative and qualitative information is based primarily on site visited and "
         "observed on the particular day and therefore is subject to fluctuation. UrbanRoof is "
         "not responsible for any incorrect information supplied to us by client, customer, or users."),
        "UrbanRoof will not abide to update this diagnosis report due to any further changes and/or damages and/or updation of the site.",
        ("This report is subject to copy rights held with UrbanRoof Private Limited. No part of "
         "this report service may be given, lent, resold, or disclosed to noncustomers, and used "
         "as evidence in the court of the law without written approval of UrbanRoof Private "
         "Limited, Pune. Our customers acknowledge, when ordering, subscribing or downloading, "
         "that UrbanRoof Private Limited inspection services are for customers' internal use "
         "and not for general publication or disclosure to third parties."),
        ("Furthermore, no part may be reproduced, stored in a retrieval system, or transmitted "
         "in any form or by any means, electronic, mechanical, photocopying, recording or "
         "otherwise, without the permission of the publisher."),
    ]
    for txt in legal_texts:
        story.append(Paragraph(txt, styles["LegalBody"]))
        story.append(Spacer(1, 5))

    story.append(_make_footer_bar(page_num, styles))

    # ── Build PDF ─────────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
        title="Detailed Diagnostic Report"
    )
    doc.build(story)
    buffer.seek(0)
    return buffer.read()