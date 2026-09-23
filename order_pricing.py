from decimal import Decimal, ROUND_HALF_UP

from content import ORDER

VAT_RATE = Decimal(str(ORDER["vat_rate"]))
FREE_DELIVERY_MIN = Decimal(str(ORDER["free_delivery_min"]))
DELIVERY_FEE = Decimal(str(ORDER["delivery_fee"]))


def _money(amount):
    return f"€{amount:.2f}"


def compute_order_totals(lines, missing_price=False):
    """Catalogue line prices are ex VAT. Returns None if any line lacks a price."""
    if missing_price or not lines:
        return None
    subtotal = Decimal("0")
    for line in lines:
        amount = line.get("line_amount")
        if amount is None:
            return None
        subtotal += amount
    vat = (subtotal * VAT_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    delivery_amount = Decimal("0") if subtotal >= FREE_DELIVERY_MIN else DELIVERY_FEE
    total = subtotal + vat + delivery_amount
    to_free = max(FREE_DELIVERY_MIN - subtotal, Decimal("0"))
    return {
        "subtotal": _money(subtotal),
        "vat": _money(vat),
        "vat_label": ORDER["vat_label"],
        "delivery": "Free" if delivery_amount == 0 else _money(delivery_amount),
        "free_delivery": subtotal >= FREE_DELIVERY_MIN,
        "amount_to_free_delivery": _money(to_free) if to_free > 0 else None,
        "total": _money(total),
    }


def totals_for_session(totals):
    if not totals:
        return None
    return dict(totals)
