import json
import logging
import os
import re
import secrets
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from urllib.parse import quote, urljoin

from flask import Flask, abort, g, redirect, render_template, request, session, url_for
from markupsafe import escape

from content import (
    ANNOUNCEMENT,
    ARTICLES,
    BRAND_FILTERS,
    BRAND_LABELS,
    BRANDS_BY_SLUG,
    BUSINESS,
    FAQ,
    GROUPS,
    HERO,
    MACHINE_PROGRAMMES,
    NAV,
    PRODUCTS,
    PRODUCTS_BY_SLUG,
    CYPRUS_B2B,
    catalog_pack_label,
)
from i18n import CATALOGS, DEFAULT_LANG, LANG_LABELS, LANGS, OG_LOCALES, fold, lang_for_path, localize_pack, translate
from mailing import (
    SITE_URL,
    format_customer_copy,
    format_order_mail,
    mail_transport_status,
    send_customer_copy,
    send_mail,
    viber_order_href,
)
from order_pricing import compute_order_totals, totals_for_session

# INFO so the Render logs show which route delivered each email.
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CUSTOMER_FIELDS = ("name", "business_name", "email", "phone", "town")


def reorder_param(lines):
    """Compact 'slug:qty,slug:qty' list; carries no personal data, so it is safe in a link."""
    return ",".join(f"{line['slug']}:{line['qty']}" for line in lines if line.get("slug"))


def parse_reorder(raw):
    items = {}
    for part in (raw or "").split(","):
        slug, _, qty = part.strip().partition(":")
        if slug not in PRODUCTS_BY_SLUG:
            continue
        try:
            quantity = int(qty)
        except ValueError:
            continue
        if quantity > 0:
            items[slug] = min(quantity, 99)
    return items


def _phone_ok(raw):
    digits = re.sub(r"\D", "", raw or "")
    return len(digits) >= 8


ARTICLES_BY_SLUG = {item["slug"]: item for item in ARTICLES}
HOME_JEAN_PAUL = [
    "smoothies-syrups-mango",
    "milkshake-chocolate",
    "chocolate-with-bueno-biscuit-no-3",
    "strawberry-granita",
    "waffle-mix",
    "english-breakfast-black-tea",
]


def current_lang():
    return getattr(g, "lang", None) or lang_for_path(request.path)


def tr(text, **values):
    return translate(text, current_lang(), **values)


def catalog():
    """Products, brands and hero packs with product copy in the page's language."""
    return CATALOGS[current_lang()]


def _search_text(item):
    brand = BRAND_LABELS.get(item.get("brand"), "")
    parts = (item["name"], item["summary"], item.get("description", ""), brand, tr(brand), tr(item["group"]))
    return fold(" ".join(parts))


def _price(product):
    raw = product.get("price")
    if raw in (None, ""):
        return None
    try:
        amount = Decimal(str(raw))
    except InvalidOperation:
        return None
    if amount <= 0:
        return None
    return amount


def cart_lines():
    raw = session.get("cart") or {}
    lines = []
    priced = Decimal("0")
    missing = False
    for slug, qty in raw.items():
        product = catalog()["by_slug"].get(slug)
        try:
            quantity = int(qty)
        except (TypeError, ValueError):
            continue
        if product is None or quantity < 1:
            continue
        amount = _price(product)
        line_total = amount * quantity if amount is not None else None
        if line_total is None:
            missing = True
        else:
            priced += line_total
        pack = catalog_pack_label(product)
        lines.append(
            {
                "product": product,
                "qty": quantity,
                "pack": pack,
                "line_amount": line_total,
                "line_total": f"€{line_total:.2f}" if line_total is not None else "Price on request",
            }
        )
    return lines, (f"€{priced:.2f}" if lines else None), missing


def order_checkout_context(lines, missing):
    totals = compute_order_totals(lines, missing)
    return {"lines": lines, "subtotal": totals["subtotal"] if totals else None, "missing_price": missing, "totals": totals}


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "vittorio-order-session")
    # Regular cafés reorder weekly; remember their details and last order for a year.
    app.permanent_session_lifetime = timedelta(days=365)
    app.jinja_env.globals["catalog_pack_label"] = lambda item: localize_pack(catalog_pack_label(item), current_lang())
    app.jinja_env.globals["brand_labels"] = BRAND_LABELS
    app.jinja_env.filters["units"] = lambda label: localize_pack(label, current_lang())

    def template_translate(text, **values):
        text = tr(text)
        # Placeholders may carry markup (links, <strong>); plain values are escaped.
        return escape(text).format(**values) if values else text

    app.jinja_env.globals["_"] = template_translate

    localized_endpoints = set()

    def localized(rule, **options):
        """Serve a view at its English path and again under /el/ for the Greek site."""

        def register(view):
            greek_rule = "/el/" if rule == "/" else f"/el{rule}"
            app.add_url_rule(rule, view_func=view, defaults={"lang": "en"}, **options)
            app.add_url_rule(greek_rule, view_func=view, defaults={"lang": "el"}, **options)
            localized_endpoints.add(view.__name__)
            return view

        return register

    @app.url_value_preprocessor
    def pull_language(_endpoint, values):
        if values and "lang" in values:
            g.lang = values.pop("lang")

    @app.url_defaults
    def keep_language(endpoint, values):
        # Links on a Greek page stay on the Greek site unless a language is named.
        if endpoint in localized_endpoints and "lang" not in values and current_lang() != DEFAULT_LANG:
            values["lang"] = current_lang()

    def suppress_mail():
        return bool(app.config.get("TESTING") or app.config.get("MAIL_SUPPRESS_SEND"))

    @app.context_processor
    def inject():
        raw = session.get("cart") or {}
        count = 0
        for qty in raw.values():
            try:
                count += max(int(qty), 0)
            except (TypeError, ValueError):
                continue
        return {
            "business": BUSINESS,
            "nav": NAV,
            "hero": catalog()["hero"],
            "cart_count": count,
            "announcement": ANNOUNCEMENT,
            "brands": catalog()["brands"],
            "brand_labels": BRAND_LABELS,
            "lang": current_lang(),
            "lang_labels": LANG_LABELS,
            "og_locales": OG_LOCALES,
        }

    def language_links(error):
        """Where the EN/ΕΛ switch points, and the hreflang alternates for search engines."""
        if error or request.endpoint not in localized_endpoints:
            return {code: url_for("home", lang=code) for code in LANGS}, None
        args = dict(request.view_args or {})
        switch = {code: url_for(request.endpoint, **{**request.args.to_dict(), **args, "lang": code}) for code in LANGS}
        alternates = {code: url_for(request.endpoint, **{**args, "lang": code}, _external=True) for code in LANGS}
        return switch, alternates

    def page(template, title, description, error=False, **context):
        canonical = urljoin(request.url_root, request.path.lstrip("/"))
        if request.query_string and template == "products.html":
            canonical = url_for("products", _external=True)
        image = url_for("static", filename=f"images/{HERO['file']}", _external=True)
        switch, alternates = language_links(error)
        seo = {
            "title": title,
            "description": description,
            "canonical": canonical,
            "image": image,
            "json_ld": context.pop("json_ld", None),
            "lang_switch": switch,
            "alternates": alternates,
        }
        return render_template(template, seo=seo, **context)

    def store_json():
        payload = {
            "@context": "https://schema.org",
            "@type": "Store",
            "name": BUSINESS["name"],
            "address": {
                "@type": "PostalAddress",
                "addressLocality": BUSINESS["locality"],
                "addressRegion": BUSINESS["region"],
                "addressCountry": "CY",
            },
            "url": urljoin(request.url_root, "visit"),
            "telephone": BUSINESS["phone"],
            "areaServed": {"@type": "Country", "name": "Cyprus"},
            "sameAs": [link["href"] for link in BUSINESS["social"]],
        }
        return json.dumps(payload, ensure_ascii=False)

    @localized("/")
    def home():
        products = catalog()["by_slug"]
        featured = [item for item in catalog()["products"] if item["featured"]]
        jean_paul = [products[slug] for slug in HOME_JEAN_PAUL]
        return page(
            "home.html",
            tr("Vittorio Gourmet Espresso — wholesale & retail coffee in Cyprus"),
            tr("Official Cyprus representative of Vittorio Gourmet Espresso and Jean Paul Lab. Coffee, beverages and café mixes with published trade prices, delivered across Cyprus."),
            featured=featured,
            jean_paul=jean_paul,
            articles=ARTICLES,
            json_ld=store_json(),
        )

    @localized("/products")
    def products():
        group = request.args.get("category", "").strip()
        brand = request.args.get("brand", "").strip()
        query = request.args.get("q", "").strip()
        items = catalog()["products"]
        if brand:
            if brand not in BRAND_LABELS:
                abort(404)
            items = [item for item in items if item.get("brand") == brand]
        groups = [name for name in GROUPS if any(item["group"] == name for item in items)]
        if group:
            if group not in GROUPS:
                abort(404)
            items = [item for item in items if item["group"] == group]
        if query:
            needle = fold(query)
            items = [
                item
                for item in items
                if needle in _search_text(item)
            ]
        title = tr("Catalogue — Vittorio Gourmet Espresso")
        if group:
            title = f"{tr(group)} — Vittorio Gourmet Espresso"
        elif brand:
            title = f"{tr(BRAND_LABELS[brand])} — Vittorio Gourmet Espresso"
        return page(
            "products.html",
            title,
            tr("Vittorio coffee and Jean Paul Lab beverages, teas, mixes and café supplies, with published trade prices plus VAT and delivery across Cyprus."),
            items=items,
            groups=groups,
            active_group=group,
            active_brand=brand,
            brand_filters=BRAND_FILTERS,
            query=query,
        )

    @localized("/products/<slug>")
    def product(slug):
        item = catalog()["by_slug"].get(slug)
        if item is None:
            abort(404)
        return page(
            "product.html",
            f"{item['name']} — Vittorio Gourmet Espresso",
            f"{item['name']}. {item.get('description') or item['price_label']}",
            item=item,
            brand=BRANDS_BY_SLUG.get(item.get("brand")),
        )

    @localized("/philosophy")
    def philosophy():
        return page(
            "philosophy.html",
            tr("Coffee philosophy — Vittorio Gourmet Espresso"),
            tr("How Vittorio thinks about coffee for the bar, and the coffees in the Cyprus catalogue."),
            coffees=[item for item in catalog()["products"] if item["group"] == "Coffee"],
        )

    @localized("/story")
    def story():
        return page(
            "story.html",
            tr("Our story — Vittorio Gourmet Espresso"),
            tr("Vittorio supplies the Cypriot bar from a depot in Kalo Xorio, and met the trade at HO.RE.CA. 2019."),
        )

    @localized("/supply")
    def supply():
        return page(
            "supply.html",
            tr("Coffee supply — Vittorio Gourmet Espresso"),
            tr("Coffee and café supplies delivered to cafés and bars across Cyprus."),
        )

    @localized("/cyprus")
    def cyprus():
        return page(
            "cyprus.html",
            tr("B2B Services — Vittorio Gourmet Espresso Cyprus"),
            tr("Wholesale coffee, machines, training, and partner supply for cafés and bars across Cyprus."),
            b2b=CYPRUS_B2B,
        )

    @localized("/machines")
    def machines():
        return page(
            "machines.html",
            tr("Coffee machines — Vittorio Gourmet Espresso"),
            tr("Appia Life, Sanremo, and Expobar machines are offered with no charge during a partnership. Setup guidance is free once cooperation starts."),
            machine_programmes=MACHINE_PROGRAMMES,
        )

    @localized("/cart/add", methods=["POST"])
    def cart_add():
        slug = request.form.get("slug", "").strip()
        if slug not in PRODUCTS_BY_SLUG:
            abort(404)
        try:
            qty = int(request.form.get("qty", "1"))
        except ValueError:
            qty = 1
        qty = min(max(qty, 1), 99)
        cart = dict(session.get("cart") or {})
        cart[slug] = min(int(cart.get(slug, 0)) + qty, 99)
        session["cart"] = cart
        return redirect(request.form.get("next") or url_for("order"))

    @localized("/cart/update", methods=["POST"])
    def cart_update():
        cart = {}
        for slug in PRODUCTS_BY_SLUG:
            raw = request.form.get(f"qty-{slug}")
            if raw is None:
                continue
            try:
                qty = int(raw)
            except ValueError:
                continue
            if qty > 0:
                cart[slug] = min(qty, 99)
        session["cart"] = cart
        return redirect(url_for("order"))

    @localized("/order", methods=["GET", "POST"])
    def order():
        lines, _subtotal, missing = cart_lines()
        checkout = order_checkout_context(lines, missing)
        errors = {}
        values = {"name": "", "business_name": "", "email": "", "phone": "", "town": "", "notes": ""}
        saved = session.get("customer") or {}
        values.update({key: saved.get(key, "") for key in CUSTOMER_FIELDS})
        if request.method == "POST":
            values = {key: request.form.get(key, "").strip() for key in values}
            if request.form.get("company_website", "").strip():
                return redirect(url_for("order_done"))
            if not lines:
                errors["cart"] = tr("Add at least one product before placing the order.")
            if len(values["name"]) < 2:
                errors["name"] = tr("Enter your name.")
            if not EMAIL_RE.match(values["email"]):
                errors["email"] = tr("Enter a valid email address.")
            if not _phone_ok(values["phone"]):
                errors["phone"] = tr("Enter a phone number we can reach you on.")
            if len(values["town"]) < 2:
                errors["town"] = tr("Enter the town in Cyprus for delivery.")
            if errors:
                body = page(
                    "order.html",
                    tr("Your order — Vittorio Gourmet Espresso"),
                    tr("Place a coffee and café-supply order for delivery in Cyprus."),
                    errors=errors,
                    values=values,
                    **checkout,
                )
                return body, 400
            placed = {
                "ref": secrets.token_hex(3).upper(),
                "lines": [
                    {
                        "slug": line["product"]["slug"],
                        "name": line["product"]["name"],
                        "qty": line["qty"],
                        "pack": line.get("pack") or catalog_pack_label(line["product"]),
                        "line_total": line["line_total"],
                    }
                    for line in lines
                ],
                "missing_price": missing,
                "totals": totals_for_session(checkout["totals"]),
                "lang": current_lang(),
                **values,
            }
            if checkout["totals"]:
                placed["subtotal"] = checkout["totals"]["subtotal"]
            placed["email_sent"] = deliver_order_to_depot(placed)
            placed["customer_copy_sent"] = email_customer_copy(placed)
            session.permanent = True
            session["customer"] = {key: values[key] for key in CUSTOMER_FIELDS}
            session["reorder"] = reorder_param(placed["lines"])
            session["cart"] = {}
            session["last_order"] = placed
            return redirect(url_for("order_done"))
        reorder_items = []
        if not lines:
            reorder_items = [
                {"product": catalog()["by_slug"][slug], "qty": qty}
                for slug, qty in parse_reorder(session.get("reorder")).items()
            ]
        return page(
            "order.html",
            tr("Your order — Vittorio Gourmet Espresso"),
            tr("Place a coffee and café-supply order for delivery in Cyprus."),
            errors=errors,
            values=values,
            reorder_items=reorder_items,
            **checkout,
        )

    @localized("/order/again")
    def order_again():
        """Refill the order list from an emailed link, or from this browser's last order."""
        items = parse_reorder(request.args.get("items") or session.get("reorder"))
        if not items:
            return redirect(url_for("products"))
        session["cart"] = items
        return redirect(url_for("order"))

    def email_customer_copy(placed):
        reorder_url = SITE_URL + url_for("order_again", items=reorder_param(placed["lines"]))
        refer_url = SITE_URL + url_for("refer")
        subject, body = format_customer_copy(placed, reorder_url, lang=placed.get("lang", DEFAULT_LANG), refer_url=refer_url)
        return send_customer_copy(subject, body, placed["email"], suppress=suppress_mail())

    def deliver_order_to_depot(placed):
        subject, order_body = format_order_mail(placed)
        sent = send_mail(
            subject,
            order_body,
            reply_to=placed.get("email"),
            suppress=suppress_mail(),
        )
        if not sent:
            # Keep the order recoverable from the Render logs when every mail route fails.
            app.logger.error("Order %s was not emailed to the depot:\n%s", placed["ref"], order_body)
        return sent

    def _order_done_context(placed):
        _, order_body = format_order_mail(placed)
        return {
            "placed": placed,
            "viber_href": viber_order_href(order_body),
        }

    @localized("/order/received")
    def order_done():
        placed = session.get("last_order")
        if not placed:
            return redirect(url_for("order"))
        if not placed.get("email_sent"):
            placed["email_sent"] = deliver_order_to_depot(placed)
            session["last_order"] = placed
        return page(
            "order_done.html",
            tr("Order received — Vittorio Gourmet Espresso"),
            tr("Your Cyprus delivery order is emailed to the depot. Payment is cash on delivery only."),
            **_order_done_context(placed),
        )

    @localized("/order/email-depot", methods=["POST"])
    def order_email_depot():
        placed = session.get("last_order")
        if not placed:
            return redirect(url_for("order"))
        placed["email_sent"] = deliver_order_to_depot(placed)
        session["last_order"] = placed
        return redirect(url_for("order_done"))

    @localized("/visit")
    def visit():
        return page(
            "visit.html",
            tr("Visit us — Vittorio Gourmet Espresso, Kalo Xorio"),
            tr("The Vittorio depot in Kalo Xorio, Larnaca, Cyprus."),
            json_ld=store_json(),
        )

    @localized("/journal")
    def journal():
        return page(
            "journal.html",
            tr("Journal — Vittorio Gourmet Espresso"),
            tr("Notes from Vittorio at HO.RE.CA. 2019 in Athens."),
            articles=ARTICLES,
        )

    @localized("/journal/<slug>")
    def article(slug):
        item = ARTICLES_BY_SLUG.get(slug)
        if item is None:
            abort(404)
        return page(
            "article.html",
            f"{tr(item['title'])} — Vittorio Gourmet Espresso",
            tr(item["summary"]),
            article=item,
        )

    @localized("/contact", methods=["GET", "POST"])
    def contact():
        errors = {}
        values = {"name": "", "email": "", "message": ""}
        sent = False
        status = 200
        if request.method == "POST":
            values = {
                "name": request.form.get("name", "").strip(),
                "email": request.form.get("email", "").strip(),
                "message": request.form.get("message", "").strip(),
            }
            honeypot = request.form.get("company_website", "").strip()
            if honeypot:
                sent = True
            else:
                if len(values["name"]) < 2:
                    errors["name"] = tr("Enter your name.")
                if not EMAIL_RE.match(values["email"]):
                    errors["email"] = tr("Enter a valid email address.")
                if len(values["message"]) < 10:
                    errors["message"] = tr("Write a message of at least 10 characters.")
                if errors:
                    status = 400
                else:
                    mail_body = (
                        f"Name: {values['name']}\n"
                        f"Email: {values['email']}\n\n"
                        f"{values['message']}"
                    )
                    if send_mail(
                        f"Vittorio contact — {values['name']}",
                        mail_body,
                        reply_to=values["email"],
                        suppress=suppress_mail(),
                    ):
                        sent = True
                    else:
                        errors["send"] = tr(
                            "We could not send your message right now. Use Contact on Viber, or try again later."
                        )
                        status = 503
        body = page(
            "contact.html",
            tr("Contact — Vittorio Gourmet Espresso"),
            tr("Reach the Vittorio depot in Kalo Xorio on Viber."),
            errors=errors,
            values=values,
            sent=sent,
        )
        return body, status

    @localized("/refer", methods=["GET", "POST"])
    def refer():
        """Partners recommend a venue; the depot follows up and rewards the partner on its first order."""
        fields = ("name", "business", "email", "venue", "venue_town", "venue_contact")
        values = {field: "" for field in fields}
        errors = {}
        sent = False
        status = 200
        if request.method == "POST":
            values = {field: request.form.get(field, "").strip() for field in fields}
            if request.form.get("company_website", "").strip():
                sent = True
            else:
                if len(values["name"]) < 2:
                    errors["name"] = tr("Enter your name.")
                if not EMAIL_RE.match(values["email"]):
                    errors["email"] = tr("Enter a valid email address.")
                if len(values["venue"]) < 2:
                    errors["venue"] = tr("Enter the venue you recommend.")
                if len(values["venue_town"]) < 2:
                    errors["venue_town"] = tr("Enter the venue's town.")
                if errors:
                    status = 400
                else:
                    mail_body = (
                        f"Recommended venue: {values['venue']}\n"
                        f"Town: {values['venue_town']}\n"
                        f"Venue contact: {values['venue_contact'] or '-'}\n\n"
                        f"Recommended by: {values['name']}\n"
                        f"Their business: {values['business'] or '-'}\n"
                        f"Email: {values['email']}\n"
                        f"Language: {'Greek' if current_lang() == 'el' else 'English'}\n\n"
                        "Reward on the venue's first order: 1 kg of Vittorio espresso with the partner's next order."
                    )
                    if send_mail(
                        f"Vittorio referral — {values['venue']} ({values['venue_town']})",
                        mail_body,
                        reply_to=values["email"],
                        suppress=suppress_mail(),
                    ):
                        sent = True
                    else:
                        errors["send"] = tr(
                            "We could not send your message right now. Use Contact on Viber, or try again later."
                        )
                        status = 503
        body = page(
            "refer.html",
            tr("Recommend a café — Vittorio Gourmet Espresso"),
            tr("Recommend a café, bar or hotel to Vittorio and receive 1 kg of espresso on their first order."),
            errors=errors,
            values=values,
            sent=sent,
        )
        return body, status

    @localized("/faq")
    def faq():
        return page(
            "faq.html",
            tr("Questions — Vittorio Gourmet Espresso"),
            tr("Delivery, machines, returns, and how an order is confirmed."),
            faq=FAQ,
        )

    @localized("/privacy")
    def privacy():
        return page(
            "privacy.html",
            tr("Privacy — Vittorio Gourmet Espresso"),
            tr("What Vittorio keeps from an order or a message on this site."),
        )

    @localized("/returns")
    def returns():
        return page(
            "returns.html",
            tr("Returns — Vittorio Gourmet Espresso"),
            tr("Unopened goods can be returned within 30 days. Orders are cash on delivery."),
        )

    @app.get("/sitemap.xml")
    def sitemap():
        paths = [
            "/",
            "/products",
            "/supply",
            "/cyprus",
            "/machines",
            "/order",
            "/philosophy",
            "/story",
            "/visit",
            "/journal",
            "/contact",
            "/refer",
            "/faq",
            "/privacy",
            "/returns",
        ]
        paths += [f"/products/{item['slug']}" for item in PRODUCTS]
        paths += [f"/journal/{item['slug']}" for item in ARTICLES]
        paths += ["/el/" if path == "/" else f"/el{path}" for path in paths]
        urls = [urljoin(request.url_root, path.lstrip("/")) for path in paths]
        xml = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        xml += [f"<url><loc>{loc}</loc></url>" for loc in urls]
        xml.append("</urlset>")
        return "\n".join(xml), 200, {"Content-Type": "application/xml; charset=utf-8"}

    @app.get("/health/mail")
    def health_mail():
        return mail_transport_status(), 200, {"Content-Type": "application/json"}

    @app.get("/robots.txt")
    def robots():
        lines = [
            "User-agent: *",
            "Allow: /",
            f"Sitemap: {urljoin(request.url_root, 'sitemap.xml')}",
        ]
        return "\n".join(lines) + "\n", 200, {"Content-Type": "text/plain; charset=utf-8"}

    @app.get("/menu")
    def menu_redirect():
        return redirect(url_for("products"), code=302)

    @app.errorhandler(404)
    def not_found(_error):
        return (
            page(
                "404.html",
                tr("Page not found — Vittorio Gourmet Espresso"),
                tr("That page is not part of Vittorio Gourmet Espresso."),
                error=True,
            ),
            404,
        )

    return app


app = create_app()
