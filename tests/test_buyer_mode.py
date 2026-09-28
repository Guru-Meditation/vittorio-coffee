"""The "For home / For business" switch: home prices include VAT, business prices are trade prices ex VAT."""
import pytest

import app as app_module
from app import create_app
from mailing import format_order_mail


@pytest.fixture
def client():
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


def business(client, lang=""):
    return client.post(f"{lang}/prices", data={"buyer": "business", "next": f"{lang}/products"})


def test_home_prices_include_vat_by_default(client):
    page = client.get("/products/espresso-grande").get_data(as_text=True)
    assert "€26.88 incl. VAT" in page  # €25.60 trade + 5%
    assert "€25.60 + VAT" not in page
    assert 'value="home" aria-pressed="true"' in page


def test_business_switch_shows_trade_prices_and_vat_notice(client):
    switched = business(client)
    assert switched.status_code == 302
    assert switched.headers["Location"] == "/products"
    page = client.get("/products/espresso-grande").get_data(as_text=True)
    assert "€25.60 + VAT" in page
    assert "incl. VAT" not in page
    assert 'value="business" aria-pressed="true"' in page
    assert "Prices exclude VAT." in page
    # And back again.
    client.post("/prices", data={"buyer": "home"})
    assert "€26.88 incl. VAT" in client.get("/products/espresso-grande").get_data(as_text=True)


def test_switch_only_returns_to_this_site(client):
    response = client.post("/prices", data={"buyer": "business", "next": "https://evil.example/x"})
    assert response.headers["Location"] == "/"


def test_greek_business_notice(client):
    business(client, "/el")
    page = client.get("/el/products/espresso-grande").get_data(as_text=True)
    assert "€25.60 + ΦΠΑ" in page
    client.post("/el/prices", data={"buyer": "home"})
    assert "€26.88 με ΦΠΑ" in client.get("/el/products/espresso-grande").get_data(as_text=True)


ORDER_FORM = {
    "name": "Maria",
    "phone": "99123456",
    "email": "maria@example.com",
    "address": "Makariou 12, 1st floor",
    "town": "Larnaca",
}


def test_home_order_totals_include_vat(client):
    client.post("/cart/add", data={"slug": "espresso-grande", "qty": "1"})
    page = client.get("/order").get_data(as_text=True)
    assert "Subtotal (incl. VAT)" in page
    assert "Includes VAT (5%)" in page
    assert "€26.88" in page
    assert "€31.88" in page  # plus €5 delivery under €40
    assert 'id="vat_number"' not in page
    assert "Deliveries are done by ACS." in page
    client.post("/order", data=ORDER_FORM)
    placed = client.get("/order/received").get_data(as_text=True)
    assert "€31.88" in placed
    assert "Deliveries are done by ACS." in placed


def test_business_order_needs_business_name_and_shows_vat_added(client):
    business(client)
    client.post("/cart/add", data={"slug": "espresso-grande", "qty": "2"})
    page = client.get("/order").get_data(as_text=True)
    assert "Subtotal (ex VAT)" in page
    assert "€51.20" in page and "€2.56" in page and "€53.76" in page
    totals = page.split('class="order-totals"', 1)[1].split("</table>", 1)[0]
    assert "Delivery" not in totals
    assert "Free delivery on orders over" not in page
    assert 'id="vat_number"' in page
    assert "ACS" not in page
    missing = client.post("/order", data=ORDER_FORM)
    assert missing.status_code == 400
    assert "Enter the business name for a trade order." in missing.get_data(as_text=True)
    done = client.post("/order", data={**ORDER_FORM, "business_name": "Harbour Bar", "vat_number": "CY10000000X"})
    assert done.status_code == 302
    placed = client.get("/order/received").get_data(as_text=True)
    assert "CY10000000X" in placed
    assert "€53.76" in placed


def test_depot_email_says_trade_or_retail():
    trade_subject, trade_body = format_order_mail({"ref": "A1", "buyer": "business", "vat_number": "CY1", "lines": []})
    assert trade_subject == "Vittorio TRADE order A1"
    assert "TRADE order (business prices ex VAT)" in trade_body
    assert "VAT number: CY1" in trade_body
    retail_subject, retail_body = format_order_mail({"ref": "B2", "buyer": "home", "lines": []})
    assert retail_subject == "Vittorio RETAIL order B2"
    assert "RETAIL order (home prices incl. VAT)" in retail_body


def test_customer_email_names_acs_for_home_orders_only():
    from mailing import format_customer_copy

    _s, home = format_customer_copy({"ref": "C3", "buyer": "home", "lines": []}, "http://x/again", lang="el")
    assert "Οι παραδόσεις γίνονται μέσω ACS." in home
    _s, trade = format_customer_copy({"ref": "D4", "buyer": "business", "lines": []}, "http://x/again")
    assert "ACS" not in trade


GLASS = "vittorio-freddo-espresso-glass"


def test_serving_line_is_free_from_sixty(client):
    home = client.get("/").get_data(as_text=True)
    assert "Vittorio cups and glasses" in home
    assert "Free with orders over €60" in home
    client.post("/cart/add", data={"slug": GLASS, "qty": "2"})
    client.post("/cart/add", data={"slug": "espresso-grande", "qty": "1"})  # €26.88 incl. VAT
    page = client.get("/order").get_data(as_text=True)
    assert "Add <strong>€33.12</strong> more, or remove them." in page
    short = client.post("/order", data=ORDER_FORM)
    assert short.status_code == 400
    assert "Vittorio cups and glasses are free with orders over €60. Add €33.12 more" in short.get_data(as_text=True)
    client.post("/cart/add", data={"slug": "espresso-grande", "qty": "2"})  # 3 × €26.88 = €80.64
    page = client.get("/order").get_data(as_text=True)
    assert "more, or remove them" not in page
    assert "€80.64" in page  # the glasses add nothing to the total
    assert client.post("/order", data=ORDER_FORM).status_code == 302
    placed = client.get("/order/received").get_data(as_text=True)
    assert "Freddo Espresso Glass" in placed and ">Free<" in placed


def test_serving_line_threshold_is_ex_vat_for_business(client):
    business(client)
    client.post("/cart/add", data={"slug": GLASS, "qty": "1"})
    client.post("/cart/add", data={"slug": "espresso-grande", "qty": "2"})  # €51.20 ex VAT
    assert "Add <strong>€8.80</strong> more" in client.get("/order").get_data(as_text=True)


def test_greek_serving_line(client):
    home = client.get("/el/").get_data(as_text=True)
    assert "Φλιτζάνια και ποτήρια Vittorio" in home
    assert "Δωρεάν με παραγγελίες άνω των €60" in home
