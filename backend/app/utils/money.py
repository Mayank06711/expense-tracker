from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

PAISA_MULTIPLIER = Decimal("100")
TWO_PLACES = Decimal("0.01")


def rupees_to_paisa(amount_str: str) -> int:
    """Convert rupee string to paisa integer. '150.50' → 15050"""
    try:
        amount = Decimal(amount_str)
    except InvalidOperation:
        raise ValueError(f"Invalid amount format: {amount_str}")

    if amount <= 0:
        raise ValueError("Amount must be greater than zero")

    if amount > Decimal("9999999.99"):
        raise ValueError("Amount exceeds maximum allowed (₹99,99,999.99)")

    # Check max 2 decimal places
    if amount != amount.quantize(TWO_PLACES):
        raise ValueError("Amount cannot have more than 2 decimal places")

    paisa = int(amount * PAISA_MULTIPLIER)
    return paisa


def paisa_to_rupees(paisa: int) -> str:
    """Convert paisa integer to rupee string. 15050 → '150.50'"""
    amount = Decimal(paisa) / PAISA_MULTIPLIER
    return str(amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP))
