from decimal import Decimal

from order_pricing import compute_order_totals


def test_business_totals_add_vat_and_no_delivery_charge():
    lines = [{"line_amount": Decimal("29.20")}]
    totals = compute_order_totals(lines, missing_price=False)
    assert totals["subtotal"] == "€29.20"
    assert totals["vat"] == "€1.46"
    assert totals["delivery"] is None
    assert totals["total"] == "€30.66"
    assert totals["free_delivery"] is False
    assert totals["amount_to_free_delivery"] is None


def test_home_delivery_fee_under_forty():
    lines = [{"line_amount": Decimal("29.20"), "line_gross": Decimal("30.66")}]
    totals = compute_order_totals(lines, missing_price=False, business=False)
    assert totals["subtotal"] == "€29.20"
    assert totals["vat"] == "€1.46"
    assert totals["delivery"] == "€5.00"
    assert totals["total"] == "€35.66"
    assert totals["free_delivery"] is False


def test_home_free_delivery_over_forty():
    lines = [{"line_amount": Decimal("40.00"), "line_gross": Decimal("42.00")}]
    totals = compute_order_totals(lines, missing_price=False, business=False)
    assert totals["delivery"] == "Free"
    assert totals["free_delivery"] is True
    assert totals["total"] == "€42.00"


def test_vat_free_lines_carry_no_vat():
    lines = [
        {"line_amount": Decimal("14.60"), "line_gross": Decimal("14.60"), "vat_free": True},
        {"line_amount": Decimal("10.00"), "line_gross": Decimal("10.50")},
    ]
    business = compute_order_totals(lines, missing_price=False)
    assert business["vat"] == "€0.50"
    assert business["total"] == "€25.10"
    home = compute_order_totals(lines, missing_price=False, business=False)
    assert home["vat"] == "€0.50"
    assert home["subtotal"] == "€24.60" and home["total"] == "€30.10"  # + €5 delivery


def test_coffee_price_label_has_no_vat():
    from app import create_app

    client = create_app().test_client()
    page = client.get("/products/costa-rica").get_data(as_text=True)
    assert "€14.60, no VAT" in page
    assert "€15.33" not in page
    with client.session_transaction() as sess:
        sess["buyer"] = "business"
    page = client.get("/products/costa-rica").get_data(as_text=True)
    assert "€14.60, no VAT" in page
    tea = client.get("/products/green-tea").get_data(as_text=True)
    assert "€5.70 + VAT" in tea
