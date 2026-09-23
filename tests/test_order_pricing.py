from decimal import Decimal

from order_pricing import compute_order_totals


def test_compute_order_totals_with_vat_and_delivery():
    lines = [{"line_amount": Decimal("29.20")}]
    totals = compute_order_totals(lines, missing_price=False)
    assert totals["subtotal"] == "€29.20"
    assert totals["vat"] == "€1.46"
    assert totals["delivery"] == "€5.00"
    assert totals["total"] == "€35.66"
    assert totals["free_delivery"] is False


def test_free_delivery_over_forty():
    lines = [{"line_amount": Decimal("40.00")}]
    totals = compute_order_totals(lines, missing_price=False)
    assert totals["delivery"] == "Free"
    assert totals["free_delivery"] is True
    assert totals["total"] == "€42.00"
