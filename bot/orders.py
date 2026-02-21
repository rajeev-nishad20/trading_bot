"""
Order placement logic layer.
Sits between the CLI and the raw Binance client.
"""

from __future__ import annotations

from typing import Any

from bot.client import BinanceFuturesClient, BinanceAPIError
from bot.logging_config import setup_logging
from bot.validators import validate_all

logger = setup_logging()

# ── ANSI colour helpers (degrade gracefully if terminal has no colours) ──

GREEN  = "\033[92m"
RED    = "\033[91m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def _fmt(colour: str, text: str) -> str:
    return f"{colour}{text}{RESET}"


def _print_order_summary(params: dict) -> None:
    """Print a formatted order request summary."""
    print(f"\n{BOLD}{CYAN}{'━' * 50}{RESET}")
    print(f"{BOLD}  📋  ORDER SUMMARY{RESET}")
    print(f"{CYAN}{'━' * 50}{RESET}")
    print(f"  Symbol     : {_fmt(BOLD, params['symbol'])}")
    print(f"  Side       : {_fmt(GREEN if params['side'] == 'BUY' else RED, params['side'])}")
    print(f"  Type       : {params['order_type']}")
    print(f"  Quantity   : {params['quantity']}")
    if params.get("price"):
        print(f"  Price      : {params['price']}")
    if params.get("stop_price"):
        print(f"  Stop Price : {params['stop_price']}")
    print(f"{CYAN}{'━' * 50}{RESET}\n")


def _print_order_response(response: dict) -> None:
    """Print a formatted order response from Binance."""
    print(f"\n{BOLD}{GREEN}  ✅  ORDER PLACED SUCCESSFULLY{RESET}")
    print(f"{GREEN}{'━' * 50}{RESET}")
    print(f"  Order ID      : {response.get('orderId', 'N/A')}")
    print(f"  Client OID    : {response.get('clientOrderId', 'N/A')}")
    print(f"  Symbol        : {response.get('symbol', 'N/A')}")
    print(f"  Status        : {_fmt(YELLOW, response.get('status', 'N/A'))}")
    print(f"  Side          : {response.get('side', 'N/A')}")
    print(f"  Type          : {response.get('type', 'N/A')}")
    print(f"  Orig Qty      : {response.get('origQty', 'N/A')}")
    print(f"  Executed Qty  : {response.get('executedQty', 'N/A')}")
    avg = response.get("avgPrice") or response.get("price", "N/A")
    print(f"  Avg Price     : {avg}")
    print(f"  Update Time   : {response.get('updateTime', 'N/A')}")
    print(f"{GREEN}{'━' * 50}{RESET}\n")


def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None = None,
    stop_price: float | None = None,
    reduce_only: bool = False,
) -> dict[str, Any]:
    """
    Validate inputs, place an order via the client, and pretty-print results.

    Returns:
        Binance API order response dict.

    Raises:
        ValueError:        on invalid inputs.
        BinanceAPIError:   on API-level errors.
        requests.RequestException: on network failures.
    """
    # ── 1. Validate ────────────────────────────────────────────────────
    params = validate_all(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )
    logger.debug("Validated params: %s", params)

    # ── 2. Print summary ────────────────────────────────────────────────
    _print_order_summary(params)

    # ── 3. Send order ───────────────────────────────────────────────────
    try:
        response = client.place_order(
            symbol=params["symbol"],
            side=params["side"],
            order_type=params["order_type"],
            quantity=params["quantity"],
            price=params.get("price"),
            stop_price=params.get("stop_price"),
            reduce_only=reduce_only,
        )
    except BinanceAPIError as exc:
        logger.error("Binance API error: %s", exc)
        print(f"\n{RED}{'━' * 50}")
        print(f"  ❌  ORDER FAILED")
        print(f"{'━' * 50}")
        print(f"  Code    : {exc.code}")
        print(f"  Message : {exc.message}")
        print(f"{'━' * 50}{RESET}\n")
        raise

    # ── 4. Log & print response ─────────────────────────────────────────
    logger.info(
        "Order placed | id=%s status=%s executedQty=%s",
        response.get("orderId"),
        response.get("status"),
        response.get("executedQty"),
    )
    _print_order_response(response)
    return response
