import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
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
    "email_public": "info@vittoriocaffee.com",
    "email_service": "pantzosantonis@gmail.com",
    "street": "Synergasias 17",
    "locality": "Kalo Xorio",
    "postal_code": "7550",
    "region": "Larnaca",
    "country": "Cyprus",
    "hours": "Monday–Sunday, 08:00–20:00",
    "maps": "https://www.google.com/maps/search/?api=1&query=Synergasias+17%2C+Kalo+Xorio+7550%2C+Larnaca%2C+Cyprus",
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
    {"label": "Supply", "endpoint": "supply"},
    {"label": "Machines", "endpoint": "machines"},
    {"label": "Order", "endpoint": "order"},
    {"label": "Visit", "endpoint": "visit"},
    {"label": "Contact", "endpoint": "contact"},
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
        "answer": "From the depot at Synergasias 17, Kalo Xorio 7550, Larnaca. A car takes orders to cafés and bars anywhere in Cyprus. We do not ship abroad.",
    },
    {
        "question": "When is the depot open?",
        "answer": "Every day, 08:00–20:00.",
    },
    {
        "question": "How does an order get confirmed?",
        "answer": "Build the list on this site. We confirm the order and the payment on Viber before the car leaves Kalo Xorio. Card payment is not taken on the page. Prices are plus VAT.",
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
}
