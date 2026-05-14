"""Generate the Energy Hunter pitch deck (.pptx) for the 5-minute hackathon demo.

Run:
    python scripts/generate_deck.py

Output:
    presentations/energy_hunter_pitch.pptx

The deck uses an eco-friendly palette (deep green, leaf green, sand, charcoal)
and embeds illustrative images generated with Pillow so the file is fully
self-contained and reproducible without internet access.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

# --------------------------------------------------------------------------- #
# Eco palette                                                                 #
# --------------------------------------------------------------------------- #

DEEP_GREEN = RGBColor(0x10, 0x4F, 0x3A)   # bosque profundo
LEAF_GREEN = RGBColor(0x2E, 0x8B, 0x57)   # hoja
LIME = RGBColor(0x9A, 0xCD, 0x32)         # acento brillante
SAND = RGBColor(0xF5, 0xEF, 0xE0)         # fondo cálido neutro
CHARCOAL = RGBColor(0x1F, 0x2A, 0x24)     # texto principal
SLATE = RGBColor(0x4B, 0x5A, 0x52)        # texto secundario
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ALERT = RGBColor(0xC2, 0x4D, 0x2C)        # ámbar tierra para alertas

# Pillow-friendly tuples
P_DEEP = (0x10, 0x4F, 0x3A)
P_LEAF = (0x2E, 0x8B, 0x57)
P_LIME = (0x9A, 0xCD, 0x32)
P_SAND = (0xF5, 0xEF, 0xE0)
P_CHARCOAL = (0x1F, 0x2A, 0x24)
P_WHITE = (0xFF, 0xFF, 0xFF)
P_ALERT = (0xC2, 0x4D, 0x2C)
P_SKY = (0xCDE7DA)


# --------------------------------------------------------------------------- #
# Paths                                                                       #
# --------------------------------------------------------------------------- #

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "presentations" / "assets"
OUTPUT = ROOT / "presentations" / "energy_hunter_pitch.pptx"
ASSETS.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Image generation helpers (Pillow)                                           #
# --------------------------------------------------------------------------- #

def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Best-effort font loader; falls back to default bitmap font on Windows."""
    candidates = (
        ["arialbd.ttf", "calibrib.ttf", "segoeuib.ttf"]
        if bold
        else ["arial.ttf", "calibri.ttf", "segoeui.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    base = Image.new("RGB", size, top)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        ImageDraw.Draw(base).line([(0, y), (w, y)], fill=(r, g, b))
    return base


def make_hero_image(path: Path) -> None:
    """Cover hero: stylised city skyline with a sun/leaf and energy lines."""
    W, H = 1600, 900
    img = _gradient((W, H), (0xE8, 0xF1, 0xE3), (0xBF, 0xDC, 0xC4))
    draw = ImageDraw.Draw(img, "RGBA")

    # Sun / leaf circle
    cx, cy, r = 1280, 240, 150
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(0xCB, 0xE6, 0x8E, 255))
    # Leaf vein
    draw.line((cx - r + 30, cy + r - 30, cx + r - 30, cy - r + 30), fill=P_DEEP, width=8)

    # Skyline buildings
    random.seed(7)
    base_y = 720
    x = 80
    while x < W - 80:
        bw = random.randint(70, 160)
        bh = random.randint(180, 420)
        color = random.choice([P_DEEP, P_LEAF, (0x1A, 0x6E, 0x52), (0x14, 0x5A, 0x42)])
        draw.rectangle((x, base_y - bh, x + bw, base_y), fill=color)
        # Windows grid
        for wy in range(base_y - bh + 20, base_y - 20, 28):
            for wx in range(x + 12, x + bw - 12, 22):
                if random.random() > 0.35:
                    draw.rectangle((wx, wy, wx + 10, wy + 14), fill=(0xF5, 0xEF, 0xE0, 220))
        x += bw + 12

    # Ground line
    draw.rectangle((0, base_y, W, H), fill=(0x10, 0x3A, 0x2C))

    # Energy waves
    for i, amp in enumerate((40, 28, 18)):
        pts = []
        for px in range(0, W, 8):
            py = 820 + int(math.sin((px / 80) + i) * amp * 0.4)
            pts.append((px, py))
        draw.line(pts, fill=(0x9A, 0xCD, 0x32, 220 - i * 40), width=4)

    img.save(path, "PNG", optimize=True)


def make_problem_image(path: Path) -> None:
    """Stylised meter dial with overload zone."""
    W, H = 1200, 800
    img = Image.new("RGB", (W, H), P_SAND)
    draw = ImageDraw.Draw(img, "RGBA")

    cx, cy, r = W // 2, H // 2 + 40, 280
    # Dial background
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=P_WHITE, outline=P_CHARCOAL, width=6)

    # Coloured arcs: green / amber / red
    draw.arc((cx - r + 20, cy - r + 20, cx + r - 20, cy + r - 20),
             start=180, end=240, fill=P_LEAF, width=40)
    draw.arc((cx - r + 20, cy - r + 20, cx + r - 20, cy + r - 20),
             start=240, end=300, fill=(0xD4, 0xA0, 0x2A), width=40)
    draw.arc((cx - r + 20, cy - r + 20, cx + r - 20, cy + r - 20),
             start=300, end=360, fill=P_ALERT, width=40)

    # Needle pointing into the red zone
    angle = math.radians(335)
    nx = cx + int(math.cos(angle) * (r - 60))
    ny = cy + int(math.sin(angle) * (r - 60))
    draw.line((cx, cy, nx, ny), fill=P_CHARCOAL, width=10)
    draw.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=P_CHARCOAL)

    # Label
    f = _font(48, bold=True)
    draw.text((cx - 220, cy + r + 20), "Consumo fuera de control", fill=P_CHARCOAL, font=f)

    img.save(path, "PNG", optimize=True)


def make_dashboard_mock(path: Path) -> None:
    """Stylised dashboard mock: map + KPIs + chart."""
    W, H = 1600, 900
    img = Image.new("RGB", (W, H), P_SAND)
    draw = ImageDraw.Draw(img, "RGBA")

    # Top bar
    draw.rectangle((0, 0, W, 80), fill=P_DEEP)
    draw.text((40, 22), "Energy Hunter — Panel B2B", fill=P_WHITE, font=_font(32, bold=True))
    draw.ellipse((W - 60, 28, W - 36, 52), fill=P_LIME)

    # Sidebar (building list)
    draw.rectangle((0, 80, 320, H), fill=(0xEC, 0xE3, 0xCE))
    draw.text((24, 100), "Edificios", fill=P_CHARCOAL, font=_font(24, bold=True))
    for i, name in enumerate(["Sede Madrid", "Planta Sevilla", "Centro Bilbao", "Oficina Valencia"]):
        y = 150 + i * 60
        draw.rectangle((16, y, 304, y + 48), fill=P_WHITE, outline=P_LEAF, width=2)
        draw.ellipse((30, y + 16, 46, y + 32), fill=P_LEAF if i == 0 else (0xCC, 0xCC, 0xCC))
        draw.text((58, y + 14), name, fill=P_CHARCOAL, font=_font(20))

    # Map area
    map_x0, map_y0, map_x1, map_y1 = 340, 100, 1000, 520
    draw.rectangle((map_x0, map_y0, map_x1, map_y1), fill=(0xDC, 0xEA, 0xD8), outline=P_LEAF, width=3)
    # Fake map grid
    for gx in range(map_x0, map_x1, 40):
        draw.line((gx, map_y0, gx, map_y1), fill=(0xC9, 0xDC, 0xC2), width=1)
    for gy in range(map_y0, map_y1, 40):
        draw.line((map_x0, gy, map_x1, gy), fill=(0xC9, 0xDC, 0xC2), width=1)
    # Markers
    pins = [(map_x0 + 180, map_y0 + 140, P_LEAF),
            (map_x0 + 360, map_y0 + 220, P_LEAF),
            (map_x0 + 500, map_y0 + 120, P_ALERT),  # anomaly
            (map_x0 + 280, map_y0 + 320, P_LEAF)]
    for (px, py, color) in pins:
        draw.ellipse((px - 14, py - 14, px + 14, py + 14), fill=color, outline=P_WHITE, width=3)
        if color == P_ALERT:
            draw.polygon([(px, py - 30), (px - 12, py - 8), (px + 12, py - 8)], fill=P_ALERT)
    draw.text((map_x0 + 16, map_y0 + 12), "Mapa interactivo", fill=P_DEEP, font=_font(22, bold=True))

    # KPI cards
    kpis = [("kWh hoy", "1.842"), ("€/MWh ahora", "112"), ("Anomalías", "3"), ("Modo Eco", "2 fases")]
    for i, (label, value) in enumerate(kpis):
        x0 = 1020 + (i % 2) * 280
        y0 = 100 + (i // 2) * 200
        draw.rectangle((x0, y0, x0 + 260, y0 + 180), fill=P_WHITE, outline=P_LEAF, width=2)
        draw.text((x0 + 20, y0 + 18), label, fill=P_CHARCOAL, font=_font(20))
        draw.text((x0 + 20, y0 + 58), value, fill=P_DEEP, font=_font(60, bold=True))

    # Chart area
    cx0, cy0, cx1, cy1 = 340, 540, 1560, 860
    draw.rectangle((cx0, cy0, cx1, cy1), fill=P_WHITE, outline=P_LEAF, width=2)
    draw.text((cx0 + 16, cy0 + 12), "Consumo por fase (últimas 6 horas)", fill=P_DEEP, font=_font(22, bold=True))
    # Axes
    draw.line((cx0 + 40, cy1 - 20, cx1 - 20, cy1 - 20), fill=P_CHARCOAL, width=2)
    draw.line((cx0 + 40, cy0 + 50, cx0 + 40, cy1 - 20), fill=P_CHARCOAL, width=2)
    # Series
    random.seed(11)
    for series_color in (P_LEAF, P_DEEP, (0x4F, 0xA0, 0x70)):
        pts = []
        for k in range(40):
            x = cx0 + 50 + k * ((cx1 - cx0 - 70) // 40)
            y = cy1 - 30 - random.randint(20, 220)
            pts.append((x, y))
        draw.line(pts, fill=series_color, width=4)
    # Anomaly marker
    ax, ay = cx0 + 50 + 26 * ((cx1 - cx0 - 70) // 40), cy0 + 90
    draw.polygon([(ax, ay - 14), (ax - 12, ay + 8), (ax + 12, ay + 8)], fill=P_ALERT)
    draw.text((ax + 16, ay - 8), "Anomalía domingo", fill=P_ALERT, font=_font(18, bold=True))

    img.save(path, "PNG", optimize=True)


def make_panic_image(path: Path) -> None:
    """Big eco button + checkboxes for the panic flow."""
    W, H = 1200, 800
    img = Image.new("RGB", (W, H), P_SAND)
    draw = ImageDraw.Draw(img, "RGBA")

    # Card
    draw.rectangle((80, 80, W - 80, H - 80), fill=P_WHITE, outline=P_LEAF, width=4)
    draw.text((120, 110), "Botón de Pánico granular", fill=P_DEEP, font=_font(40, bold=True))
    draw.text((120, 170), "Selecciona qué fases pasan a Modo Eco (-40%)", fill=P_CHARCOAL, font=_font(24))

    # Checkboxes
    items = [("Fase A — Iluminación oficinas", True),
             ("Fase B — Climatización plantas 1-3", True),
             ("Fase C — Servidores críticos", False),
             ("Fase D — Cargadores VE", True)]
    for i, (text, checked) in enumerate(items):
        y = 230 + i * 70
        # Box
        draw.rectangle((140, y, 180, y + 40), fill=P_WHITE, outline=P_DEEP, width=3)
        if checked:
            draw.line((148, y + 22, 162, y + 34), fill=P_LEAF, width=6)
            draw.line((162, y + 34, 174, y + 10), fill=P_LEAF, width=6)
        draw.text((210, y + 6), text, fill=P_CHARCOAL, font=_font(26))

    # Panic button (eco green, accessible label)
    draw.rounded_rectangle((140, 580, 700, 680), radius=24, fill=P_DEEP)
    draw.text((180, 612), "Activar Modo Eco", fill=P_WHITE, font=_font(36, bold=True))

    # Result chip
    draw.rounded_rectangle((740, 580, 1080, 680), radius=24, fill=P_LIME)
    draw.text((780, 612), "−40% consumo", fill=P_CHARCOAL, font=_font(30, bold=True))

    img.save(path, "PNG", optimize=True)


def make_architecture_image(path: Path) -> None:
    """Simple architecture diagram: Streamlit ↔ Mock API ↔ Kiro stub."""
    W, H = 1400, 700
    img = Image.new("RGB", (W, H), P_SAND)
    draw = ImageDraw.Draw(img, "RGBA")

    boxes = [
        (60, 260, 320, 440, "Streamlit\nDashboard", P_LEAF),
        (440, 100, 720, 280, "Smart Breaker\nMock API", P_DEEP),
        (440, 420, 720, 600, "SIOS\nPrecios", P_DEEP),
        (840, 260, 1100, 440, "Kiro\nWebhook", P_LEAF),
        (1180, 260, 1380, 440, "Modo Eco\n−40%", P_LIME),
    ]
    for (x0, y0, x1, y1, label, color) in boxes:
        draw.rounded_rectangle((x0, y0, x1, y1), radius=18, fill=color, outline=P_CHARCOAL, width=3)
        f = _font(28, bold=True)
        text_color = P_WHITE if color != P_LIME else P_CHARCOAL
        # Center text
        lines = label.split("\n")
        total_h = len(lines) * 36
        ty = (y0 + y1) // 2 - total_h // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=f)
            tw = bbox[2] - bbox[0]
            draw.text(((x0 + x1) // 2 - tw // 2, ty), line, fill=text_color, font=f)
            ty += 36

    # Arrows
    def arrow(p0, p1):
        draw.line([p0, p1], fill=P_CHARCOAL, width=4)
        ax, ay = p1
        draw.polygon([(ax, ay - 10), (ax, ay + 10), (ax + 18, ay)], fill=P_CHARCOAL)

    arrow((320, 350), (438, 190))
    arrow((320, 350), (438, 510))
    arrow((720, 190), (840, 330))
    arrow((720, 510), (840, 370))
    arrow((1100, 350), (1178, 350))

    # Title
    draw.text((60, 40), "Arquitectura local 100% reproducible", fill=P_DEEP, font=_font(34, bold=True))

    img.save(path, "PNG", optimize=True)


def make_savings_chart(path: Path) -> None:
    """Bar chart: kWh before vs after Eco Mode."""
    W, H = 1200, 720
    img = Image.new("RGB", (W, H), P_SAND)
    draw = ImageDraw.Draw(img, "RGBA")

    draw.text((60, 40), "Impacto inmediato del Modo Eco", fill=P_DEEP, font=_font(34, bold=True))

    categories = [("Iluminación", 120, 72),
                  ("Climatización", 240, 144),
                  ("Cargadores VE", 180, 108),
                  ("Total fases", 540, 324)]

    # Axes
    ox, oy = 120, 620
    draw.line((ox, oy, W - 60, oy), fill=P_CHARCOAL, width=3)
    draw.line((ox, 140, ox, oy), fill=P_CHARCOAL, width=3)

    bar_w = 90
    gap = 160
    max_val = 600
    for i, (label, before, after) in enumerate(categories):
        x = ox + 60 + i * (bar_w * 2 + gap - 90)
        # Before bar (charcoal)
        bh = int((before / max_val) * (oy - 160))
        draw.rectangle((x, oy - bh, x + bar_w, oy), fill=(0x4B, 0x5A, 0x52))
        draw.text((x, oy - bh - 30), f"{before}", fill=P_CHARCOAL, font=_font(22, bold=True))
        # After bar (lime)
        ah = int((after / max_val) * (oy - 160))
        draw.rectangle((x + bar_w + 10, oy - ah, x + bar_w * 2 + 10, oy), fill=P_LEAF)
        draw.text((x + bar_w + 10, oy - ah - 30), f"{after}", fill=P_DEEP, font=_font(22, bold=True))
        # Label
        draw.text((x - 4, oy + 12), label, fill=P_CHARCOAL, font=_font(20))

    # Legend
    draw.rectangle((W - 360, 100, W - 340, 120), fill=(0x4B, 0x5A, 0x52))
    draw.text((W - 320, 96), "Antes (kWh)", fill=P_CHARCOAL, font=_font(22))
    draw.rectangle((W - 360, 140, W - 340, 160), fill=P_LEAF)
    draw.text((W - 320, 136), "Con Modo Eco (−40%)", fill=P_CHARCOAL, font=_font(22))

    img.save(path, "PNG", optimize=True)


def make_roadmap_image(path: Path) -> None:
    """Horizontal roadmap with milestones."""
    W, H = 1400, 500
    img = Image.new("RGB", (W, H), P_SAND)
    draw = ImageDraw.Draw(img, "RGBA")
    draw.text((60, 40), "Roadmap", fill=P_DEEP, font=_font(36, bold=True))

    # Track
    draw.rectangle((80, 240, W - 80, 270), fill=P_LEAF)
    milestones = [
        (180, "MVP demo\nhackathon", P_LIME),
        (480, "Piloto\n3 edificios", P_LEAF),
        (780, "Integración\nbreakers reales", P_LEAF),
        (1080, "Multi-tenant\n+ alertas IA", P_DEEP),
        (1320, "Mercado\nEU", P_DEEP),
    ]
    for (x, label, color) in milestones:
        draw.ellipse((x - 22, 233, x + 22, 277), fill=color, outline=P_CHARCOAL, width=3)
        # Label box
        lines = label.split("\n")
        f = _font(22, bold=True)
        ty = 310
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=f)
            tw = bbox[2] - bbox[0]
            draw.text((x - tw // 2, ty), line, fill=P_CHARCOAL, font=f)
            ty += 28

    img.save(path, "PNG", optimize=True)


# --------------------------------------------------------------------------- #
# Slide builder helpers (python-pptx)                                         #
# --------------------------------------------------------------------------- #

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def add_background(slide, color: RGBColor) -> None:
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    rect.line.fill.background()
    rect.fill.solid()
    rect.fill.fore_color.rgb = color
    rect.shadow.inherit = False
    # Send to back by reordering xml
    spTree = rect._element.getparent()
    spTree.remove(rect._element)
    spTree.insert(2, rect._element)


def add_side_band(slide, color: RGBColor, width=Inches(0.35)) -> None:
    band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, width, SLIDE_H)
    band.line.fill.background()
    band.fill.solid()
    band.fill.fore_color.rgb = color


def add_textbox(
    slide,
    left,
    top,
    width,
    height,
    text: str,
    *,
    size: int = 18,
    bold: bool = False,
    color: RGBColor = CHARCOAL,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = "Calibri"
    return tb


def add_bullets(
    slide,
    left,
    top,
    width,
    height,
    bullets: list[str],
    *,
    size: int = 22,
    color: RGBColor = CHARCOAL,
    bullet_color: RGBColor = LEAF_GREEN,
):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    for i, item in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        # Bullet marker
        marker = p.add_run()
        marker.text = "▎ "
        marker.font.size = Pt(size)
        marker.font.bold = True
        marker.font.color.rgb = bullet_color
        marker.font.name = "Calibri"
        # Text
        run = p.add_run()
        run.text = item
        run.font.size = Pt(size)
        run.font.color.rgb = color
        run.font.name = "Calibri"
        p.space_after = Pt(8)
    return tb


def add_footer(slide, page_num: int, total: int) -> None:
    add_textbox(
        slide, Inches(0.5), Inches(7.05), Inches(8), Inches(0.35),
        "Energy Hunter · Hackathon Demo", size=11, color=SLATE,
    )
    add_textbox(
        slide, Inches(11.5), Inches(7.05), Inches(1.4), Inches(0.35),
        f"{page_num} / {total}", size=11, color=SLATE, align=PP_ALIGN.RIGHT,
    )


# --------------------------------------------------------------------------- #
# Slide layouts                                                               #
# --------------------------------------------------------------------------- #

TOTAL_SLIDES = 10


def build_cover(prs: Presentation, hero_path: Path) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    add_background(slide, SAND)

    # Hero image as full-bleed top band
    slide.shapes.add_picture(str(hero_path), 0, 0, width=SLIDE_W, height=Inches(4.2))

    # Green title bar overlay
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(3.6), SLIDE_W, Inches(0.6))
    bar.line.fill.background()
    bar.fill.solid()
    bar.fill.fore_color.rgb = DEEP_GREEN

    add_textbox(
        slide, Inches(0.7), Inches(3.62), Inches(12), Inches(0.6),
        "Energy Hunter", size=28, bold=True, color=WHITE,
    )

    # Subtitle block
    add_textbox(
        slide, Inches(0.7), Inches(4.5), Inches(12), Inches(0.7),
        "Gestión inteligente de energía para edificios B2B",
        size=34, bold=True, color=DEEP_GREEN,
    )
    add_textbox(
        slide, Inches(0.7), Inches(5.25), Inches(12), Inches(0.6),
        "Visibilidad en tiempo real · Detección de anomalías · Modo Eco con un clic",
        size=20, color=SLATE,
    )

    # Tagline pill
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.7), Inches(6.1), Inches(5.2), Inches(0.55))
    pill.line.fill.background()
    pill.fill.solid()
    pill.fill.fore_color.rgb = LIME
    add_textbox(
        slide, Inches(0.7), Inches(6.1), Inches(5.2), Inches(0.55),
        "Menos consumo · Menos emisiones · Más control",
        size=16, bold=True, color=CHARCOAL, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
    )

    add_textbox(
        slide, Inches(0.7), Inches(6.8), Inches(12), Inches(0.4),
        "Avance MVP · Hackathon 2026", size=14, color=SLATE,
    )


def build_title_slide(prs: Presentation, page: int, eyebrow: str, title: str, subtitle: str) -> object:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide, SAND)
    add_side_band(slide, DEEP_GREEN)
    add_textbox(slide, Inches(0.7), Inches(0.5), Inches(12), Inches(0.4),
                eyebrow.upper(), size=12, bold=True, color=LEAF_GREEN)
    add_textbox(slide, Inches(0.7), Inches(0.85), Inches(12), Inches(0.9),
                title, size=34, bold=True, color=DEEP_GREEN)
    add_textbox(slide, Inches(0.7), Inches(1.7), Inches(12), Inches(0.6),
                subtitle, size=18, color=SLATE)
    add_footer(slide, page, TOTAL_SLIDES)
    return slide


def build_problem(prs: Presentation, page: int, image: Path) -> None:
    slide = build_title_slide(
        prs, page,
        "El problema",
        "Los edificios consumen sin saber dónde ni cuándo",
        "Datos dispersos, facturas sorpresa y nula reacción ante picos de consumo",
    )
    slide.shapes.add_picture(str(image), Inches(7.6), Inches(2.4), width=Inches(5.2))
    add_bullets(
        slide, Inches(0.7), Inches(2.6), Inches(6.8), Inches(4),
        [
            "30-40% del consumo eléctrico mundial proviene de edificios.",
            "Los gestores ven la factura, pero no la fase ni el equipo culpable.",
            "Las anomalías (consumos fuera de patrón) pasan desapercibidas durante días.",
            "Apagar manualmente cargas no críticas requiere coordinación lenta.",
        ],
        size=18,
    )


def build_solution(prs: Presentation, page: int, dashboard: Path) -> None:
    slide = build_title_slide(
        prs, page,
        "La solución",
        "Un panel B2B que ve, alerta y actúa",
        "Streamlit + telemetría en tiempo real + Modo Eco granular por fase",
    )
    slide.shapes.add_picture(str(dashboard), Inches(0.7), Inches(2.4), width=Inches(8.2))
    add_bullets(
        slide, Inches(9.1), Inches(2.5), Inches(3.7), Inches(4.5),
        [
            "Mapa con todos los edificios.",
            "KPIs vivos: kWh, €/MWh, anomalías.",
            "Curvas por fase con marcadores visuales.",
            "Botón de pánico con efecto inmediato.",
        ],
        size=16,
    )


def build_advantages(prs: Presentation, page: int) -> None:
    slide = build_title_slide(
        prs, page,
        "Ventajas clave",
        "Por qué Energy Hunter mueve la aguja",
        "Diseñado alrededor del ahorro, la accesibilidad y la velocidad de reacción",
    )

    cards = [
        ("Ahorro inmediato", "Hasta −40% de consumo en las fases que el operador elige, sin obras."),
        ("Detección de anomalías", "Regla de domingo (×1.40 sobre baseline) y marcadores en mapa y gráfica."),
        ("Control granular", "Modo Eco fase a fase, no \"todo o nada\". Cero impacto en cargas críticas."),
        ("Telemetría 30 s", "Lectura cada 30 s con back-off automático y estado API siempre visible."),
        ("Accesible WCAG 2.1 AA", "Lectores de pantalla, contraste alto, navegación por teclado."),
        ("Stack abierto", "Python + Streamlit + Flask. Reproducible en local en 2 comandos."),
    ]
    col_w = Inches(4.0)
    row_h = Inches(1.55)
    x0 = Inches(0.7)
    y0 = Inches(2.5)
    for i, (title, desc) in enumerate(cards):
        col = i % 3
        row = i // 3
        x = x0 + col * (col_w + Inches(0.15))
        y = y0 + row * (row_h + Inches(0.2))
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, col_w, row_h)
        card.line.color.rgb = LEAF_GREEN
        card.line.width = Pt(1.5)
        card.fill.solid()
        card.fill.fore_color.rgb = WHITE
        # Accent dot
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, x + Inches(0.2), y + Inches(0.22), Inches(0.22), Inches(0.22))
        dot.line.fill.background()
        dot.fill.solid()
        dot.fill.fore_color.rgb = LIME
        add_textbox(slide, x + Inches(0.55), y + Inches(0.15), col_w - Inches(0.6), Inches(0.4),
                    title, size=16, bold=True, color=DEEP_GREEN)
        add_textbox(slide, x + Inches(0.25), y + Inches(0.6), col_w - Inches(0.4), Inches(0.95),
                    desc, size=12, color=CHARCOAL)


def build_panic(prs: Presentation, page: int, image: Path) -> None:
    slide = build_title_slide(
        prs, page,
        "Demo destacada",
        "Botón de Pánico granular: del clic al ahorro en segundos",
        "Marca las fases, confirma, y el webhook propaga Modo Eco al hardware simulado",
    )
    slide.shapes.add_picture(str(image), Inches(0.7), Inches(2.4), width=Inches(7))
    add_bullets(
        slide, Inches(8.1), Inches(2.5), Inches(4.7), Inches(4.5),
        [
            "1. El operador ve un pico anómalo.",
            "2. Selecciona qué fases pasan a Eco.",
            "3. Confirma con un único botón.",
            "4. Webhook → API → −40% en esas fases.",
            "5. Estado se anuncia por aria-live (a11y).",
            "6. Cargas críticas siguen intactas.",
        ],
        size=15,
    )


def build_architecture(prs: Presentation, page: int, image: Path) -> None:
    slide = build_title_slide(
        prs, page,
        "Cómo funciona",
        "Arquitectura simple, demoable en local",
        "Sin dependencias cloud para el hackathon: 2 comandos y listo",
    )
    slide.shapes.add_picture(str(image), Inches(0.7), Inches(2.3), width=Inches(12))
    add_textbox(
        slide, Inches(0.7), Inches(6.2), Inches(12), Inches(0.6),
        "Streamlit consume el Mock API (Smart Breaker + SIOS), Kiro orquesta el "
        "fan-out a Modo Eco. TDD + property-based tests cubren las 10 propiedades críticas.",
        size=13, color=SLATE,
    )


def build_savings(prs: Presentation, page: int, image: Path) -> None:
    slide = build_title_slide(
        prs, page,
        "Impacto",
        "Ahorro medible por categoría de carga",
        "Ejemplo de un edificio piloto: 4 fases activadas en Modo Eco durante 1 hora",
    )
    slide.shapes.add_picture(str(image), Inches(0.7), Inches(2.3), width=Inches(8.5))
    add_bullets(
        slide, Inches(9.4), Inches(2.5), Inches(3.4), Inches(4.5),
        [
            "−40% por fase activada.",
            "Reducción proporcional de €/h.",
            "Menos huella de CO₂ inmediata.",
            "Sin tocar servidores críticos.",
            "Auditable: cada acción queda registrada.",
        ],
        size=15,
    )


def build_roadmap(prs: Presentation, page: int, image: Path) -> None:
    slide = build_title_slide(
        prs, page,
        "Hacia dónde va",
        "Roadmap del MVP al producto",
        "Hoy: hackathon. Mañana: piloto real con breakers físicos.",
    )
    slide.shapes.add_picture(str(image), Inches(0.5), Inches(2.5), width=Inches(12.3))


def build_closing(prs: Presentation, page: int) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide, DEEP_GREEN)
    add_textbox(
        slide, Inches(0.7), Inches(1.6), Inches(12), Inches(1),
        "Energía bajo control. Naturaleza protegida.",
        size=44, bold=True, color=WHITE,
    )
    add_textbox(
        slide, Inches(0.7), Inches(2.7), Inches(12), Inches(0.8),
        "Energy Hunter convierte cada edificio en un actor activo del ahorro.",
        size=22, color=SAND,
    )

    # Three stat tiles
    stats = [("−40%", "consumo por fase\nen Modo Eco"),
             ("30 s", "frecuencia de\ntelemetría"),
             ("WCAG 2.1 AA", "accesibilidad\npor diseño")]
    for i, (big, small) in enumerate(stats):
        x = Inches(0.7) + i * Inches(4.1)
        tile = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(4), Inches(3.9), Inches(2))
        tile.line.fill.background()
        tile.fill.solid()
        tile.fill.fore_color.rgb = LEAF_GREEN
        add_textbox(slide, x, Inches(4.1), Inches(3.9), Inches(0.8),
                    big, size=40, bold=True, color=LIME, align=PP_ALIGN.CENTER)
        add_textbox(slide, x, Inches(5.0), Inches(3.9), Inches(1),
                    small, size=14, color=WHITE, align=PP_ALIGN.CENTER)

    add_textbox(
        slide, Inches(0.7), Inches(6.6), Inches(12), Inches(0.5),
        "¿Preguntas? — github.com/energy-hunter   ·   demo en vivo disponible",
        size=14, color=SAND, align=PP_ALIGN.CENTER,
    )


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #

def main() -> Path:
    # 1. Generate images
    hero = ASSETS / "hero.png"
    problem = ASSETS / "problem_meter.png"
    dashboard = ASSETS / "dashboard_mock.png"
    panic = ASSETS / "panic_panel.png"
    architecture = ASSETS / "architecture.png"
    savings = ASSETS / "savings_chart.png"
    roadmap = ASSETS / "roadmap.png"

    make_hero_image(hero)
    make_problem_image(problem)
    make_dashboard_mock(dashboard)
    make_panic_image(panic)
    make_architecture_image(architecture)
    make_savings_chart(savings)
    make_roadmap_image(roadmap)

    # 2. Build deck (16:9)
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    build_cover(prs, hero)                      # 1
    build_problem(prs, 2, problem)              # 2
    build_solution(prs, 3, dashboard)           # 3
    build_advantages(prs, 4)                    # 4
    build_panic(prs, 5, panic)                  # 5
    build_architecture(prs, 6, architecture)    # 6
    build_savings(prs, 7, savings)              # 7
    build_roadmap(prs, 8, roadmap)              # 8
    # Slide 9: differentiation vs alternatives
    diff = build_title_slide(
        prs, 9,
        "Frente a alternativas",
        "Lo que nos diferencia de otros proyectos del hackathon",
        "Foco en acción, no solo en visualización",
    )
    add_bullets(
        diff, Inches(0.7), Inches(2.6), Inches(12), Inches(4),
        [
            "Otros muestran datos: nosotros además accionamos el Modo Eco en segundos.",
            "Granularidad por fase, no por edificio entero (cargas críticas siempre seguras).",
            "Stack 100% open-source y reproducible en local sin cuentas cloud.",
            "Accesibilidad WCAG AA desde el día 1, no como capa cosmética.",
            "TDD con propiedades formales: 10 invariantes verificadas con Hypothesis.",
        ],
        size=18,
    )
    build_closing(prs, 10)                      # 10

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    out = main()
    print(f"Deck escrito en: {out}")
