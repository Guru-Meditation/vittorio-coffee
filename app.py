import json
import re
from urllib.parse import urljoin

from flask import Flask, abort, redirect, render_template, request, url_for

from content import ARTICLES, BUSINESS, FAQ, GROUPS, HERO, NAV, PRODUCTS, PRODUCTS_BY_SLUG

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ARTICLES_BY_SLUG = {item["slug"]: item for item in ARTICLES}


def create_app():
    app = Flask(__name__)

    @app.context_processor
    def inject():
        return {"business": BUSINESS, "nav": NAV, "hero": HERO}

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
            "telephone": BUSINESS["phone_tel"],
            "email": BUSINESS["email_public"],
            "address": {
                "@type": "PostalAddress",
                "streetAddress": BUSINESS["street"],
                "addressLocality": BUSINESS["locality"],
                "postalCode": BUSINESS["postal_code"],
                "addressRegion": BUSINESS["region"],
                "addressCountry": "CY",
            },
            "openingHoursSpecification": {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ],
                "opens": "08:00",
                "closes": "20:00",
            },
            "url": urljoin(request.url_root, "visit"),
        }
        return json.dumps(payload, ensure_ascii=False)

    @app.get("/")
    def home():
        featured = [item for item in PRODUCTS if item["featured"]]
        return page(
            "home.html",
            "Vittorio Gourmet Espresso — coffee supplies in Larnaca",
            "Gourmet espresso, chocolate, teas, and café mixes from Synergasias 17, Kiti. Prices and hours as published by Vittorio Gourmet Espresso.",
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
            item["summary"][:155],
            item=item,
        )

    @app.get("/philosophy")
    def philosophy():
        return page(
            "philosophy.html",
            "Coffee philosophy — Vittorio Gourmet Espresso",
            "How Vittorio Gourmet Espresso describes specialty coffee, and the coffees actually listed in the Cyprus shop.",
            coffees=[item for item in PRODUCTS if item["group"] == "Coffee"],
        )

    @app.get("/story")
    def story():
        return page(
            "story.html",
            "Our story — Vittorio Gourmet Espresso",
            "The service mission published by Vittorio Gourmet Espresso, and its 2019 appearance at HO.RE.CA.",
        )

    @app.get("/visit")
    def visit():
        return page(
            "visit.html",
            "Visit us — Vittorio Gourmet Espresso, Kiti",
            "Synergasias 17, Kiti 7550, Larnaca. Open Monday to Sunday, 08:00–20:00. Call +357 99 766 848.",
            json_ld=store_json(),
        )

    @app.get("/journal")
    def journal():
        return page(
            "journal.html",
            "Journal — Vittorio Gourmet Espresso",
            "Two notes from 2019 about Vittorio Gourmet Espresso at HO.RE.CA. No newer articles are published.",
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
                    sent = True
        body = page(
            "contact.html",
            "Contact — Vittorio Gourmet Espresso",
            "Write to Vittorio Gourmet Espresso in Kiti, or call +357 99 766 848. Monday to Sunday, 08:00–20:00.",
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
            "Hours, the Kiti address, returns, VAT, and what this catalogue does not invent.",
            faq=FAQ,
        )

    @app.get("/privacy")
    def privacy():
        return page(
            "privacy.html",
            "Privacy — Vittorio Gourmet Espresso",
            "How this preview handles the contact form, and what the live shop’s privacy page currently contains.",
        )

    @app.get("/returns")
    def returns():
        return page(
            "returns.html",
            "Returns — Vittorio Gourmet Espresso",
            "Unopened goods can be returned within 30 days. The live site says it does not yet take payment online.",
        )

    @app.get("/sitemap.xml")
    def sitemap():
        paths = [
            "/",
            "/products",
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
                "That page is not on this Vittorio Gourmet Espresso preview.",
            ),
            404,
        )

    return app


app = create_app()
