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
    "delivery": "Car delivery to cafés and bars across Cyprus. Nothing leaves the island.",
    "machines": ["Apia Life", "Sanremo", "Expobar"],
    "social": [
        {"label": "Facebook", "href": "https://www.facebook.com/profile.php?id=100095007198368"},
        {"label": "Instagram", "href": "https://www.instagram.com/vittoriogourmetespresso.cy/"},
        {"label": "YouTube", "href": "https://www.youtube.com/channel/UCHSA0RFth6yxoTQsBRupfdw"},
    ],
}

NAV = [
    {"label": "Catalogue", "endpoint": "products"},
    {"label": "Order", "endpoint": "order"},
    {"label": "B2B Services", "endpoint": "cyprus"},
    {"label": "Contact", "endpoint": "contact"},
]

CYPRUS_B2B = {
    "eyebrow": "B2B Services",
    "title": "Vittorio B2B Services",
    "lede": "Your trusted partner in premium coffee and hospitality solutions.",
    "cards": [
        {
            "title": "Wholesale & Supply",
            "body": "Coffee, chocolate powders, and ingredients delivered to professionals across Cyprus. Reliable supply for high-volume partners.",
        },
        {
            "title": "Machines for Business",
            "body": "Espresso equipment placement for cafés, hotels, and restaurants. Setup guidance once a partnership starts.",
        },
        {
            "title": "Coffee for the Bar",
            "body": "Espresso and hospitality supply for cafés, bars, and hotels across the island.",
        },
        {
            "title": "Sourcing & Private Label",
            "body": "Custom blends and branded products for your business.",
        },
        {
            "title": "Training & Support",
            "body": "Barista training and coffee education for professional teams.",
        },
        {
            "title": "Become a Vittorio Partner",
            "body": "Join our network of cafés and bars supplied from Kalo Xorio.",
            "cta_label": "Contact us",
            "cta_endpoint": "contact",
        },
    ],
}

MACHINE_PROGRAMMES = [
    {
        "brand": "Apia Life",
        "image": "machines/apia-vittoria-ii.jpg",
        "alt": "Apia Life three-group commercial espresso machine in black and stainless steel.",
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
        "answer": "From the depot in Kalo Xorio, Larnaca. A car takes orders to cafés and bars anywhere in Cyprus. We do not ship abroad.",
    },
    {
        "question": "How does an order get confirmed?",
        "answer": "Build the list on this site and place the order. It is emailed to the depot. Payment is cash on delivery only — no card on this site. Prices are plus VAT. We may confirm details on Contact before the car leaves Kalo Xorio.",
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
        "answer": "Cafés and bars across Cyprus. The delivery is by car, from the Kalo Xorio depot, and it stays on the island.",
    },
    {
        "question": "Which machines do you place?",
        "answer": "Apia Life, Sanremo, and Expobar. The machine is offered with no charge for as long as the partnership continues. Setup guidance is free once we start working together.",
    },
    {
        "question": "Do you mark dietary claims?",
        "answer": "Only when the product itself states them. We do not add vegan, gluten-free, or similar marks that the listing does not carry.",
    },
]

HERO = {
    "file": "brand/hero-bar.jpg",
    "width": 1280,
    "height": 720,
    "alt": "Espresso pours into a black Vittorio cup on a white Sanremo machine while a barista in a black Vittorio shirt holds the cup steady.",
    "headline": "Vittorio Gourmet Espresso Deliveries all over Cyprus",
}
