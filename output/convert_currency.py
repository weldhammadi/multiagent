import os
from typing import Literal


def convert_currency(
    amount: float,
    direction: Literal["EUR_TO_USD", "USD_TO_EUR"],
    rate: float,
) -> float:
    """Convert a monetary amount between euros and dollars.

    Args:
        amount: The monetary amount to convert. Must be non‑negative.
        direction: Conversion direction, either "EUR_TO_USD" or "USD_TO_EUR".
        rate: The conversion rate. Must be a positive number.

    Returns:
        The converted amount as a ``float``.

    Raises:
        ValueError: If ``amount`` is negative, ``rate`` is non‑positive, or
            ``direction`` is not one of the accepted literals.
    """
    if amount < 0:
        raise ValueError("Le montant ne peut pas être négatif")
    if rate <= 0:
        raise ValueError("Le taux de conversion doit être strictement positif")

    if direction == "EUR_TO_USD":
        return amount * rate
    if direction == "USD_TO_EUR":
        return amount / rate

    # This point should never be reached because ``direction`` is typed as a Literal,
    # but we keep a defensive check for runtime safety.
    raise ValueError(
        "Direction invalide : doit être 'EUR_TO_USD' ou 'USD_TO_EUR'"
    )
