"""Build uniform, sharp WebP versions of the product photos and the homepage hero.

Every packshot is trimmed to its content, centred on a white square with the same
margin, and saved at two widths so cards stay crisp on phones and retina screens.
Originals are left untouched. Run after adding or replacing a product photo:

    python tools/optimize_images.py      (needs Pillow: pip install pillow)
"""

import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "static" / "images"
PRODUCTS_PATH = ROOT / "data" / "products.json"
WEB_DIR = "products/web"
SIZES = {"sm": 600, "lg": 1200}
MARGIN = 0.14
QUALITY = 84


def flatten(image):
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.getchannel("A"))
        return background
    return image.convert("RGB")


def trim(image):
    white = Image.new("RGB", image.size, (255, 255, 255))
    diff = ImageChops.difference(image, white).convert("L").point(lambda value: 255 if value > 14 else 0)
    box = diff.getbbox()
    return image.crop(box) if box else image


def square(image):
    side = int(max(image.size) * (1 + MARGIN))
    canvas = Image.new("RGB", (side, side), (255, 255, 255))
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return canvas


def save_webp(image, width, target):
    width = min(width, image.width)
    resized = image.resize((width, width), Image.LANCZOS) if width != image.width else image
    resized = resized.filter(ImageFilter.UnsharpMask(radius=1.0, percent=45, threshold=2))
    target.parent.mkdir(parents=True, exist_ok=True)
    resized.save(target, "WEBP", quality=QUALITY, method=6)
    return width


def build_products():
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    for item in products:
        source = IMAGES / item["image"]["file"]
        framed = square(trim(flatten(Image.open(source))))
        web = {}
        for label, width in SIZES.items():
            rel = f"{WEB_DIR}/{item['slug']}-{label}.webp"
            web[label] = {"file": rel, "width": save_webp(framed, width, IMAGES / rel)}
        item["image"]["web"] = web
    PRODUCTS_PATH.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(products)


# Real packshots for the homepage hero, cut out of their white backgrounds.
HERO_PRODUCTS = [
    "espresso-grande",
    "costa-rica",
    "espresso-100-arabica",
    "blue-night",
    "chocolate-with-bueno-biscuit-no-3",
    "milkshake-chocolate",
    "smoothies-syrups-mango",
]


def cutout(path, tolerance=26):
    """Make the studio background transparent, keeping matching colours inside the product.

    The background colour is sampled from the corners, so white and cream sweeps both work.
    """
    source = Image.open(path)
    if source.mode in ("P", "LA") or (source.mode == "RGB" and "transparency" in source.info):
        source = source.convert("RGBA")
    if source.mode == "RGBA" and source.getpixel((0, 0))[3] == 0:
        return source.crop(source.getchannel("A").getbbox())
    image = source.convert("RGB")
    corners = [image.getpixel(point) for point in ((2, 2), (image.width - 3, 2), (2, image.height - 3), (image.width - 3, image.height - 3))]
    key = tuple(sum(channel) // len(corners) for channel in zip(*corners))
    distance = ImageChops.difference(image, Image.new("RGB", image.size, key))
    near_key = ImageChops.lighter(ImageChops.lighter(distance.getchannel("R"), distance.getchannel("G")), distance.getchannel("B"))
    mask = near_key.point(lambda value: 255 if value < tolerance else 0)
    width, height = mask.size
    edges = [(x, y) for x in range(0, width, 6) for y in (0, height - 1)]
    edges += [(x, y) for y in range(0, height, 6) for x in (0, width - 1)]
    for point in edges:
        if mask.getpixel(point) == 255:
            ImageDraw.floodfill(mask, point, 128)
    alpha = mask.point(lambda value: 0 if value == 128 else 255)
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    rgba = image.copy()
    rgba.putalpha(alpha)
    return rgba.crop(alpha.getbbox())


def build_hero():
    products = {item["slug"]: item for item in json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))}
    target = IMAGES / "hero"
    target.mkdir(parents=True, exist_ok=True)
    for slug in HERO_PRODUCTS:
        piece = cutout(IMAGES / products[slug]["image"]["file"])
        piece.thumbnail((900, 900), Image.LANCZOS)
        piece.save(target / f"{slug}.webp", "WEBP", quality=88, method=6)
    build_share_image(target)


# Pieces for the B2B "build your counter" scene: (output name, source image, tolerance).
SCENE_PIECES = [
    # Official manufacturer photos (downloaded with the owner's OK on 2026-09-24), cycled on the counter.
    ("machine-appia-life", "machines/brand/appia-life.png", 26),
    ("machine-sanremo", "machines/brand/sanremo-cafe-racer.png", 12),
    ("machine-expobar", "machines/brand/expobar-onyx-pro.jpg", 30),
    ("waffle-mix", "products/waffle-mix.jpg", 26),
    ("soft-ice-cream", "products/soft-ice-cream-1kg.png", 26),
    ("cups", "products/glasses-4-oz-8-oz-12-oz-16-oz.png", 22),
    ("lids", "products/black-lids-12-16oz.png", 55),
    ("straws", "products/frappe-straws-x-500.png", 34),
]


def build_scene():
    target = IMAGES / "scene"
    target.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for name, source, tolerance in SCENE_PIECES:
        piece = cutout(IMAGES / source, tolerance)
        piece.thumbnail((900, 900), Image.LANCZOS)
        piece.save(target / f"{name}.webp", "WEBP", quality=88, method=6)
        sizes[name] = piece.size
    return sizes


def build_share_image(folder):
    """1200x630 link-preview image: the same packshots on the site's espresso background."""
    canvas = Image.new("RGB", (1200, 630), (20, 12, 8))
    glow = Image.new("L", (1200, 630), 0)
    ImageDraw.Draw(glow).ellipse((500, 120, 1500, 900), fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    canvas = Image.composite(Image.new("RGB", canvas.size, (120, 70, 38)), canvas, glow)
    heights = {"espresso-grande": 470, "costa-rica": 500, "espresso-100-arabica": 470, "blue-night": 270,
               "chocolate-with-bueno-biscuit-no-3": 290, "milkshake-chocolate": 260, "smoothies-syrups-mango": 380}
    pieces = []
    for slug in HERO_PRODUCTS:
        piece = Image.open(folder / f"{slug}.webp").convert("RGBA")
        height = heights[slug]
        pieces.append(piece.resize((round(piece.width * height / piece.height), height), Image.LANCZOS))
    gap = 18
    room = 1200 - 2 * 50 - gap * (len(pieces) - 1)
    scale = min(1.0, room / sum(piece.width for piece in pieces))
    pieces = [piece.resize((round(piece.width * scale), round(piece.height * scale)), Image.LANCZOS) for piece in pieces]
    left = (1200 - sum(piece.width for piece in pieces) - gap * (len(pieces) - 1)) // 2
    for piece in pieces:
        canvas.paste(piece, (left, 590 - piece.height), piece)
        left += piece.width + gap
    logo_left = 60
    for name in ("logo-footer.png", "jean-paul.png"):
        logo = Image.open(IMAGES / "brand" / name).convert("RGBA")
        logo = logo.resize((round(logo.width * 96 / logo.height), 96), Image.LANCZOS)
        canvas.paste(logo, (logo_left, 56), logo)
        logo_left += logo.width + 48
    canvas.save(IMAGES / "brand" / "share.jpg", "JPEG", quality=86, optimize=True)


if __name__ == "__main__":
    count = build_products()
    build_hero()
    scene = build_scene()
    print(f"optimised {count} product photos, the hero packshots and the B2B scene: {scene}")
