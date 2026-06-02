import io
from PIL import Image, ImageDraw, ImageFont

IMAGE_W = 1200
IMAGE_H = 630
MARGIN_X = 90
MARGIN_Y = 70
BG_COLOR = (15, 23, 42)        # slate-900
QUOTE_COLOR = (241, 245, 249)  # slate-100
ATTR_COLOR = (148, 163, 184)   # slate-400
ACCENT_COLOR = (99, 102, 241)  # indigo-500

_FONT_PATHS = [
    "/usr/share/fonts/dejavu-sans/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
_FONT_PATHS_BOLD = [p.replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf") for p in _FONT_PATHS]


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = _FONT_PATHS_BOLD if bold else _FONT_PATHS
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default(size=size)


def _wrap_lines(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        if draw.textlength(test, font=font) <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _fit_quote(draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int):
    """Return (font, lines) fitting within max_width x max_height, shrinking if needed."""
    for size in range(42, 22, -2):
        font = _load_font(size)
        lines = _wrap_lines(draw, text, font, max_width)
        line_h = draw.textbbox((0, 0), "Ag", font=font)[3]
        total_h = line_h * len(lines) + (line_h * 0.35) * (len(lines) - 1)
        if total_h <= max_height:
            return font, lines, int(line_h)
    font = _load_font(22)
    return font, _wrap_lines(draw, text, font, max_width), draw.textbbox((0, 0), "Ag", font=font)[3]


def generate(quote: dict) -> bytes:
    img = Image.new("RGB", (IMAGE_W, IMAGE_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Decorative large opening quote mark
    deco_font = _load_font(240, bold=True)
    draw.text((MARGIN_X - 20, MARGIN_Y - 80), "“", font=deco_font,
              fill=(*ACCENT_COLOR, 38))  # ~15% opacity via blending below

    # Blend the decorative mark at low opacity
    overlay = Image.new("RGB", (IMAGE_W, IMAGE_H), BG_COLOR)
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.text((MARGIN_X - 20, MARGIN_Y - 80), "“", font=deco_font, fill=ACCENT_COLOR)
    img = Image.blend(img, overlay, alpha=0.12)
    draw = ImageDraw.Draw(img)

    # Quote text block
    text_w = IMAGE_W - 2 * MARGIN_X
    # Reserve space for attribution line + gap + accent line
    attr_font = _load_font(26)
    attr_h = draw.textbbox((0, 0), "Ag", font=attr_font)[3]
    gap = 32
    accent_line_h = 3
    reserved = attr_h + gap + accent_line_h + 20
    text_area_h = IMAGE_H - 2 * MARGIN_Y - reserved

    quote_font, lines, line_h = _fit_quote(draw, f"“{quote['text']}”", text_w, text_area_h)
    line_spacing = int(line_h * 0.4)
    block_h = line_h * len(lines) + line_spacing * (len(lines) - 1)
    y = MARGIN_Y + (text_area_h - block_h) // 2

    for line in lines:
        line_w = draw.textlength(line, font=quote_font)
        x = (IMAGE_W - line_w) / 2
        draw.text((x, y), line, font=quote_font, fill=QUOTE_COLOR)
        y += line_h + line_spacing

    # Accent separator line
    y += gap // 2
    line_x0 = IMAGE_W // 2 - 40
    line_x1 = IMAGE_W // 2 + 40
    draw.rectangle([line_x0, y, line_x1, y + accent_line_h], fill=ACCENT_COLOR)
    y += accent_line_h + gap // 2

    # Attribution
    attribution = f"— {quote['author']}, {quote['year']}"
    attr_w = draw.textlength(attribution, font=attr_font)
    draw.text(((IMAGE_W - attr_w) / 2, y), attribution, font=attr_font, fill=ATTR_COLOR)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def alt_text(quote: dict) -> str:
    source = quote.get("source", "")
    source_str = f" [{source}]" if source else ""
    return f'"{quote["text"]}" — {quote["author"]}, {quote["year"]}{source_str}'
