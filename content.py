import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRODUCTS = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
PRODUCTS_BY_SLUG = {item["slug"]: item for item in PRODUCTS}

GROUPS = []
for item in PRODUCTS:
    if item["group"] not in GROUPS:
        GROUPS.append(item["group"])

BUSINESS = {
    "name": "Vittorio Gourmet Espresso",
    "short_name": "Vittorio",
    "phone_display": "+357 99 766 848",
    "phone_tel": "+35799766848",
    "email_public": "info@vittoriocaffee.com",
    "email_service": "pantzosantonis@gmail.com",
    "street": "Synergasias 17",
    "locality": "Kiti",
    "postal_code": "7550",
    "region": "Larnaca",
    "country": "Cyprus",
    "hours": "Monday–Sunday, 08:00–20:00",
    "maps": "https://www.google.com/maps/search/?api=1&query=Synergasias+17%2C+Kiti+7550%2C+Larnaca%2C+Cyprus",
    "social": [
        {"label": "Facebook", "href": "https://www.facebook.com/profile.php?id=100095007198368"},
        {"label": "Instagram", "href": "https://www.instagram.com/vittoriogourmetespresso.cy/"},
        {"label": "YouTube", "href": "https://www.youtube.com/channel/UCHSA0RFth6yxoTQsBRupfdw"},
    ],
}

NAV = [
    {"label": "Catalogue", "endpoint": "products"},
    {"label": "Philosophy", "endpoint": "philosophy"},
    {"label": "Story", "endpoint": "story"},
    {"label": "Visit", "endpoint": "visit"},
    {"label": "Journal", "endpoint": "journal"},
    {"label": "Contact", "endpoint": "contact"},
]

ARTICLES = [
    {
        "slug": "horeca-2019",
        "title": "A stand at HO.RE.CA. 2019",
        "date": "2019-02-08",
        "date_label": "8–11 February 2019",
        "summary": "The company posted an invitation to meet the team at HO.RE.CA. 2019 in Athens.",
        "body": [
            "Vittorio Gourmet Espresso published a short invitation to HO.RE.CA., the hospitality exhibition, in 2019.",
            "The post names Metropolitan Expo, Hall 1, stand C12/D11, and the dates 8–11 February 2019.",
            "It asks visitors to come and hear about the products. It does not describe a prize, a talk, or a product launch.",
        ],
    },
    {
        "slug": "horeca-2019-thanks",
        "title": "After the 14th HORECA",
        "date": "2019-02-11",
        "date_label": "February 2019",
        "summary": "A follow-up post, written in Greek, thanks people who visited the stand.",
        "body": [
            "A second post says the 14th HORECA 2019 had ended. The original text is in Greek.",
            "It thanks visitors for coming and for their interest, and says the team hoped to meet them again the following year.",
            "The post does not publish attendance figures or name a product that debuted there.",
        ],
    },
]

FAQ = [
    {
        "question": "Where is the counter?",
        "answer": "Synergasias 17, Kiti 7550, in the Larnaca district of Cyprus. That is the only address published on the current website.",
    },
    {
        "question": "When is it open?",
        "answer": "The site lists Monday to Sunday, 08:00–20:00. It does not say whether those hours are for a café, a trade counter, or both.",
    },
    {
        "question": "Can I pay on this preview?",
        "answer": "No. The live shop’s returns page says the website does not currently take payment. Use the contact form, phone, or email to ask about an order.",
    },
    {
        "question": "How do returns work?",
        "answer": "Unopened, unused goods can be returned within 30 days of purchase for a refund. The customer pays return shipping unless the company made the error. Write to pantzosantonis@gmail.com or call +357 99 766 848 with the order number.",
    },
    {
        "question": "Are the prices final?",
        "answer": "Catalogue prices are copied from the public shop and are shown plus VAT. Records with no price are marked “Price not published” rather than shown as zero.",
    },
    {
        "question": "Do you publish dietary labels?",
        "answer": "Only when the product page states them. There is no allergen grid on the current shop, so this site does not add vegan, gluten-free, or similar marks.",
    },
]

HERO = {
    "file": "brand/hero.jpg",
    "width": 650,
    "height": 650,
    "alt": "Person drinking from a Vittorio Gourmet Espresso cup, the photograph used on the current homepage.",
}
