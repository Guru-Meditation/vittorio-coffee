"""Refresh data/products.json summaries from the public WooCommerce shop HTML descriptions."""

import html
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_PATH = ROOT / "data" / "products.json"
API = "https://vittoriocoffee.com/wp-json/wc/store/v1/products?per_page=100&page={page}"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def strip_markup(value):
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return dedupe_repeated(text)


def dedupe_repeated(text):
    """Shop pages sometimes repeat the same paragraph twice."""
    words = text.split()
    if len(words) < 12:
        return text
    half = len(words) // 2
    if words[:half] == words[half : half * 2]:
        return " ".join(words[:half])
    return text


def fetch_remote():
    by_slug = {}
    page = 1
    while True:
        url = API.format(page=page)
        request = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(request, timeout=60) as response:
            batch = json.load(response)
        if not batch:
            break
        for item in batch:
            slug = item["slug"]
            description = strip_markup(item.get("description") or "")
            short = strip_markup(item.get("short_description") or "")
            text = description or short
            if text:
                by_slug[slug] = text
        page += 1
    return by_slug


def main():
    remote = fetch_remote()
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    updated = 0
    missing = []
    for product in products:
        slug = product["slug"]
        if slug in remote:
            product["summary"] = remote[slug]
            updated += 1
        else:
            missing.append(slug)
    PRODUCTS_PATH.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"updated {updated} summaries from shop")
    print(f"unchanged {len(missing)}:", ", ".join(missing[:12]), "..." if len(missing) > 12 else "")


if __name__ == "__main__":
    main()
