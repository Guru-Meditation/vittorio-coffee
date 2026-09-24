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
    "/health/mail",
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
            assert item["image"]["web"]["lg"]["file"] in page
    for item in ARTICLES:
        response = client.get(f"/journal/{item['slug']}")
        assert response.status_code == 200


def test_unknown_pages(client):
    assert client.get("/products/not-a-product").status_code == 404
    assert client.get("/journal/not-a-note").status_code == 404
    assert client.get("/missing").status_code == 404


def test_catalogue_puts_coffee_before_serviceware(client):
    page = client.get("/products").get_data(as_text=True)
    assert page.index("Costa Rica") < page.index("Aromatic Chocolate No.2")
    assert page.index("Aromatic Chocolate No.2") < page.index("Granite Straws")
    assert page.index(">Coffee<") < page.index(">Serviceware<")
    straw = client.get("/products/granite-straws-x-1000-pcs").get_data(as_text=True)
    assert "products/web/granite-straws-x-1000-pcs-lg.webp" in straw


def test_catalogue_shows_pack_size(client):
    page = client.get("/products").get_data(as_text=True)
    assert page.count("0.5 kg") >= 5
    assert page.count("1 kg") >= 2
    assert page.count("350gr") >= 3
    assert "1000 pcs" in page
    assert "card-pack" in page
    vanillia_card = page.split("Milkshake Vanilla", 1)[1].split("Add to order", 1)[0]
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
    assert b"Guatemala" in found.data
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
    assert "0.5 kg" in page
    assert "order-line-media" in page
    assert "products/costa-rica" in page
    assert "Cyprus" in page
    assert "payment on delivery" in page.lower()
    assert "Submit order" in page
    assert "VAT (5%)" in page
    assert "Total to pay on delivery" in page
    assert "Free delivery on orders over €40" in page
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
    assert "cash on delivery" in body.lower()
    assert "Order confirmation" in body
    assert "Reference" in body
    assert "0.5 kg" in body
    assert "Contact on Viber" in body
    assert "Email order" in body
    assert "viber://chat" in body
    assert "Total to pay on delivery" in body
    assert "€35.66" in body
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


def test_order_confirmation_warns_when_depot_email_fails(monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, "send_mail", lambda *args, **kwargs: False)
    flask_app = app_module.create_app()
    flask_app.config.update(TESTING=True)
    client = flask_app.test_client()
    client.post("/cart/add", data={"slug": "costa-rica", "qty": "1"})
    placed = client.post(
        "/order",
        data={"name": "Koxar", "phone": "99123456", "email": "koxar@example.com", "town": "Larnaca"},
    )
    assert placed.status_code == 302
    body = client.get("/order/received").get_data(as_text=True)
    assert "has not reached Vittorio yet" in body
    assert "viber://chat" in body


def test_order_again_link_refills_cart_with_valid_items(client):
    response = client.get("/order/again?items=costa-rica:2,not-a-product:1,filter:0")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/order")
    page = client.get("/order").get_data(as_text=True)
    assert 'name="qty-costa-rica" type="number" min="0" max="99" value="2"' in page
    assert "qty-filter" not in page


def test_order_again_without_items_goes_to_catalogue(client):
    response = client.get("/order/again")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/products")


def test_repeat_customer_sees_last_order_and_saved_details(client):
    client.post("/cart/add", data={"slug": "costa-rica", "qty": "3"})
    client.post(
        "/order",
        data={
            "name": "Koxar",
            "business_name": "Harbour Bar",
            "phone": "99123456",
            "email": "koxar@example.com",
            "town": "Larnaca",
        },
    )
    done = client.get("/order/received").get_data(as_text=True)
    assert "A copy is on its way to koxar@example.com" in done
    page = client.get("/order").get_data(as_text=True)
    assert "Your last order" in page
    assert "Order the same again" in page
    assert 'value="99123456"' not in page  # checkout form is hidden until the cart has items
    client.get("/order/again")
    refilled = client.get("/order").get_data(as_text=True)
    assert 'name="qty-costa-rica" type="number" min="0" max="99" value="3"' in refilled
    assert 'value="99123456"' in refilled


def test_home_presents_both_brands(client):
    home = client.get("/").get_data(as_text=True)
    assert "Official Cyprus representative of Vittorio Gourmet Espresso and Jean Paul Lab" in home
    assert "brand/jean-paul.png" in home
    assert "Browse Jean Paul Lab" in home
    assert "/products?brand=jean-paul-lab" in home
    assert "depot" not in home.lower()


def test_catalogue_brand_filter(client):
    jp = client.get("/products?brand=jean-paul-lab").get_data(as_text=True)
    assert "Fruit Smoothies – Mango" in jp
    assert "Espresso Grande" not in jp
    assert "31 products" in jp
    vittorio = client.get("/products?brand=vittorio").get_data(as_text=True)
    assert "Espresso Grande" in vittorio
    assert "Fruit Smoothies" not in vittorio
    assert client.get("/products?brand=nope").status_code == 404
    assert b"Blue Night" in client.get("/products?q=jean+paul").data


def test_home_hero_uses_real_packshots(client):
    home = client.get("/").get_data(as_text=True)
    assert "hero-bar" not in home
    assert "images/hero/espresso-grande.webp" in home
    assert "images/hero/smoothies-syrups-mango.webp" in home
    assert "brand/share.jpg" in home  # link preview image


def test_home_copy_stays_short(client):
    home = client.get("/").get_data(as_text=True)
    assert "by car" not in home.lower()
    assert "Choose" not in home
    assert "steps" not in home


def test_hero_packs_explain_and_open_their_category(client):
    home = client.get("/").get_data(as_text=True)
    assert 'href="/products?category=Coffee"' in home
    assert 'href="/products?category=Teas"' in home
    assert 'role="tooltip"' in home
    assert "Jean Paul Lab tea: Blue Night fruit tea." in home
    assert "All teas" in home
    assert 'href="/products?brand=jean-paul-lab&amp;category=Smoothies"' in home


def test_b2b_story_builds_the_counter(client):
    page = client.get("/cyprus").get_data(as_text=True)
    for title in ("Your espresso machine", "Vittorio coffee", "Beyond coffee", "Delivered across Cyprus", "Machine service"):
        assert title in page
    assert "images/scene/machine.webp" in page
    assert 'class="scene-map"' in page
    assert "Private Label" not in page
