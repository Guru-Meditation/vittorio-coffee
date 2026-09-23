import html

import pytest

from app import create_app
from content import ARTICLES, PRODUCTS

PAGES = [
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
    "/sitemap.xml",
    "/robots.txt",
]


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.mark.parametrize("path", PAGES)
def test_public_pages(client, path):
    response = client.get(path)
    assert response.status_code == 200


def test_every_product_and_article(client):
    for item in PRODUCTS:
        response = client.get(f"/products/{item['slug']}")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert html.escape(item["name"]) in page
        assert item["price_label"] in page
        if item["image"]:
            assert item["image"]["file"] in page
    for item in ARTICLES:
        response = client.get(f"/journal/{item['slug']}")
        assert response.status_code == 200


def test_unknown_pages(client):
    assert client.get("/products/not-a-product").status_code == 404
    assert client.get("/journal/not-a-note").status_code == 404
    assert client.get("/missing").status_code == 404


def test_catalogue_filter_and_search(client):
    coffee = client.get("/products?category=Coffee")
    assert coffee.status_code == 200
    assert b"Costa Rica" in coffee.data
    assert client.get("/products?category=Nope").status_code == 404
    found = client.get("/products?q=guatemala")
    assert b"Guatemala" in found.data
    empty = client.get("/products?q=zzzz-no-match")
    assert b"Nothing in the catalogue matches" in empty.data


def test_contact_validation_and_success(client):
    bad = client.post("/contact", data={"name": "", "email": "nope", "message": "short"})
    assert bad.status_code == 400
    assert b"Enter your name." in bad.data
    ok = client.post(
        "/contact",
        data={"name": "Koxar", "email": "koxar@example.com", "message": "Please confirm the Kiti hours."},
    )
    assert ok.status_code == 200
    assert b"Thank you" in ok.data
    honeypot = client.post(
        "/contact",
        data={"name": "", "email": "", "message": "", "company_website": "https://spam.example"},
    )
    assert honeypot.status_code == 200
    assert b"Thank you" in honeypot.data


def test_seo_and_store_schema(client):
    home = client.get("/")
    html = home.get_data(as_text=True)
    assert "<title>Vittorio Gourmet Espresso" in html
    assert 'rel="canonical"' in html
    assert 'property="og:description"' in html
    assert '"@type": "Store"' in html
    assert "Restaurant" not in html
    assert "Synergasias 17" in html
    sitemap = client.get("/sitemap.xml").get_data(as_text=True)
    assert "/products/costa-rica" in sitemap
    assert "/visit" in sitemap
    robots = client.get("/robots.txt").get_data(as_text=True)
    assert "Sitemap:" in robots


def test_menu_alias_and_navigation(client):
    menu = client.get("/menu")
    assert menu.status_code == 302
    assert menu.headers["Location"].endswith("/products")
    home = client.get("/").get_data(as_text=True)
    assert "Visit us" in home
    assert 'aria-controls="site-nav"' in home
    assert "prefers-reduced-motion" in client.get("/static/css/site.css").get_data(as_text=True)


def test_does_not_invent_claims(client):
    home = client.get("/").get_data(as_text=True).casefold()
    for phrase in ("yirgacheffe", "italian roast", "signature blend", "award", "organic certified", "100% growth"):
        assert phrase not in home
