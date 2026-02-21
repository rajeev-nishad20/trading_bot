"""
Binance Futures Testnet REST client.
Wraps raw HTTP calls so the rest of the codebase stays exchange-agnostic.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import requests

from bot.logging_config import setup_logging

BASE_URL = "https://testnet.binancefuture.com"
logger = setup_logging()


class BinanceAPIError(Exception):
    """Raised when Binance returns a non-2xx response or an error payload."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[Binance {code}] {message}")


class BinanceFuturesClient:
    """
    Lightweight wrapper around Binance USDT-M Futures REST API.

    Parameters
    ----------
    api_key:    Testnet API key
    api_secret: Testnet API secret
    """

    def __init__(self, api_key: str, api_secret: str):
        self._api_key = api_key
        self._api_secret = api_secret
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.debug("BinanceFuturesClient initialised (testnet)")

    # ── Internal helpers ──────────────────────────────────────────────────

    def _sign(self, params: dict) -> dict:
        """Append HMAC-SHA256 signature to params dict."""
        params["timestamp"] = int(time.time() * 1000)
        query = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(self, method: str, endpoint: str, params: dict | None = None) -> Any:
        """
        Execute a signed request and return the parsed JSON response.

        Raises:
            BinanceAPIError: on API-level errors
            requests.RequestException: on network-level errors
        """
        url = f"{BASE_URL}{endpoint}"
        params = params or {}
        signed = self._sign(params)

        logger.debug("→ %s %s | params: %s", method.upper(), endpoint, {k: v for k, v in signed.items() if k != "signature"})

        try:
            if method.upper() == "GET":
                resp = self._session.get(url, params=signed, timeout=10)
            else:
                resp = self._session.post(url, data=signed, timeout=10)
        except requests.RequestException as exc:
            logger.error("Network error: %s", exc)
            raise

        logger.debug("← HTTP %s | body: %s", resp.status_code, resp.text[:500])

        try:
            data = resp.json()
        except ValueError:
            resp.raise_for_status()
            raise

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            raise BinanceAPIError(data["code"], data.get("msg", "Unknown error"))

        resp.raise_for_status()
        return data

    # ── Public API ────────────────────────────────────────────────────────

    def get_server_time(self) -> int:
        """Return Binance server timestamp (ms)."""
        data = self._request("GET", "/fapi/v1/time")
        return data["serverTime"]

    def get_exchange_info(self, symbol: str | None = None) -> dict:
        """Return exchange info, optionally filtered by symbol."""
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        return self._request("GET", "/fapi/v1/exchangeInfo", params)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        time_in_force: str = "GTC",
        stop_price: float | None = None,
        reduce_only: bool = False,
    ) -> dict:
        """
        Place a futures order on the testnet.

        Parameters
        ----------
        symbol       : Trading pair, e.g. BTCUSDT
        side         : BUY or SELL
        order_type   : MARKET | LIMIT | STOP_MARKET
        quantity     : Contract quantity
        price        : Required for LIMIT orders
        time_in_force: GTC (default) | IOC | FOK
        stop_price   : Required for STOP_MARKET orders
        reduce_only  : Whether this is a reduce-only order
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("price is required for LIMIT orders")
            params["price"] = price
            params["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            if stop_price is None:
                raise ValueError("stopPrice is required for STOP_MARKET orders")
            params["stopPrice"] = stop_price

        if reduce_only:
            params["reduceOnly"] = "true"

        logger.info(
            "Placing %s %s order | symbol=%s qty=%s price=%s",
            side,
            order_type,
            symbol,
            quantity,
            price or stop_price or "N/A",
        )

        return self._request("POST", "/fapi/v1/order", params)

    def get_open_orders(self, symbol: str | None = None) -> list:
        """Fetch all open orders, optionally filtered by symbol."""
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        return self._request("GET", "/fapi/v1/openOrders", params)

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel a specific order by orderId."""
        return self._request(
            "DELETE",
            "/fapi/v1/order",
            {"symbol": symbol.upper(), "orderId": order_id},
        )

    def get_account_balance(self) -> list:
        """Return futures wallet balances."""
        return self._request("GET", "/fapi/v2/balance", {})
