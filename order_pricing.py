from decimal import Decimal, ROUND_HALF_UP

from content import ORDER

VAT_RATE = Decimal(str(ORDER["vat_rate"]))
FREE_DELIVERY_MIN = Decimal(str(ORDER["free_delivery_min"]))
DELIVERY_FEE = Decimal(str(ORDER["delivery_fee"]))
CENT = Decimal("0.01")
VAT_FREE_GROUPS = set(ORDER["vat_free_groups"])


def _money(amount):
    return f"€{amount:.2f}"


def is_vat_free(product):
    """Coffee and sugar are sold without VAT."""
    return product.get("group") in VAT_FREE_GROUPS


def with_vat(amount, vat_free=False):
    """Home price of one pack: the trade price plus VAT (none for VAT-free goods), rounded to the cent shown."""
    if vat_free:
        return amount
    return (amount * (1 + VAT_RATE)).quantize(CENT, rounding=ROUND_HALF_UP)


def compute_order_totals(lines, missing_price=False, business=True):
    """Everyone sees prices ex VAT with VAT added on top (owner's choice, 2026-10-17).

    Each line carries `line_amount` (ex VAT). Lines with `vat_free` set (coffee, sugar) carry no VAT.
    Home orders get free delivery from €40 of goods (ex VAT), otherwise a flat fee.
    Business orders carry no delivery charge; the depot arranges trade delivery.
    Returns None if any line lacks a price.
    """
    if missing_price or not lines:
        return None
    key = "line_amount"
    subtotal = Decimal("0")
    for line in lines:
        amount = line.get(key)
        if amount is None:
            return None
        subtotal += amount
    taxable = sum((line[key] for line in lines if not line.get("vat_free")), Decimal("0"))
    vat = (taxable * VAT_RATE).quantize(CENT, rounding=ROUND_HALF_UP)
    goods = subtotal + vat
    if business:
        delivery_amount, to_free = Decimal("0"), Decimal("0")
    else:
        delivery_amount = Decimal("0") if subtotal >= FREE_DELIVERY_MIN else DELIVERY_FEE
        to_free = max(FREE_DELIVERY_MIN - subtotal, Decimal("0"))
    return {
        "subtotal": _money(subtotal),
        "vat": _money(vat),
        "vat_label": ORDER["vat_label"],
        "incl_vat": False,
        "delivery": None if business else ("Free" if delivery_amount == 0 else _money(delivery_amount)),
        "free_delivery": not business and subtotal >= FREE_DELIVERY_MIN,
        "amount_to_free_delivery": _money(to_free) if to_free > 0 else None,
        "total": _money(goods + delivery_amount),
    }


def totals_for_session(totals):
    if not totals:
        return None
    return dict(totals)
