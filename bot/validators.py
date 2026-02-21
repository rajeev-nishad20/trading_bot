"""
Input validation helpers for the Trading Bot CLI.
All validation errors raise ValueError with human-readable messages.
"""

from __future__ import annotations

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_symbol(symbol: str) -> str:
    """Ensure symbol is non-empty and uppercase."""
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be empty.")
    if not symbol.isalnum():
        raise ValueError(f"Symbol '{symbol}' contains invalid characters.")
    return symbol


def validate_side(side: str) -> str:
    """Ensure side is BUY or SELL."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(f"Side must be one of {VALID_SIDES}, got '{side}'.")
    return side


def validate_order_type(order_type: str) -> str:
    """Ensure order type is one of the supported types."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(f"Order type must be one of {VALID_ORDER_TYPES}, got '{order_type}'.")
    return order_type


def validate_quantity(quantity: float) -> float:
    """Ensure quantity is a positive number."""
    if quantity <= 0:
        raise ValueError(f"Quantity must be > 0, got {quantity}.")
    return quantity


def validate_price(price: float | None, order_type: str) -> float | None:
    """
    Ensure price is provided and positive for LIMIT/STOP_MARKET orders.
    Price is ignored (and can be None) for MARKET orders.
    """
    if order_type in {"LIMIT", "STOP_MARKET"}:
        if price is None:
            raise ValueError(f"Price is required for {order_type} orders.")
        if price <= 0:
            raise ValueError(f"Price must be > 0, got {price}.")
    return price


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None = None,
    stop_price: float | None = None,
) -> dict:
    """
    Run all validations and return a clean params dict.

    Returns:
        Dict with validated and normalised parameters.
    """
    validated = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, order_type.strip().upper()),
    }

    if order_type.strip().upper() == "STOP_MARKET":
        if stop_price is None or stop_price <= 0:
            raise ValueError("stop_price is required and must be > 0 for STOP_MARKET orders.")
        validated["stop_price"] = stop_price

    return validated
