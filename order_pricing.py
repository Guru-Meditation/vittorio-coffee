from decimal import Decimal, ROUND_HALF_UP

from content import ORDER

VAT_RATE = Decimal(str(ORDER["vat_rate"]))
FREE_DELIVERY_MIN = Decimal(str(ORDER["free_delivery_min"]))
DELIVERY_FEE = Decimal(str(ORDER["delivery_fee"]))
CENT = Decimal("0.01")


def _money(amount):
    return f"€{amount:.2f}"


def with_vat(amount):
    """Home price of one pack: the trade price plus VAT, rounded to the cent shown on the site."""
    return (amount * (1 + VAT_RATE)).quantize(CENT, rounding=ROUND_HALF_UP)


def compute_order_totals(lines, missing_price=False, business=True):
    """Businesses see trade prices ex VAT with VAT added; home buyers see VAT-inclusive prices.

    Each line carries `line_amount` (ex VAT) and, for home orders, `line_gross` (incl. VAT).
    Home orders get free delivery from €40 of goods (VAT included), otherwise a flat fee.
    Business orders carry no delivery charge; the depot arranges trade delivery.
    Returns None if any line lacks a price.
    """
    if missing_price or not lines:
        return None
    key = "line_amount" if business else "line_gross"
    subtotal = Decimal("0")
    for line in lines:
        amount = line.get(key)
        if amount is None:
            return None
        subtotal += amount
    if business:
        vat = (subtotal * VAT_RATE).quantize(CENT, rounding=ROUND_HALF_UP)
        goods = subtotal + vat
    else:
        vat = (subtotal - subtotal / (1 + VAT_RATE)).quantize(CENT, rounding=ROUND_HALF_UP)
        goods = subtotal
    if business:
        delivery_amount, to_free = Decimal("0"), Decimal("0")
    else:
        delivery_amount = Decimal("0") if subtotal >= FREE_DELIVERY_MIN else DELIVERY_FEE
        to_free = max(FREE_DELIVERY_MIN - subtotal, Decimal("0"))
    return {
        "subtotal": _money(subtotal),
        "vat": _money(vat),
        "vat_label": ORDER["vat_label"],
        "incl_vat": not business,
        "delivery": None if business else ("Free" if delivery_amount == 0 else _money(delivery_amount)),
        "free_delivery": not business and subtotal >= FREE_DELIVERY_MIN,
        "amount_to_free_delivery": _money(to_free) if to_free > 0 else None,
        "total": _money(goods + delivery_amount),
    }


def totals_for_session(totals):
    if not totals:
        return None
    return dict(totals)
