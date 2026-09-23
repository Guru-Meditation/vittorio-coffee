"""Build data/products.json from the public store export.

Facts (name, slug, price, categories) come from the WooCommerce store API.
Summaries are written for this site and are not the shop's product copy.
"""

import html
import json
import os
import re
from pathlib import Path

SOURCE = Path(os.environ.get("VITTORIO_SOURCE", os.path.join(os.environ["TEMP"], "vittorio-all.json")))
DEST = Path(__file__).resolve().parents[1] / "data" / "products.json"

COFFEE = {
    "costa-rica",
    "filter",
    "espresso-decafeine",
    "espresso-grande",
    "greek",
    "espresso-100-arabica",
    "single-origin-guatemala",
}

AROMATIC_RANGE = [
    "Chocolate with Banoffee No.1",
    "Chocolate with Black Forest & Passion Fruit No.2",
    "Chocolate with Bueno & Biscuit No.3",
    "Chocolate with Caramel & Mocha No.4",
    "Chocolate with Lemon & Biscuit No.5",
    "White with Strawberry No.6",
    "White with Mastiha & Rose No.7",
    "Chocolate with Orange & Ceylon Cinnamon No.8",
    "Chocolate with Salted Caramel No.9",
]


def strip(value):
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def money(product):
    prices = product.get("prices") or {}
    minor = int(prices.get("currency_minor_unit") or 2)
    raw = prices.get("price")
    try:
        amount = int(raw) / (10 ** minor)
    except (TypeError, ValueError):
        return None
    if amount <= 0:
        return None
    return f"{amount:.2f}"


def image_for(group):
    if group == "Coffee":
        return {
            "file": "beans-still.jpg",
            "width": 1152,
            "height": 864,
            "alt": "Roasted coffee beans in a dark bowl, an illustrative photo rather than product packaging.",
        }
    if group in {"Aromatic chocolates", "Chocolate powders", "Soft ice cream"}:
        return {
            "file": "cocoa-still.jpg",
            "width": 1024,
            "height": 1024,
            "alt": "Cocoa and dark chocolate on cream paper, an illustrative photo rather than product packaging.",
        }
    return {
        "file": "counter-room.jpg",
        "width": 1152,
        "height": 864,
        "alt": "A quiet supply counter in warm light, an illustrative photo rather than a shop interior.",
    }


def group_for(slug, categories):
    if slug in COFFEE:
        return "Coffee"
    if "Soft Ice Cream" in categories:
        return "Soft ice cream"
    if "Aromatic Chocolates" in categories:
        return "Aromatic chocolates"
    if slug in {"chocolate-powder-la-vittoria-classic", "chocolate-powder-paolo-chocolate", "freddoccino"}:
        return "Chocolate powders"
    if slug == "coffee-syrup-vanillia":
        return "Coffee syrups"
    if slug.startswith("smoothies-"):
        return "Smoothies"
    if slug.startswith("milkshake-"):
        return "Milkshakes"
    if "Teas" in categories:
        return "Teas"
    if slug in {"waffle-mix", "pancake-mix", "crepe-mix"}:
        return "Café mixes"
    if "Granitas" in categories:
        return "Granitas"
    return "Serviceware"


def describe(slug, name, group):
    if slug == "costa-rica":
        return (
            "Washed Arabica from Costa Rica. The shop lists Caturra and Catuai varieties, farms between 1,200 and 1,800 metres, about 2,400 mm of yearly rain, high acidity, a rich body, apricot and nectarine aroma, a chocolate note, and a clean sweet finish.",
            ["Single-origin Arabica", "Washed process"],
            None,
        )
    if slug == "single-origin-guatemala":
        return (
            "Single-origin Arabica from Guatemala. The published note stops at a distinct aroma and does not list altitude, process, or pack size.",
            ["Single-origin Arabica"],
            None,
        )
    if slug == "filter":
        return (
            "500 g of coffee ground for filter brewing. The shop describes a strong aroma at the first sip.",
            ["500 g", "Ground coffee"],
            None,
        )
    if slug == "espresso-decafeine":
        return (
            "500 g of 100% Arabica espresso with the caffeine removed. The shop says the decaffeination uses a modern process and is meant for people who still want the taste of coffee.",
            ["500 g", "100% Arabica"],
            "Caffeine removed, as stated on the product page.",
        )
    if slug == "espresso-grande":
        return (
            "A 1 kg espresso blend of Arabica and Robusta. No further origin or tasting notes are published.",
            ["1 kg", "Arabica and Robusta"],
            None,
        )
    if slug == "espresso-100-arabica":
        return (
            "A 1 kg espresso of 100% Arabica. The shop calls it a gourmet blend of specialty coffees.",
            ["1 kg", "100% Arabica"],
            None,
        )
    if slug == "greek":
        return (
            "500 g of Greek coffee. The shop credits the cup to bean selection and the roast, and describes a full body and rich flavour.",
            ["500 g", "Greek coffee"],
            None,
        )
    if slug == "soft-ice-cream-1kg":
        return (
            "A 1 kg mix for a soft-serve machine. The title says four flavours; the description names Vanilla, Chocolate, and Strawberry Bueno.",
            ["1 kg", "For a soft-serve machine"],
            None,
        )
    if group == "Aromatic chocolates":
        return (
            f"350 g aromatic chocolate powder. This listing is {name}. The same product text also names a nine-part range: {', '.join(AROMATIC_RANGE)}. Only the separately priced shop records are sold as individual items here.",
            ["350 g"],
            None,
        )
    if slug == "chocolate-powder-la-vittoria-classic":
        return (
            "La Vittoria Classic chocolate powder in a 1 kg pack.",
            ["1 kg", "La Vittoria"],
            None,
        )
    if slug == "chocolate-powder-paolo-chocolate":
        return (
            "Paolo chocolate powder in a 1 kg pack.",
            ["1 kg", "La Vittoria"],
            None,
        )
    if slug == "freddoccino":
        return (
            "A 1 kg chocolate powder for hot or cold drinks. The product text describes a thick classic cocoa profile and also mentions a white chocolate with a soft texture.",
            ["1 kg", "Hot or cold"],
            None,
        )
    if slug == "coffee-syrup-vanillia":
        return (
            "Coffee syrup in an 800 ml bottle. The page says there are seven flavours and names caramel, hazelnut, and vanilla. The other four names are not published.",
            ["800 ml"],
            None,
        )
    if group == "Smoothies":
        flavour = name.replace("Smoothies Syrups ", "")
        return (
            f"{flavour} fruit pulp for blending with ice and water or milk.",
            ["Fruit pulp"],
            None,
        )
    if slug == "milkshake-chocolate":
        return (
            "Chocolate milkshake powder, with 350 g stated on the page. The description says the mix is thick and made with sour cream, pieces of fruit, and powdered yogurt.",
            ["350 g"],
            "Contains sour cream, fruit, and powdered yogurt, as stated. No allergen panel is published.",
        )
    if group == "Milkshakes":
        flavour = name.replace("Milkshake ", "")
        return (
            f"{flavour} milkshake powder. The description says the mix is thick and made with sour cream, pieces of fruit, and powdered yogurt. A pack weight is not stated on this record.",
            [],
            "Contains sour cream, fruit, and powdered yogurt, as stated. No allergen panel is published.",
        )
    if group == "Teas":
        return (
            f"{name} from the Jean Paul Lab tea range. Pack size on these listings is 100 g. The shared shop text names ten teas in the line; this page is only the one in the title.",
            ["100 g"],
            None,
        )
    if slug == "crepe-mix":
        return (
            "A 3 kg crêpe mix. The shop describes it as a balanced batter for sweet or savoury crêpes.",
            ["3 kg"],
            None,
        )
    if slug == "waffle-mix":
        return (
            "A 3 kg waffle mix. The shop describes a fluffy, crisp waffle.",
            ["3 kg"],
            None,
        )
    if slug == "pancake-mix":
        return (
            "A 3 kg pancake mix from the same powder line as the crêpe and waffle mixes.",
            ["3 kg"],
            None,
        )
    if group == "Granitas":
        weight = "500 g is stated on the lemon listing." if slug == "lemon-granita-powder" else "A pack weight is not repeated on the strawberry listing."
        return (
            f"Granita powder for a granita machine, in a strawberry and lemon pair. {weight} The page says the powders use no preservatives and permitted colourings.",
            ["For a granita machine"],
            "No preservatives, as stated. Colourings are described as permitted. No fuller dietary panel is published.",
        )
    return (
        f"{name}. Café serviceware listed in the shop. No description or price is published on the record.",
        [],
        None,
    )


def main():
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    products = []
    for item in raw:
        name = strip(item.get("name"))
        slug = item["slug"]
        categories = [strip(c.get("name", "")) for c in item.get("categories") or []]
        group = group_for(slug, categories)
        summary, facts, dietary = describe(slug, name, group)
        price = money(item)
        products.append(
            {
                "slug": slug,
                "name": name,
                "price": price,
                "price_label": f"€{price} + VAT" if price else "Price not published",
                "group": group,
                "categories": categories,
                "summary": summary,
                "facts": facts,
                "dietary": dietary,
                "image": image_for(group),
                "featured": slug in COFFEE,
            }
        )
    DEST.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(products)} -> {DEST}")


if __name__ == "__main__":
    main()
