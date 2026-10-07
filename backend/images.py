"""Serve product photos with the black bars trimmed off (Problem 11 follow-up).

73 of the 102 catalogue photos have black bars baked into the files. The originals in data/products/
are left untouched: on first request each photo is cropped to its real content, padded back to a
square with the photo's own background color, and cached in backend/.image_cache/.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

BAR_LUMA = 28  # pixels darker than this count as "bar black" (allows for JPEG noise)
MIN_BAR_FRACTION = 0.02  # only trim if the bars cover at least 2% of the width/height
FILL_THRESHOLDS = (60, 35, 15)  # tried in order: looser fills absorb more JPEG halo, stricter ones are safer
WHITE = (255, 255, 255)
LEAK_LUMA = 18  # filled pixels brighter than this were garment, not background
MAX_LEAK = 0.01  # reject a fill that whitened more than 1% of the image's garment-dark pixels


def _content_box(img: Image.Image) -> tuple[int, int, int, int] | None:
    """Bounding box of everything that isn't near-black bar, or None if there are no bars to trim."""
    mask = img.convert("L").point(lambda v: 255 if v > BAR_LUMA else 0)
    box = mask.getbbox()
    if box is None:
        return None
    left, top, right, bottom = box
    w, h = img.size
    trimmed_x = (left + (w - right)) / w
    trimmed_y = (top + (h - bottom)) / h
    if trimmed_x < MIN_BAR_FRACTION and trimmed_y < MIN_BAR_FRACTION:
        return None
    return box


def _flood_white(img: Image.Image, thresh: int) -> Image.Image:
    out = img.copy()
    w, h = out.size
    gray = out.convert("L")
    step = max(1, min(w, h) // 60)
    seeds = [(x, y) for x in range(0, w, step) for y in (0, h - 1)] + [(x, y) for y in range(0, h, step) for x in (0, w - 1)]
    for xy in seeds:
        if gray.getpixel(xy) <= BAR_LUMA and out.getpixel(xy) != WHITE:
            ImageDraw.floodfill(out, xy, WHITE, thresh=thresh)
    return out


def _leak_share(before: Image.Image, after: Image.Image) -> float:
    """Share of the image the fill turned white although it was NOT background-black (luma > LEAK_LUMA).
    Real backgrounds are ~0-15 luma, so on good photos this stays under 0.1% (JPEG halo); when the fill
    leaks into a dark navy garment (luma 20-50) it jumps to 45-60%."""
    gray = before.convert("L").get_flattened_data()
    b, a = before.get_flattened_data(), after.get_flattened_data()
    leaked = sum(1 for g, p, q in zip(gray, b, a) if q == WHITE and p != WHITE and g > LEAK_LUMA)
    return leaked / max(1, len(gray))


def _whiten_black_background(img: Image.Image) -> Image.Image:
    """Some photos have a fully black background, not just side bars. Flood-fill it to white from the
    edges inward. The fill only spreads through connected near-black pixels, so most garments stop it.
    Very dark garments (e.g. a near-black navy hoodie) can let it leak in, so we try progressively
    stricter thresholds and keep the black background rather than ever damage the product."""
    for thresh in FILL_THRESHOLDS:
        filled = _flood_white(img, thresh)
        if _leak_share(img, filled) < MAX_LEAK:
            return filled
    return img


def trim_bars(img: Image.Image) -> Image.Image:
    img = ImageOps.exif_transpose(img).convert("RGB")
    box = _content_box(img)
    if box is None:
        return img
    content = img.crop(box)
    if content.convert("L").getpixel((1, 1)) <= BAR_LUMA:  # still black after cropping: black background
        content = _whiten_black_background(content)
    # pad back to a square using the photo's own background (its corner color, usually white or light gray)
    bg = content.getpixel((2, 2))
    side = max(content.size)
    square = Image.new("RGB", (side, side), bg)
    square.paste(content, ((side - content.width) // 2, (side - content.height) // 2))
    return square


def trimmed_photo(source: Path, cache_dir: Path) -> Path:
    """Path to the trimmed copy of `source`, regenerating it if the original changed."""
    cache_dir.mkdir(exist_ok=True)
    target = cache_dir / source.name
    if not target.exists() or target.stat().st_mtime < source.stat().st_mtime:
        with Image.open(source) as img:
            trim_bars(img).save(target, "JPEG", quality=88, optimize=True)
    return target
