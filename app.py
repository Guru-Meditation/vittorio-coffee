import json
import os
import re
import secrets
from decimal import Decimal, InvalidOperation
from urllib.parse import quote, urljoin

from flask import Flask, abort, redirect, render_template, request, session, url_for

from content import (
    ARTICLES,
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
from mailing import format_order_mail, send_mail, viber_order_href

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _phone_ok(raw):
    digits = re.sub(r"\D", "", raw or "")
    return len(digits) >= 8
ARTICLES_BY_SLUG = {item["slug"]: item for item in ARTICLES}


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
        product = PRODUCTS_BY_SLUG.get(slug)
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
        lines.append(
            {
                "product": product,
                "qty": quantity,
                "line_total": f"€{line_total:.2f}" if line_total is not None else "Price on request",
            }
        )
    return lines, (f"€{priced:.2f}" if lines else None), missing


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "vittorio-order-session")
    app.jinja_env.globals["catalog_pack_label"] = catalog_pack_label

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
        return {"business": BUSINESS, "nav": NAV, "hero": HERO, "cart_count": count}

    def page(template, title, description, **context):
        canonical = urljoin(request.url_root, request.path.lstrip("/"))
        if request.query_string and template == "products.html":
            canonical = urljoin(request.url_root, "products")
        image = url_for("static", filename=f"images/{HERO['file']}", _external=True)
        seo = {
            "title": title,
            "description": description,
            "canonical": canonical,
            "image": image,
            "json_ld": context.pop("json_ld", None),
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
            "areaServed": {"@type": "Country", "name": "Cyprus"},
        }
        return json.dumps(payload, ensure_ascii=False)

    @app.get("/")
    def home():
        featured = [item for item in PRODUCTS if item["featured"]]
        return page(
            "home.html",
            "Vittorio Gourmet Espresso — wholesale & retail coffee in Cyprus",
            "Wholesale and retail coffee, ingredients, and espresso equipment for Cyprus. Apia Life, Sanremo, and Expobar partnerships.",
            featured=featured,
            articles=ARTICLES,
            json_ld=store_json(),
        )

    @app.get("/products")
    def products():
        group = request.args.get("category", "").strip()
        query = request.args.get("q", "").strip()
        items = PRODUCTS
        if group:
            if group not in GROUPS:
                abort(404)
            items = [item for item in items if item["group"] == group]
        if query:
            needle = query.casefold()
            items = [
                item
                for item in items
                if needle in item["name"].casefold() or needle in item["summary"].casefold()
            ]
        title = "Catalogue — Vittorio Gourmet Espresso"
        if group:
            title = f"{group} — Vittorio Gourmet Espresso"
        return page(
            "products.html",
            title,
            "Coffee, chocolate, teas, syrups, mixes, and serviceware from the Vittorio Gourmet Espresso shop, with published prices plus VAT.",
            items=items,
            groups=GROUPS,
            active_group=group,
            query=query,
        )

    @app.get("/products/<slug>")
    def product(slug):
        item = PRODUCTS_BY_SLUG.get(slug)
        if item is None:
            abort(404)
        return page(
            "product.html",
            f"{item['name']} — Vittorio Gourmet Espresso",
            f"{item['name']}. {item['price_label']}.",
            item=item,
        )

    @app.get("/philosophy")
    def philosophy():
        return page(
            "philosophy.html",
            "Coffee philosophy — Vittorio Gourmet Espresso",
            "How Vittorio thinks about coffee for the bar, and the coffees in the Cyprus catalogue.",
            coffees=[item for item in PRODUCTS if item["group"] == "Coffee"],
        )

    @app.get("/story")
    def story():
        return page(
            "story.html",
            "Our story — Vittorio Gourmet Espresso",
            "Vittorio supplies the Cypriot bar from a depot in Kalo Xorio, and met the trade at HO.RE.CA. 2019.",
        )

    @app.get("/supply")
    def supply():
        return page(
            "supply.html",
            "Coffee supply — Vittorio Gourmet Espresso",
            "Depot in Kalo Xorio. Car delivery of coffee and café supplies to cafés and bars across Cyprus.",
        )

    @app.get("/cyprus")
    def cyprus():
        return page(
            "cyprus.html",
            "B2B Services — Vittorio Gourmet Espresso Cyprus",
            "Wholesale coffee, machines, training, and partner supply for cafés and bars across Cyprus.",
            b2b=CYPRUS_B2B,
        )

    @app.get("/machines")
    def machines():
        return page(
            "machines.html",
            "Coffee machines — Vittorio Gourmet Espresso",
            "Apia Life, Sanremo, and Expobar machines are offered with no charge during a partnership. Setup guidance is free once cooperation starts.",
            machine_programmes=MACHINE_PROGRAMMES,
        )

    @app.post("/cart/add")
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

    @app.post("/cart/update")
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

    @app.route("/order", methods=["GET", "POST"])
    def order():
        lines, subtotal, missing = cart_lines()
        errors = {}
        values = {"name": "", "business_name": "", "email": "", "phone": "", "town": "", "notes": ""}
        if request.method == "POST":
            values = {key: request.form.get(key, "").strip() for key in values}
            if request.form.get("company_website", "").strip():
                return redirect(url_for("order_done"))
            if not lines:
                errors["cart"] = "Add at least one product before placing the order."
            if len(values["name"]) < 2:
                errors["name"] = "Enter your name."
            if not EMAIL_RE.match(values["email"]):
                errors["email"] = "Enter a valid email address."
            if not _phone_ok(values["phone"]):
                errors["phone"] = "Enter a phone number we can reach you on."
            if len(values["town"]) < 2:
                errors["town"] = "Enter the town in Cyprus for delivery."
            if errors:
                body = page(
                    "order.html",
                    "Your order — Vittorio Gourmet Espresso",
                    "Place a coffee and café-supply order for delivery by car in Cyprus.",
                    lines=lines,
                    subtotal=subtotal,
                    missing_price=missing,
                    errors=errors,
                    values=values,
                )
                return body, 400
            placed = {
                "ref": secrets.token_hex(3).upper(),
                "lines": [
                    {"name": line["product"]["name"], "qty": line["qty"], "line_total": line["line_total"]}
                    for line in lines
                ],
                "subtotal": subtotal,
                "missing_price": missing,
                **values,
            }
            subject, order_body = format_order_mail(placed)
            placed["email_sent"] = send_mail(
                subject,
                order_body,
                reply_to=placed["email"],
                suppress=suppress_mail(),
            )
            session["cart"] = {}
            session["last_order"] = placed
            return redirect(url_for("order_done"))
        return page(
            "order.html",
            "Your order — Vittorio Gourmet Espresso",
            "Place a coffee and café-supply order for delivery by car in Cyprus.",
            lines=lines,
            subtotal=subtotal,
            missing_price=missing,
            errors=errors,
            values=values,
        )

    def _order_done_context(placed):
        _, order_body = format_order_mail(placed)
        return {
            "placed": placed,
            "viber_href": viber_order_href(order_body),
        }

    @app.get("/order/received")
    def order_done():
        placed = session.get("last_order")
        if not placed:
            return redirect(url_for("order"))
        return page(
            "order_done.html",
            "Order received — Vittorio Gourmet Espresso",
            "Your Cyprus delivery order is emailed to the depot. Payment is cash on delivery only.",
            **_order_done_context(placed),
        )

    @app.get("/visit")
    def visit():
        return page(
            "visit.html",
            "Visit us — Vittorio Gourmet Espresso, Kalo Xorio",
            "The Vittorio depot in Kalo Xorio, Larnaca, Cyprus.",
            json_ld=store_json(),
        )

    @app.get("/journal")
    def journal():
        return page(
            "journal.html",
            "Journal — Vittorio Gourmet Espresso",
            "Notes from Vittorio at HO.RE.CA. 2019 in Athens.",
            articles=ARTICLES,
        )

    @app.get("/journal/<slug>")
    def article(slug):
        item = ARTICLES_BY_SLUG.get(slug)
        if item is None:
            abort(404)
        return page(
            "article.html",
            f"{item['title']} — Vittorio Gourmet Espresso",
            item["summary"],
            article=item,
        )

    @app.route("/contact", methods=["GET", "POST"])
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
                    errors["name"] = "Enter your name."
                if not EMAIL_RE.match(values["email"]):
                    errors["email"] = "Enter a valid email address."
                if len(values["message"]) < 10:
                    errors["message"] = "Write a message of at least 10 characters."
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
                        errors["send"] = (
                            "We could not send your message right now. Use Contact on Viber, or try again later."
                        )
                        status = 503
        body = page(
            "contact.html",
            "Contact — Vittorio Gourmet Espresso",
            "Reach the Vittorio depot in Kalo Xorio on Viber.",
            errors=errors,
            values=values,
            sent=sent,
        )
        return body, status

    @app.get("/faq")
    def faq():
        return page(
            "faq.html",
            "Questions — Vittorio Gourmet Espresso",
            "Delivery, machines, returns, and how an order is confirmed.",
            faq=FAQ,
        )

    @app.get("/privacy")
    def privacy():
        return page(
            "privacy.html",
            "Privacy — Vittorio Gourmet Espresso",
            "What Vittorio keeps from an order or a message on this site.",
        )

    @app.get("/returns")
    def returns():
        return page(
            "returns.html",
            "Returns — Vittorio Gourmet Espresso",
            "Unopened goods can be returned within 30 days. Orders are cash on delivery.",
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
            "/faq",
            "/privacy",
            "/returns",
        ]
        paths += [f"/products/{item['slug']}" for item in PRODUCTS]
        paths += [f"/journal/{item['slug']}" for item in ARTICLES]
        urls = [urljoin(request.url_root, path.lstrip("/")) for path in paths]
        xml = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        xml += [f"<url><loc>{loc}</loc></url>" for loc in urls]
        xml.append("</urlset>")
        return "\n".join(xml), 200, {"Content-Type": "application/xml; charset=utf-8"}

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
                "Page not found — Vittorio Gourmet Espresso",
                "That page is not part of Vittorio Gourmet Espresso.",
            ),
            404,
        )

    return app


app = create_app()
