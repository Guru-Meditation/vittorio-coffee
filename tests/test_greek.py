import re
from pathlib import Path

import pytest

import app as app_module
from app import create_app
from content import (
    ANNOUNCEMENT,
    ARTICLES,
    BRAND_FILTERS,
    BRANDS,
    BUSINESS,
    CYPRUS_B2B,
    FAQ,
    GROUPS,
    HERO,
    MACHINE_PROGRAMMES,
    NAV,
    PRODUCTS,
)
from i18n import EL, PRODUCTS_EL

ROOT = Path(__file__).resolve().parents[1]

GREEK_PAGES = [
    "/el/",
    "/el/products",
    "/el/products/costa-rica",
    "/el/philosophy",
    "/el/story",
    "/el/visit",
    "/el/journal",
    "/el/journal/horeca-2019",
    "/el/supply",
    "/el/cyprus",
    "/el/machines",
    "/el/order",
    "/el/contact",
    "/el/refer",
    "/el/faq",
    "/el/privacy",
    "/el/returns",
]


@pytest.fixture
def client():
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


@pytest.mark.parametrize("path", GREEK_PAGES)
def test_greek_pages_render_in_greek(client, path):
    response = client.get(path)
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert '<html lang="el">' in page
    assert '<meta property="og:locale" content="el_GR">' in page
    assert "Κατάλογος" in page  # nav
    assert "Οι τιμές δεν περιλαμβάνουν ΦΠΑ." in page  # footer


def test_bare_el_redirects_to_greek_home(client):
    response = client.get("/el")
    assert response.status_code == 308
    assert response.headers["Location"].endswith("/el/")


def test_english_stays_english(client):
    home = client.get("/").get_data(as_text=True)
    assert '<html lang="en">' in home
    assert "Official Cyprus representative" in home
    assert "Κατάλογος" not in home
    assert 'hreflang="el" href="http://localhost/el/"' in home


def test_hreflang_and_language_switch(client):
    page = client.get("/el/products?brand=vittorio&category=Coffee").get_data(as_text=True)
    assert '<link rel="canonical" href="http://localhost/el/products">' in page
    assert '<link rel="alternate" hreflang="en" href="http://localhost/products">' in page
    assert '<link rel="alternate" hreflang="el" href="http://localhost/el/products">' in page
    assert '<link rel="alternate" hreflang="x-default" href="http://localhost/products">' in page
    # The switch keeps the filters, so a buyer lands on the same shelf in the other language.
    assert 'href="/products?brand=vittorio&amp;category=Coffee" hreflang="en"' in page
    assert 'href="/el/products?brand=vittorio&amp;category=Coffee" hreflang="el" lang="el" aria-current="true"' in page
    english = client.get("/products/costa-rica").get_data(as_text=True)
    assert 'href="/el/products/costa-rica" hreflang="el"' in english


def test_links_on_greek_pages_stay_greek(client):
    home = client.get("/el/").get_data(as_text=True)
    main = home.split('<main id="content">', 1)[1].split("</main>", 1)[0]
    links = re.findall(r'href="(/[^"]*)"', main)
    assert links
    assert all(link.startswith("/el/") for link in links), [link for link in links if not link.startswith("/el/")]
    assert 'action="/el/cart/add"' in home


def test_greek_home_copy(client):
    home = client.get("/el/").get_data(as_text=True)
    assert "Vittorio Gourmet Espresso με παράδοση σε όλη την Κύπρο" in home
    assert "Επίσημος αντιπρόσωπος στην Κύπρο της <strong>Vittorio Gourmet Espresso</strong>" in home
    assert "Τσάι Jean Paul Lab: φρουτοτσάι Blue Night." in home
    assert "Προϊόντα Jean Paul Lab" in home
    assert "€14.60 + ΦΠΑ" in home
    assert "Αντικαταβολή" in home


def test_greek_catalogue_and_search(client):
    page = client.get("/el/products?brand=jean-paul-lab").get_data(as_text=True)
    assert "31 προϊόντα" in page
    assert ">Τσάγια<" in page
    straws = client.get("/el/products/granite-straws-x-1000-pcs").get_data(as_text=True)
    assert "1000 τεμ." in straws
    assert "Τιμή κατόπιν ζήτησης" in straws
    # Accent- and case-insensitive, so a typed "σοκολατα" finds "σοκολάτα".
    found = client.get("/el/products?q=ΣΟΚΟΛΑΤΑ").get_data(as_text=True)
    assert "Aromatic Chocolate No.3" in found
    assert "Κανένα προϊόν" in client.get("/el/products?q=zzzz").get_data(as_text=True)
    assert "Επιστροφές προϊόντων." in client.get("/el/returns").get_data(as_text=True)


def test_greek_404(client):
    response = client.get("/el/no-such-page")
    assert response.status_code == 404
    page = response.get_data(as_text=True)
    assert '<html lang="el">' in page
    assert "Η σελίδα δεν βρέθηκε." in page


def test_greek_order_flow_and_customer_copy(monkeypatch):
    sent = []
    monkeypatch.setattr(
        app_module, "send_customer_copy", lambda subject, body, to, suppress=False: sent.append((subject, body)) or True
    )
    flask_app = app_module.create_app()
    flask_app.config["TESTING"] = True
    client = flask_app.test_client()

    empty = client.post("/el/order", data={"name": "", "email": "x", "phone": "1", "town": ""})
    assert empty.status_code == 400
    assert "Προσθέστε τουλάχιστον ένα προϊόν" in empty.get_data(as_text=True)

    added = client.post("/el/cart/add", data={"slug": "costa-rica", "qty": "2", "next": "/el/order"})
    assert added.headers["Location"].endswith("/el/order")
    page = client.get("/el/order").get_data(as_text=True)
    assert "Αποστολή παραγγελίας" in page
    assert "ΦΠΑ (5%)" in page

    invalid = client.post("/el/order", data={"name": "Κ", "email": "no", "phone": "1", "town": ""})
    assert invalid.status_code == 400
    errors = invalid.get_data(as_text=True)
    assert "Συμπληρώστε το όνομά σας." in errors
    assert "Συμπληρώστε την πόλη παράδοσης στην Κύπρο." in errors

    placed = client.post(
        "/el/order",
        data={"name": "Κώστας", "email": "k@example.com", "phone": "99123456", "address": "Μακαρίου 12", "town": "Λάρνακα"},
    )
    assert placed.headers["Location"].endswith("/el/order/received")
    done = client.get("/el/order/received").get_data(as_text=True)
    assert "Ευχαριστούμε, Κώστας" in done
    assert "Λάρνακα, Κύπρος" in done
    assert "Σύνολο πληρωτέο κατά την παράδοση" in done

    subject, body = sent[0]
    assert subject.startswith("Η παραγγελία σας Vittorio")
    assert "Γεια σας Κώστας," in body
    assert "/el/order/again?items=costa-rica:2" in body
    # The depot copy stays in English but says the customer ordered in Greek.
    _subject, depot = app_module.format_order_mail({"ref": "X", "lang": "el", "lines": []})
    assert "Language: Greek" in depot


def test_greek_contact_errors(client):
    response = client.post("/el/contact", data={"name": "", "email": "no", "message": "hi"})
    assert response.status_code == 400
    page = response.get_data(as_text=True)
    assert "Γράψτε μήνυμα τουλάχιστον 10 χαρακτήρων." in page


def test_sitemap_lists_greek_pages(client):
    sitemap = client.get("/sitemap.xml").get_data(as_text=True)
    assert "http://localhost/el/</loc>" in sitemap
    assert "/el/products/costa-rica" in sitemap
    assert "/el/cyprus" in sitemap


def test_every_product_has_greek_copy():
    assert set(PRODUCTS_EL) == {item["slug"] for item in PRODUCTS}
    for item in PRODUCTS:
        greek = PRODUCTS_EL[item["slug"]]
        assert greek["description"], item["slug"]
        for field in ("profile", "dietary"):
            if item.get(field):
                assert greek.get(field), (item["slug"], field)


def _template_strings():
    found = set()
    for path in (ROOT / "templates").glob("*.html"):
        text = path.read_text(encoding="utf-8")
        found.update(re.findall(r'\b_\(\s*"([^"]+)"', text))
        found.update(re.findall(r"\b_\(\s*'([^']+)'", text))
    for name, pattern in (("app.py", r'\btr\(\s*"([^"]+)"'), ("mailing.py", r'\bt\(\s*["\']([^"\']+)["\']')):
        found.update(re.findall(pattern, (ROOT / name).read_text(encoding="utf-8")))
    return found


def _content_strings():
    names_only = {"Vittorio", "Jean Paul Lab", "Vittorio Espresso Grande", "Vittorio Costa Rica", "Vittorio Espresso 100% Arabica"}
    strings = [item["label"] for item in NAV] + list(GROUPS)
    strings += [entry["label"] for entry in BRAND_FILTERS]
    strings += [brand[key] for brand in BRANDS for key in ("line", "body")]
    strings += [CYPRUS_B2B[key] for key in ("eyebrow", "title", "lede")]
    strings += [chapter[key] for chapter in CYPRUS_B2B["chapters"] for key in ("label", "title", "body")]
    strings += [town["name"] for town in CYPRUS_B2B["towns"]] + [piece["alt"] for piece in CYPRUS_B2B["scene"]]
    strings += [entry[key] for entry in FAQ for key in ("question", "answer")]
    strings += [article[key] for article in ARTICLES for key in ("title", "date_label", "summary")]
    strings += [paragraph for article in ARTICLES for paragraph in article["body"]]
    strings += [programme["alt"] for programme in MACHINE_PROGRAMMES]
    strings += [HERO["headline"], ANNOUNCEMENT, BUSINESS["locality"], BUSINESS["region"], BUSINESS["country"]]
    return {text for text in strings if text not in names_only}


def test_every_ui_string_has_a_greek_translation():
    missing = sorted(text for text in _template_strings() | _content_strings() if text not in EL)
    assert not missing, missing
