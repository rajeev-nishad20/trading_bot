#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║          BINANCE FUTURES TESTNET  —  TRADING BOT         ║
║                   CLI Entry Point                        ║
╚══════════════════════════════════════════════════════════╝

Usage (quick mode — all flags):
    python cli.py order --symbol BTCUSDT --side BUY --type MARKET --qty 0.001

Usage (interactive mode):
    python cli.py interactive

Usage (balance check):
    python cli.py balance

Credentials: set env vars  BINANCE_API_KEY  and  BINANCE_API_SECRET
             or pass       --api-key / --api-secret flags.
"""

from __future__ import annotations

import argparse
import os
import sys
import textwrap

from bot.client import BinanceFuturesClient, BinanceAPIError
from bot.logging_config import setup_logging
from bot.orders import place_order

logger = setup_logging()

# ── ANSI helpers ──────────────────────────────────────────────────────────

BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"

BANNER = f"""{CYAN}{BOLD}
╔══════════════════════════════════════════════════════════╗
║       🚀  Binance Futures Testnet  —  Trading Bot        ║
╚══════════════════════════════════════════════════════════╝{RESET}
"""


# ── Credential helpers ────────────────────────────────────────────────────

def _get_client(args: argparse.Namespace) -> BinanceFuturesClient:
    """Resolve API credentials from CLI flags → env vars → prompt."""
    api_key    = getattr(args, "api_key",    None) or os.getenv("BINANCE_API_KEY")
    api_secret = getattr(args, "api_secret", None) or os.getenv("BINANCE_API_SECRET")

    if not api_key:
        api_key = input("  Enter Binance Testnet API Key    : ").strip()
    if not api_secret:
        api_secret = input("  Enter Binance Testnet API Secret : ").strip()

    if not api_key or not api_secret:
        logger.error("API credentials missing.")
        sys.exit("❌  API key and secret are required.")

    logger.info("Client created with provided credentials.")
    return BinanceFuturesClient(api_key, api_secret)


# ── Sub-command handlers ──────────────────────────────────────────────────

def cmd_order(args: argparse.Namespace) -> None:
    """Handle the 'order' sub-command (non-interactive)."""
    client = _get_client(args)
    try:
        place_order(
            client=client,
            symbol=args.symbol,
            side=args.side.upper(),
            order_type=args.type.upper(),
            quantity=args.qty,
            price=args.price,
            stop_price=args.stop_price,
            reduce_only=args.reduce_only,
        )
    except (ValueError, BinanceAPIError) as exc:
        logger.error("Order failed: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        sys.exit(1)


def cmd_balance(args: argparse.Namespace) -> None:
    """Handle the 'balance' sub-command."""
    client = _get_client(args)
    try:
        balances = client.get_account_balance()
        print(f"\n{BOLD}{CYAN}{'━'*50}{RESET}")
        print(f"{BOLD}  💰  ACCOUNT BALANCES{RESET}")
        print(f"{CYAN}{'━'*50}{RESET}")
        for asset in balances:
            bal = float(asset.get("balance", 0))
            if bal > 0:
                print(f"  {asset['asset']:8s}  Balance: {bal:.4f}  "
                      f"Available: {float(asset.get('availableBalance', 0)):.4f}")
        print(f"{CYAN}{'━'*50}{RESET}\n")
    except BinanceAPIError as exc:
        sys.exit(f"❌  {exc}")


def cmd_interactive(args: argparse.Namespace) -> None:
    """Interactive menu-driven mode (Bonus: enhanced CLI UX)."""
    print(BANNER)
    client = _get_client(args)

    while True:
        print(f"\n{BOLD}  MAIN MENU{RESET}")
        print("  [1]  Place an Order")
        print("  [2]  View Account Balance")
        print("  [3]  View Open Orders")
        print("  [4]  Cancel an Order")
        print("  [q]  Quit\n")

        choice = input("  Select option: ").strip().lower()

        if choice == "q":
            print(f"\n{YELLOW}  👋  Goodbye!{RESET}\n")
            break

        elif choice == "1":
            _interactive_place_order(client)

        elif choice == "2":
            cmd_balance(args)

        elif choice == "3":
            _interactive_open_orders(client)

        elif choice == "4":
            _interactive_cancel_order(client)

        else:
            print(f"{RED}  ⚠  Unknown option. Please try again.{RESET}")


def _prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"  {label}{suffix}: ").strip()
    return val if val else (default or "")


def _interactive_place_order(client: BinanceFuturesClient) -> None:
    print(f"\n{CYAN}{'━'*50}{RESET}")
    print(f"{BOLD}  📝  PLACE ORDER{RESET}")
    print(f"{CYAN}{'━'*50}{RESET}")

    symbol     = _prompt("Symbol (e.g. BTCUSDT)", "BTCUSDT").upper()
    side       = _prompt("Side   [BUY/SELL]", "BUY").upper()
    order_type = _prompt("Type   [MARKET/LIMIT/STOP_MARKET]", "MARKET").upper()

    try:
        qty = float(_prompt("Quantity (e.g. 0.001)"))
    except ValueError:
        print(f"{RED}  ❌  Invalid quantity.{RESET}")
        return

    price = stop_price = None

    if order_type == "LIMIT":
        try:
            price = float(_prompt("Limit Price"))
        except ValueError:
            print(f"{RED}  ❌  Invalid price.{RESET}")
            return

    if order_type == "STOP_MARKET":
        try:
            stop_price = float(_prompt("Stop Price"))
        except ValueError:
            print(f"{RED}  ❌  Invalid stop price.{RESET}")
            return

    confirm = _prompt("Confirm order? [yes/no]", "yes").lower()
    if confirm not in {"yes", "y"}:
        print(f"{YELLOW}  Order cancelled.{RESET}")
        return

    try:
        place_order(
            client=client,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=qty,
            price=price,
            stop_price=stop_price,
        )
    except (ValueError, BinanceAPIError) as exc:
        logger.error("Interactive order error: %s", exc)


def _interactive_open_orders(client: BinanceFuturesClient) -> None:
    symbol = _prompt("Symbol (leave blank for all)", "").upper() or None
    try:
        orders = client.get_open_orders(symbol)
        if not orders:
            print(f"{YELLOW}  No open orders found.{RESET}")
            return
        print(f"\n{BOLD}  Open Orders ({len(orders)}){RESET}")
        for o in orders:
            print(f"  [{o['orderId']}] {o['symbol']} {o['side']} {o['type']} "
                  f"qty={o['origQty']} price={o.get('price','N/A')} status={o['status']}")
    except BinanceAPIError as exc:
        print(f"{RED}  ❌  {exc}{RESET}")


def _interactive_cancel_order(client: BinanceFuturesClient) -> None:
    symbol   = _prompt("Symbol", "BTCUSDT").upper()
    order_id_str = _prompt("Order ID")
    try:
        order_id = int(order_id_str)
        result = client.cancel_order(symbol, order_id)
        print(f"{GREEN}  ✅  Cancelled order {result.get('orderId')} — status: {result.get('status')}{RESET}")
        logger.info("Cancelled order %s for %s", order_id, symbol)
    except (ValueError, BinanceAPIError) as exc:
        print(f"{RED}  ❌  {exc}{RESET}")
        logger.error("Cancel order error: %s", exc)


# ── Argument parser ───────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """\
            ╔══════════════════════════════════════════╗
            ║  Binance Futures Testnet  —  Trading Bot  ║
            ╚══════════════════════════════════════════╝

            Examples:
              # Market buy
              python cli.py order --symbol BTCUSDT --side BUY --type MARKET --qty 0.001

              # Limit sell
              python cli.py order --symbol ETHUSDT --side SELL --type LIMIT --qty 0.01 --price 3200

              # Stop-Market
              python cli.py order --symbol BTCUSDT --side SELL --type STOP_MARKET --qty 0.001 --stop-price 58000

              # Interactive mode
              python cli.py interactive

              # Balance
              python cli.py balance
            """
        ),
    )

    # ── Global credential flags ────────────────────────────────────────
    parser.add_argument("--api-key",    dest="api_key",    default=None, help="Binance API key (overrides env var)")
    parser.add_argument("--api-secret", dest="api_secret", default=None, help="Binance API secret (overrides env var)")

    sub = parser.add_subparsers(dest="command", required=True)

    # ── order ──────────────────────────────────────────────────────────
    order_p = sub.add_parser("order", help="Place an order directly via CLI flags")
    order_p.add_argument("--symbol",      required=True,               help="Trading pair, e.g. BTCUSDT")
    order_p.add_argument("--side",        required=True,               help="BUY or SELL",               choices=["BUY","SELL","buy","sell"])
    order_p.add_argument("--type",        required=True,               help="MARKET | LIMIT | STOP_MARKET")
    order_p.add_argument("--qty",         required=True, type=float,   help="Order quantity")
    order_p.add_argument("--price",       type=float,    default=None, help="Limit price (LIMIT orders)")
    order_p.add_argument("--stop-price",  dest="stop_price", type=float, default=None, help="Stop price (STOP_MARKET orders)")
    order_p.add_argument("--reduce-only", dest="reduce_only", action="store_true", help="Reduce-only flag")
    order_p.set_defaults(func=cmd_order)

    # ── balance ────────────────────────────────────────────────────────
    bal_p = sub.add_parser("balance", help="Show account balances")
    bal_p.set_defaults(func=cmd_balance)

    # ── interactive ────────────────────────────────────────────────────
    int_p = sub.add_parser("interactive", help="Launch interactive menu")
    int_p.set_defaults(func=cmd_interactive)

    return parser


# ── Entry point ───────────────────────────────────────────────────────────

def main() -> None:
    print(BANNER)
    parser = build_parser()
    args   = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
