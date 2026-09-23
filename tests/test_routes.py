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
    "/supply",
    "/cyprus",
    "/machines",
    "/order",
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


def test_catalogue_puts_coffee_before_serviceware(client):
    page = client.get("/products").get_data(as_text=True)
    assert page.index("Costa Rica") < page.index("Chocolate with Black Forest")
    assert page.index("Chocolate with Black Forest") < page.index("Granite Straws")
    assert page.index(">Coffee<") < page.index(">Serviceware<")
    straw = client.get("/products/granite-straws-x-1000-pcs").get_data(as_text=True)
    assert "products/granite-straws-x-1000-pcs.png" in straw


def test_catalogue_shows_pack_size(client):
    page = client.get("/products").get_data(as_text=True)
    assert page.count("0.5 kg") >= 5
    assert page.count("1 kg") >= 2
    assert page.count("350gr") >= 3
    assert "1000 pcs" in page
    assert "card-pack" in page
    vanillia_card = page.split("Milkshake Vanillia", 1)[1].split("Add to order", 1)[0]
    assert "350gr" in vanillia_card


def test_pack_field_matches_published_quantities():
    from content import PRODUCTS, catalog_pack_label

    by_slug = {item["slug"]: item for item in PRODUCTS}
    assert catalog_pack_label(by_slug["lemon-granita-powder"]) == "0.5 kg"
    assert catalog_pack_label(by_slug["strawberry-granita"]) == "0.5 kg"
    assert catalog_pack_label(by_slug["granite-straws-x-1000-pcs"]) == "1000 pcs"
    assert catalog_pack_label(by_slug["milkshake-vanillia"]) == "350gr"
    assert catalog_pack_label(by_slug["smoothies-syrups-peach"]) == "1 ltr"
    assert catalog_pack_label(by_slug["white-life-chamomile"]) == "50gr"
    with_pack = sum(1 for item in PRODUCTS if catalog_pack_label(item))
    assert with_pack == 45


def test_catalogue_filter_and_search(client):
    coffee = client.get("/products?category=Coffee")
    assert coffee.status_code == 200
    assert b"Costa Rica" in coffee.data
    assert client.get("/products?category=Nope").status_code == 404
    found = client.get("/products?q=guatemala")
    assert b"GUATEMALA" in found.data
    empty = client.get("/products?q=zzzz-no-match")
    assert b"Nothing in the catalogue matches" in empty.data


def test_contact_validation_and_success(client):
    bad = client.post("/contact", data={"name": "", "email": "nope", "message": "short"})
    assert bad.status_code == 400
    assert b"Enter your name." in bad.data
    ok = client.post(
        "/contact",
        data={"name": "Koxar", "email": "koxar@example.com", "message": "Please confirm the Kalo Xorio hours."},
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
    assert "Kalo Xorio, Larnaca" in html
    assert "Synergasias 17" not in html
    assert "Monday–Sunday" not in html
    assert "info@vittoriocaffee.com" not in html
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
    assert "Contact" in home
    assert "B2B Services" in home
    cyprus = client.get("/cyprus").get_data(as_text=True)
    assert "Vittorio B2B Services" in cyprus
    assert "across Cyprus" in cyprus
    assert "Greece" not in cyprus
    assert 'aria-controls="site-nav"' in home
    assert "prefers-reduced-motion" in client.get("/static/css/site.css").get_data(as_text=True)


def test_order_flow_and_cyprus_delivery(client):
    added = client.post("/cart/add", data={"slug": "costa-rica", "qty": "2"})
    assert added.status_code == 302
    assert added.headers["Location"].endswith("/order")
    page = client.get("/order").get_data(as_text=True)
    assert "Costa Rica" in page
    assert "order-line-media" in page
    assert "products/costa-rica" in page
    assert "Cyprus" in page
    assert "payment on delivery" in page.lower()
    assert "Submit order" in page
    placed = client.post(
        "/order",
        data={
            "name": "Koxar",
            "business_name": "Harbour Bar",
            "phone": "99123456",
            "email": "koxar@example.com",
            "town": "Larnaca",
            "notes": "",
        },
    )
    assert placed.status_code == 302
    done = client.get("/order/received")
    assert done.status_code == 200
    body = done.get_data(as_text=True)
    assert "Harbour Bar" in body
    assert "99123456" in body
    assert "payment on delivery" in body.lower()
    assert "Order confirmation" in body
    assert "Reference" in body
    assert "Open Viber with this order" in body
    assert "viber://chat" in body
    assert "Ready for the depot" not in body
    assert "Email order" not in body
    retail = client.post("/cart/add", data={"slug": "costa-rica", "qty": "1"})
    assert retail.status_code == 302
    placed_retail = client.post(
        "/order",
        data={
            "name": "Koxar",
            "business_name": "",
            "phone": "99123456",
            "email": "koxar@example.com",
            "town": "Larnaca",
            "notes": "",
        },
    )
    assert placed_retail.status_code == 302
    retail_done = client.get("/order/received").get_data(as_text=True)
    assert "Enter the café or bar name." not in retail_done
    assert "Larnaca, Cyprus" in retail_done
    assert "viber://chat?number=" in client.get("/").get_data(as_text=True)
    machines = client.get("/machines").get_data(as_text=True)
    assert "Apia Life" in machines
    assert "Sanremo" in machines
    assert "Expobar" in machines
    assert "no charge" in machines
    assert "machines/apia-vittoria-ii.jpg" in machines
    assert "machines/sanremo-opera.jpg" in machines
    assert "machines/expobar-elegance.jpg" in machines
    machines_main = machines.split("<main", 1)[1].split("</main>", 1)[0]
    assert 'href="/contact"' not in machines_main
    assert ">Viber</a>" not in machines_main


def test_does_not_invent_claims(client):
    home = client.get("/").get_data(as_text=True).casefold()
    for phrase in ("yirgacheffe", "italian roast", "signature blend", "award", "organic certified", "100% growth"):
        assert phrase not in home
