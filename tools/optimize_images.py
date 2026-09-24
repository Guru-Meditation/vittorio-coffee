"""Build uniform, sharp WebP versions of the product photos and the homepage hero.

Every packshot is trimmed to its content, centred on a white square with the same
margin, and saved at two widths so cards stay crisp on phones and retina screens.
Originals are left untouched. Run after adding or replacing a product photo:

    python tools/optimize_images.py      (needs Pillow: pip install pillow)
"""

import json
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

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


def build_hero():
    source = Image.open(IMAGES / "brand" / "hero-bar.jpg").convert("RGB")
    for width in (960, 1280):
        height = round(source.height * width / source.width)
        resized = source if width == source.width else source.resize((width, height), Image.LANCZOS)
        resized.save(IMAGES / "brand" / f"hero-bar-{width}.webp", "WEBP", quality=86, method=6)


if __name__ == "__main__":
    count = build_products()
    build_hero()
    print(f"optimised {count} product photos and the hero")
