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
    assert totals["subtotal"] == "€30.66"
    assert totals["vat"] == "€1.46"
    assert totals["delivery"] == "€5.00"
    assert totals["total"] == "€35.66"
    assert totals["free_delivery"] is False


def test_home_free_delivery_over_forty():
    lines = [{"line_amount": Decimal("38.10"), "line_gross": Decimal("40.00")}]
    totals = compute_order_totals(lines, missing_price=False, business=False)
    assert totals["delivery"] == "Free"
    assert totals["free_delivery"] is True
    assert totals["total"] == "€40.00"
