"""Download the public Vittorio shop logo and product photos into static/images."""

import json
import re
import struct
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / "data" / "products.json"
OUT = ROOT / "static" / "images" / "products"
BRAND = ROOT / "static" / "images" / "brand"
API = "https://vittoriocoffee.com/wp-json/wc/store/v1/products?per_page=50"
HEADERS = {"User-Agent": "Mozilla/5.0"}

BRAND_FILES = {
    "logo.png": "https://vittoriocoffee.com/wp-content/uploads/2023/07/logo-se-mayro.png",
    "logo-footer.png": "https://vittoriocoffee.com/wp-content/uploads/2023/07/sjnsajcsac.png",
    "mark.png": "https://vittoriocoffee.com/wp-content/uploads/2023/07/vswgfewfaefa.png",
    "jean-paul.png": "https://vittoriocoffee.com/wp-content/uploads/2023/09/jpl.png",
    "hero.jpg": "https://vittoriocoffee.com/wp-content/uploads/2023/08/scascasc.jpg",
}


def fetch(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def largest_src(image):
    srcset = image.get("srcset") or ""
    best_url = image.get("src") or ""
    best_width = 0
    for part in srcset.split(","):
        piece = part.strip().split()
        if len(piece) < 2 or not piece[1].endswith("w"):
            continue
        width = int(piece[1][:-1])
        if width > best_width:
            best_width = width
            best_url = piece[0]
    return best_url


def dimensions(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        index = 2
        while index < len(data) - 8:
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                height, width = struct.unpack(">HH", data[index + 5 : index + 9])
                return width, height
            if marker in (0xD8, 0xD9):
                index += 2
                continue
            length = struct.unpack(">H", data[index + 2 : index + 4])[0]
            index += 2 + length
    return 800, 800


def extension(url, data):
    match = re.search(r"\.(png|jpe?g|webp|gif)(?:$|\?)", url, re.I)
    if match:
        ext = match.group(1).lower()
        return "jpg" if ext == "jpeg" else ext
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    return "jpg"


def main():
    request = urllib.request.Request(API, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=60) as response:
        remote = json.load(response)
    by_slug = {}
    OUT.mkdir(parents=True, exist_ok=True)
    for product in remote:
        images = product.get("images") or []
        if not images:
            continue
        url = largest_src(images[0])
        if not url:
            continue
        data = fetch(url)
        ext = extension(url, data)
        filename = f"{product['slug']}.{ext}"
        path = OUT / filename
        path.write_bytes(data)
        width, height = dimensions(data)
        by_slug[product["slug"]] = {
            "file": f"products/{filename}",
            "width": width,
            "height": height,
            "alt": product["name"],
        }
        print("product", filename, width, height)

    BRAND.mkdir(parents=True, exist_ok=True)
    for name, url in BRAND_FILES.items():
        try:
            data = fetch(url)
        except Exception as error:
            hostinger = url.replace(
                "https://vittoriocoffee.com",
                "https://lightsteelblue-magpie-267841.hostingersite.com",
            )
            print("retry", name, error)
            data = fetch(hostinger)
        (BRAND / name).write_bytes(data)
        print("brand", name, dimensions(data))

    products = json.loads(PRODUCTS.read_text(encoding="utf-8"))
    missing = []
    for product in products:
        image = by_slug.get(product["slug"])
        if image:
            product["image"] = image
        else:
            missing.append(product["slug"])
            product["image"] = None
    PRODUCTS.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    print("updated", len(products), "missing", missing)


if __name__ == "__main__":
    main()
