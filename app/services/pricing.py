from decimal import Decimal, ROUND_HALF_UP

from app.config.settings import settings


DEFAULT_PRICES = {
    "NGN": {
        "cleanflow_file": Decimal("100"),
    },
    "GBP": {
        "cleanflow_file": Decimal("0.10"),
    },
    "USD": {
        "cleanflow_file": Decimal("0.15"),
    },
    "EUR": {
        "cleanflow_file": Decimal("0.15"),
    },
}


CURRENCY_SYMBOLS = {
    "NGN": "₦",
    "GBP": "£",
    "USD": "$",
    "EUR": "€",
}


def validate_currency(currency: str) -> str:
    currency = currency.upper().strip()

    if currency not in settings.supported_currencies:
        raise ValueError(f"Unsupported currency: {currency}")

    return currency


def cleanflow_file_price(
    quantity: int,
    currency: str = "NGN",
) -> Decimal:
    """
    Calculate the current basic CleanFlow file price.

    Quantity-based volume pricing can be added later without changing
    the API contract.
    """

    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")

    currency = validate_currency(currency)

    price = DEFAULT_PRICES[currency]["cleanflow_file"]

    # Initial volume pricing.
    if currency == "NGN":
        if quantity >= 501:
            price = Decimal("50")
        elif quantity >= 101:
            price = Decimal("60")
        elif quantity >= 51:
            price = Decimal("70")
        elif quantity >= 11:
            price = Decimal("80")

    total = price * quantity

    return total.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def currency_symbol(currency: str) -> str:
    currency = validate_currency(currency)
    return CURRENCY_SYMBOLS[currency]