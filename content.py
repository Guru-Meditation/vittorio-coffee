import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

_PACK_FACT = re.compile(r"^\d+ (g|kg|ml|ltr|pcs)$")


def _format_pack(raw):
    if not raw:
        return None
    if raw == "500 g":
        return "0.5 kg"
    if raw.endswith(" g"):
        return raw.replace(" g", "gr")
    return raw


def _pack_from_facts(facts):
    for fact in facts or []:
        if _PACK_FACT.match(fact):
            return fact
    return None


def catalog_pack_label(item):
    """Short pack size for catalogue cards; uses product pack field or weight in facts."""
    raw = None
    if isinstance(item, dict):
        raw = item.get("pack") or _pack_from_facts(item.get("facts"))
    else:
        raw = _pack_from_facts(item)
    return _format_pack(raw)


PRODUCTS = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
GROUP_ORDER = [
    "Coffee",
    "Aromatic chocolates",
    "Chocolate powders",
    "Soft ice cream",
    "Coffee syrups",
    "Smoothies",
    "Milkshakes",
    "Teas",
    "Café mixes",
    "Granitas",
    "Serviceware",
]
PRODUCTS.sort(key=lambda item: GROUP_ORDER.index(item["group"]) if item["group"] in GROUP_ORDER else len(GROUP_ORDER))
PRODUCTS_BY_SLUG = {item["slug"]: item for item in PRODUCTS}

GROUPS = []
for item in PRODUCTS:
    if item["group"] not in GROUPS:
        GROUPS.append(item["group"])

# The two houses this Cyprus representative carries. Facts come from vittorio.gr and jeanpaul.gr.
BRANDS = [
    {
        "slug": "vittorio",
        "name": "Vittorio Gourmet Espresso",
        "short": "Vittorio",
        "logo": {"file": "brand/logo-footer.png", "width": 678, "height": 275},
        "line": "Italian-style espresso since 2000",
        "body": "Espresso blends, single origins, Greek and filter coffee, and chocolate.",
        "site": "https://www.vittorio.gr/",
        "showcase": ["espresso-grande", "costa-rica", "chocolate-powder-la-vittoria-classic"],
    },
    {
        "slug": "jean-paul-lab",
        "name": "Jean Paul Lab",
        "short": "Jean Paul Lab",
        "logo": {"file": "brand/jean-paul.png", "width": 294, "height": 156},
        "line": "Premium beverages and dessert mixes",
        "body": "Teas, smoothies, milkshakes, granitas, syrups and dessert mixes.",
        "site": "https://www.jeanpaul.gr/index.php/en",
        "showcase": ["smoothies-syrups-mango", "blue-night", "chocolate-with-bueno-biscuit-no-3"],
    },
]
BRANDS_BY_SLUG = {brand["slug"]: brand for brand in BRANDS}
BRAND_FILTERS = [
    {"slug": "vittorio", "label": "Vittorio"},
    {"slug": "jean-paul-lab", "label": "Jean Paul Lab"},
    {"slug": "essentials", "label": "Café essentials"},
]
BRAND_LABELS = {entry["slug"]: entry["label"] for entry in BRAND_FILTERS}
for brand in BRANDS:
    brand["count"] = sum(1 for item in PRODUCTS if item.get("brand") == brand["slug"])
    brand["products"] = [PRODUCTS_BY_SLUG[slug] for slug in brand["showcase"]]

ANNOUNCEMENT = "Official Cyprus representative of Vittorio Gourmet Espresso and Jean Paul Lab"

ORDER = {
    "vat_rate": "0.05",
    "vat_label": "5%",
    "free_delivery_min": "40",
    "delivery_fee": "5.00",
}

BUSINESS = {
    "name": "Vittorio Gourmet Espresso",
    "short_name": "Vittorio",
    "email_service": "pantzosantonis@gmail.com",
    "locality": "Kalo Xorio",
    "postal_code": "7550",
    "region": "Larnaca",
    "country": "Cyprus",
    "maps": "https://www.google.com/maps/search/?api=1&query=Kalo+Xorio%2C+Larnaca%2C+Cyprus",
    "viber": "viber://chat?number=%2B35799766848",
    "phone": "+35799766848",
    # Google Business Profile "Ask for reviews" link; the footer shows it once set.
    "reviews": "https://g.page/r/CRkhDH0foV3FEBM/review",
    "trustpilot": "",
    # Google Search Console "HTML tag" verification codes (the content="..." values), one per property.
    "search_console": [
        "WmBAxmaZormtC7pr3mufzgV5-ozEobNwUEvtuKtnXAI",  # vittorio-coffee.onrender.com
        "MPQErzrMwgPCQpFPoQi6eGpg-k3ub2vmR3FZBdH916g",  # vittoriocyprus.com
    ],
    "delivery": "Delivery to cafés, bars and hotels across Cyprus.",
    "machines": ["Appia Life", "Sanremo", "Expobar"],
    "social": [
        {"label": "Facebook", "href": "https://www.facebook.com/profile.php?id=100095007198368"},
        {"label": "Instagram", "href": "https://www.instagram.com/vittoriogourmetespresso.cy/"},
        {"label": "YouTube", "href": "https://www.youtube.com/channel/UCHSA0RFth6yxoTQsBRupfdw"},
    ],
}

NAV = [
    {"label": "Home", "endpoint": "home"},
    {"label": "Catalogue", "endpoint": "products"},
    {"label": "Order", "endpoint": "order"},
    {"label": "B2B Services", "endpoint": "cyprus"},
    {"label": "Contact", "endpoint": "contact"},
]

CYPRUS_B2B = {
    "eyebrow": "B2B Services",
    "title": "Vittorio B2B Services",
    "lede": "Everything a café needs, from one supplier.",
    # Scrolling through the chapters fills the counter scene, piece by piece.
    "chapters": [
        {"key": "machine", "label": "Machines", "title": "Your espresso machine",
         "body": "Appia Life, Sanremo or Expobar, on loan at no charge while we work together."},
        {"key": "setup", "label": "Setup", "title": "Installed and explained",
         "body": "Free setup guidance and machine training for your staff."},
        {"key": "coffee", "label": "Coffee", "title": "Vittorio coffee",
         "body": "Espresso blends, single origins, Greek and filter coffee."},
        {"key": "menu", "label": "Beverages", "title": "Beyond coffee",
         "body": "Jean Paul Lab smoothies, milkshakes, teas, granitas and dessert mixes."},
        {"key": "essentials", "label": "Essentials", "title": "Cups, lids and straws",
         "body": "Serviceware for takeaway and the bar."},
        {"key": "delivery", "label": "Delivery", "title": "Delivered across Cyprus",
         "body": "From Kalo Xorio to your café. Cash on delivery, free over €40."},
        {"key": "service", "label": "Service", "title": "Machine service",
         "body": "We service the machines we supply."},
    ],
    # Real cut-out photos on the counter: step = chapter that brings it in; x/b/w in % of the scene.
    "scene": [
        {"src": "hero/espresso-grande.webp", "w": 371, "h": 900, "step": 2, "x": 2, "b": 30, "size": 11, "z": 2, "alt": "Vittorio Espresso Grande"},
        {"src": "hero/costa-rica.webp", "w": 329, "h": 707, "step": 2, "x": 12.5, "b": 30, "size": 11, "z": 2, "alt": "Vittorio Costa Rica"},
        {"src": "hero/espresso-100-arabica.webp", "w": 381, "h": 900, "step": 2, "x": 23, "b": 30, "size": 11, "z": 2, "alt": "Vittorio Espresso 100% Arabica"},
        {"src": "hero/blue-night.webp", "w": 478, "h": 519, "step": 3, "x": 64.5, "b": 30, "size": 12, "z": 2, "alt": "Jean Paul Lab Blue Night tea"},
        {"src": "hero/chocolate-with-bueno-biscuit-no-3.webp", "w": 825, "h": 900, "step": 3, "x": 76, "b": 30, "size": 12, "z": 2, "alt": "Jean Paul Lab aromatic chocolate"},
        {"src": "hero/smoothies-syrups-mango.webp", "w": 262, "h": 808, "step": 3, "x": 88.5, "b": 30, "size": 6, "z": 2, "alt": "Jean Paul Lab mango smoothie"},
        {"src": "scene/cups.webp", "w": 900, "h": 402, "step": 4, "x": 1, "b": 4, "size": 26, "z": 4, "alt": "Vittorio cups"},
        {"src": "scene/lids.webp", "w": 748, "h": 586, "step": 4, "x": 27, "b": 4, "size": 13, "z": 4, "alt": "Black lids"},
        {"src": "scene/straws.webp", "w": 895, "h": 569, "step": 4, "x": 40, "b": 4, "size": 15, "z": 4, "alt": "Straws"},
        {"src": "scene/waffle-mix.webp", "w": 735, "h": 575, "step": 3, "x": 55, "b": 4, "size": 19, "z": 4, "alt": "Jean Paul Lab waffle mix"},
        {"src": "hero/milkshake-chocolate.webp", "w": 438, "h": 470, "step": 3, "x": 74, "b": 4, "size": 13, "z": 4, "alt": "Jean Paul Lab chocolate milkshake"},
        {"src": "scene/soft-ice-cream.webp", "w": 280, "h": 463, "step": 3, "x": 87.5, "b": 4, "size": 10, "z": 4, "alt": "Soft ice cream"},
    ],
    # Official manufacturer photos, shown one at a time in the same spot and cycled while in view.
    "machines": [
        {"src": "scene/machine-appia-life.webp", "w": 900, "h": 559, "name": "Nuova Simonelli Appia Life"},
        {"src": "scene/machine-sanremo.webp", "w": 774, "h": 512, "name": "Sanremo Café Racer"},
        {"src": "scene/machine-expobar.webp", "w": 465, "h": 332, "name": "Expobar Onyx Pro"},
    ],
    "machine_slot": {"x": 33.5, "b": 29, "size": 31},
    "towns": [
        {"name": "Nicosia", "x": 183.8, "y": 119.8},
        {"name": "Limassol", "x": 136.6, "y": 206.2},
        {"name": "Paphos", "x": 45.3, "y": 190.0},
        {"name": "Larnaca", "x": 222.1, "y": 164.8},
        {"name": "Ayia Napa", "x": 276.6, "y": 152.2},
    ],
    "base": {"name": "Kalo Xorio", "x": 208.8, "y": 159.4},
    # Simplified coastline, projected from real coordinates (see git history for the generator).
    "island": "M23.3 132.4 L39.5 143.2 L49.8 139.6 L64.5 123.4 L83.6 118.0 L101.3 119.8 L113.1 109.0 L120.5 78.4 L138.1 85.6 L177.9 89.2 L219.1 85.6 L263.3 78.4 L292.8 65.8 L322.2 47.8 L351.7 31.6 L364.9 24.4 L354.6 35.2 L329.6 56.8 L304.5 74.8 L278.0 91.0 L267.7 114.4 L270.7 128.8 L282.4 146.8 L289.8 157.6 L276.6 155.8 L255.9 157.6 L241.2 154.0 L225.0 166.6 L223.5 182.8 L197.0 197.2 L174.9 202.6 L145.5 206.2 L136.6 209.8 L127.8 217.0 L123.4 227.8 L113.1 218.8 L98.4 215.2 L86.6 213.4 L64.5 204.4 L43.9 195.4 L32.1 175.6 L27.7 150.4 Z",
}

MACHINE_PROGRAMMES = [
    {
        "brand": "Appia Life",
        "image": "machines/apia-vittoria-ii.jpg",
        "alt": "Appia Life three-group commercial espresso machine in black and stainless steel.",
        "models": ["Vittoria II", "Compact", "Bar"],
    },
    {
        "brand": "Sanremo",
        "image": "machines/sanremo-opera.jpg",
        "alt": "Sanremo Café Racer three-group espresso machine in black and stainless steel.",
        "models": ["Opera", "Cube", "You"],
    },
    {
        "brand": "Expobar",
        "image": "machines/expobar-elegance.jpg",
        "alt": "Expobar two-group commercial espresso machine in polished stainless steel with black accents.",
        "models": ["Brewtus IV", "Elegance", "Office"],
    },
]

ARTICLES = [
    {
        "slug": "horeca-2019",
        "title": "A stand at HO.RE.CA. 2019",
        "date": "2019-02-08",
        "date_label": "8–11 February 2019",
        "summary": "Vittorio met the trade at HO.RE.CA. 2019, Metropolitan Expo, Athens.",
        "body": [
            "In February 2019 Vittorio took a stand at HO.RE.CA., the hospitality exhibition in Athens.",
            "The invitation named Metropolitan Expo, Hall 1, stand C12/D11, and the dates 8–11 February.",
            "The team was there to talk through the range with people who run bars, cafés, and hotels.",
        ],
    },
    {
        "slug": "horeca-2019-thanks",
        "title": "After the 14th HORECA",
        "date": "2019-02-11",
        "date_label": "February 2019",
        "summary": "A note of thanks after the 14th HORECA, written first in Greek.",
        "body": [
            "When the 14th HORECA closed, Vittorio posted a thank-you. The original note is in Greek.",
            "It thanks everyone who came to the stand, and looks ahead to meeting them again the following year.",
        ],
    },
]

FAQ = [
    {
        "question": "Where do you deliver from?",
        "answer": "From Kalo Xorio, Larnaca, to anywhere in Cyprus. We do not ship abroad.",
    },
    {
        "question": "How does an order get confirmed?",
        "answer": "Order on this site or on Viber. We confirm every order before delivery. Prices exclude VAT; payment is cash on delivery.",
    },
    {
        "question": "How do returns work?",
        "answer": "Unopened, unused goods can be returned within 30 days for a refund. You pay return shipping unless the error was ours. Send the order number by email to pantzosantonis@gmail.com, or open Viber.",
    },
    {
        "question": "Are the prices final?",
        "answer": "Catalogue prices are the published trade prices, shown plus VAT. A line marked “Price not published” is confirmed before delivery.",
    },
    {
        "question": "Who do you supply?",
        "answer": "Cafés, bars, hotels and retail customers across Cyprus.",
    },
    {
        "question": "Which machines do you place?",
        "answer": "Appia Life, Sanremo and Expobar, at no charge for partners, with free setup and training.",
    },
    {
        "question": "Do you mark dietary claims?",
        "answer": "Only when the product itself states them. We do not add vegan, gluten-free, or similar marks that the listing does not carry.",
    },
]

# Real packshots on the counter (built by tools/optimize_images.py); share.jpg is the link preview.
HERO = {
    "file": "brand/share.jpg",
    "alt": "Vittorio coffee bags beside Jean Paul Lab tea, aromatic chocolate, milkshake and fruit smoothie packs.",
    "headline": "Vittorio Gourmet Espresso Deliveries all over Cyprus",
    "packs": [
        {"slug": "espresso-grande", "kind": "bag", "width": 371, "height": 900},
        {"slug": "costa-rica", "kind": "bag", "width": 329, "height": 707},
        {"slug": "espresso-100-arabica", "kind": "bag", "width": 381, "height": 900, "wide_only": True},
        {"slug": "blue-night", "kind": "tin", "width": 478, "height": 519},
        {"slug": "chocolate-with-bueno-biscuit-no-3", "kind": "tin", "width": 825, "height": 900},
        {"slug": "milkshake-chocolate", "kind": "tin", "width": 438, "height": 470, "wide_only": True},
        {"slug": "smoothies-syrups-mango", "kind": "bottle", "width": 262, "height": 808},
    ],
}
# Each pack on the counter explains itself in a hover card and opens its catalogue category.
for pack in HERO["packs"]:
    product = PRODUCTS_BY_SLUG[pack["slug"]]
    pack["name"] = product["name"]
    pack["group"] = product["group"]
    pack["description"] = product.get("description", "")
    pack["price_label"] = product["price_label"]
    pack["size"] = catalog_pack_label(product)
    pack["brand"] = BRAND_LABELS.get(product.get("brand"), "")
