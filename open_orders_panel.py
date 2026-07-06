import base64
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()

KALSHI_API_BASE = (
    os.getenv("KALSHI_API_BASE")
    or os.getenv("KALSHI_BASE_URL")
    or "https://api.elections.kalshi.com/trade-api/v2"
).rstrip("/")

KALSHI_API_KEY_ID = (
    os.getenv("KALSHI_API_KEY_ID")
    or os.getenv("KALSHI_ACCESS_KEY")
    or os.getenv("KALSHI_KEY_ID")
    or os.getenv("KALSHI_API_KEY")
)

KALSHI_PRIVATE_KEY_FILE = (
    os.getenv("KALSHI_PRIVATE_KEY_FILE")
    or os.getenv("KALSHI_PRIVATE_KEY_PATH")
    or os.getenv("KALSHI_KEY_FILE")
)

KALSHI_PRIVATE_KEY_TEXT = os.getenv("KALSHI_PRIVATE_KEY")
KALSHI_PASSPHRASE = os.getenv("KALSHI_PASSPHRASE")

ORDER_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_MAX_AGE_SECONDS = 900
PANEL_CACHE: Dict[str, Any] = {"key": None, "time": 0, "text": None, "keyboard": None}
PANEL_CACHE_SECONDS = 3


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        if isinstance(value, str):
            value = value.replace("$", "").replace("¢", "").replace("c", "").replace("%", "").strip()
            if value == "":
                return default
        return float(value)
    except Exception:
        return default


def _short_order_id(order_id: str) -> str:
    order_id = _safe_str(order_id, "UNKNOWN")
    if len(order_id) <= 12:
        return order_id
    return order_id[:6] + "..." + order_id[-4:]


def _clean_error(error: Exception) -> str:
    text = str(error)
    if "INCORRECT_API_KEY_SIGNATURE" in text:
        return "Kalshi API signature error. Check KALSHI_API_KEY_ID and private key file in .env."
    if "Missing Kalshi API key" in text:
        return "Missing Kalshi API key id. Check KALSHI_API_KEY_ID in .env."
    if "Missing Kalshi private key" in text:
        return "Missing Kalshi private key. Check KALSHI_PRIVATE_KEY_FILE in .env."
    return text


def _load_private_key():
    try:
        from cryptography.hazmat.primitives import serialization
    except Exception as e:
        raise RuntimeError("Missing cryptography package. Run: pip install cryptography") from e

    password = KALSHI_PASSPHRASE.encode("utf-8") if KALSHI_PASSPHRASE else None

    if KALSHI_PRIVATE_KEY_TEXT:
        key_text = KALSHI_PRIVATE_KEY_TEXT.replace("\\n", "\n").encode("utf-8")
        return serialization.load_pem_private_key(key_text, password=password)

    if KALSHI_PRIVATE_KEY_FILE:
        with open(KALSHI_PRIVATE_KEY_FILE, "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=password)

    raise RuntimeError("Missing Kalshi private key. Set KALSHI_PRIVATE_KEY_FILE or KALSHI_PRIVATE_KEY in .env.")


def _sign_message(message: str) -> str:
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
    except Exception as e:
        raise RuntimeError("Missing cryptography package. Run: pip install cryptography") from e

    private_key = _load_private_key()
    signature = private_key.sign(
        message.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def _auth_headers(method: str, path: str) -> Dict[str, str]:
    if not KALSHI_API_KEY_ID:
        raise RuntimeError("Missing Kalshi API key id. Set KALSHI_API_KEY_ID in .env.")

    timestamp = str(int(time.time() * 1000))
    method = method.upper()
    message = timestamp + method + path
    signature = _sign_message(message)

    return {
        "KALSHI-ACCESS-KEY": KALSHI_API_KEY_ID,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json",
    }


def _request(method: str, path: str, params: Optional[Dict[str, Any]] = None, json_body: Optional[Dict[str, Any]] = None):
    method = method.upper()
    headers = _auth_headers(method, path)
    url = KALSHI_API_BASE + path
    response = requests.request(method, url, headers=headers, params=params, json=json_body, timeout=12)
    if response.status_code >= 400:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(f"Kalshi API error {response.status_code}: {detail}")
    if not response.text.strip():
        return {}
    try:
        return response.json()
    except Exception:
        return {"raw": response.text}


def _extract_orders(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ["orders", "open_orders", "data", "results"]:
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]

    if isinstance(payload.get("order"), dict):
        return [payload["order"]]

    return []


def _order_ticker(order: Dict[str, Any]) -> str:
    for key in ["ticker", "market_ticker", "market", "market_id", "contract_ticker"]:
        value = order.get(key)
        if value:
            return _safe_str(value).upper()
    return "UNKNOWN"


def _order_id(order: Dict[str, Any]) -> str:
    for key in ["order_id", "id", "client_order_id", "client_id"]:
        value = order.get(key)
        if value:
            return _safe_str(value)
    return ""


def _order_status(order: Dict[str, Any]) -> str:
    for key in ["status", "state"]:
        value = order.get(key)
        if value:
            return _safe_str(value).upper()
    return "OPEN"


def _order_side(order: Dict[str, Any]) -> str:
    side = _safe_str(order.get("side") or order.get("action") or "").upper()
    contract_side = _safe_str(order.get("yes_no") or order.get("contract_side") or order.get("position_side") or "").upper()
    if contract_side in {"YES", "NO"} and side:
        return f"{side} {contract_side}"
    if contract_side in {"YES", "NO"}:
        return contract_side
    return side or "ORDER"


def _order_price(order: Dict[str, Any]) -> str:
    for key in ["yes_price", "no_price", "price", "limit_price", "limit_price_cents", "yes_price_dollars", "no_price_dollars"]:
        if key in order and order.get(key) is not None:
            price = _to_float(order.get(key))
            if price is None:
                continue
            if 0 < price <= 1:
                price *= 100
            return f"{price:g}c"
    return "N/A"


def _order_quantity(order: Dict[str, Any]) -> str:
    for key in ["remaining_count", "remaining_count_fp", "count", "quantity", "contracts", "remaining_contracts", "num_contracts"]:
        if key in order and order.get(key) is not None:
            return _safe_str(order.get(key))
    for key in ["amount", "notional", "dollar_amount"]:
        if key in order and order.get(key) is not None:
            value = _to_float(order.get(key))
            if value is not None:
                return f"${value:g}"
    return "N/A"


def _cache_order(order: Dict[str, Any]) -> str:
    order_id = _order_id(order)
    ticker = _order_ticker(order)
    token = uuid.uuid4().hex[:12]
    ORDER_CACHE[token] = {
        "order_id": order_id,
        "ticker": ticker,
        "created_at": time.time(),
        "order": order,
    }
    _clean_cache()
    return token


def _clean_cache() -> None:
    now = time.time()
    expired = [token for token, data in ORDER_CACHE.items() if now - data.get("created_at", 0) > CACHE_MAX_AGE_SECONDS]
    for token in expired:
        ORDER_CACHE.pop(token, None)


def get_open_orders(ticker: Optional[str] = None) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {"status": "open"}
    if ticker:
        params["ticker"] = ticker.upper()

    try:
        payload = _request("GET", "/portfolio/orders", params=params)
        orders = _extract_orders(payload)
    except Exception:
        payload = _request("GET", "/portfolio/orders")
        orders = _extract_orders(payload)

    open_statuses = {"OPEN", "RESTING", "UNFILLED", "PARTIALLY_FILLED", "PARTIAL_FILL", "PENDING"}
    filtered = []
    for order in orders:
        status = _order_status(order)
        if status and status not in open_statuses:
            continue
        if ticker and _order_ticker(order) != ticker.upper():
            continue
        filtered.append(order)

    return filtered


def orders_panel_text(ticker: Optional[str] = None) -> str:
    ticker = ticker.upper() if ticker else None

    try:
        orders = get_open_orders(ticker)
    except Exception as e:
        return f"""OPEN ORDERS PANEL

Status:
Could not load open orders.

Error:
{_clean_error(e)}

Check .env API key/private key settings, then refresh.""".strip()

    title = f"OPEN ORDERS - {ticker}" if ticker else "OPEN ORDERS PANEL"

    if not orders:
        scope = f" for {ticker}" if ticker else ""
        return f"""{title}

Status:
No active limit orders{scope}.

Use Manual Limit Order from a trade card to place one.""".strip()

    lines = [title, "", f"Active Orders: {len(orders)}", ""]

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for order in orders:
        grouped.setdefault(_order_ticker(order), []).append(order)

    for group_ticker, group_orders in grouped.items():
        lines.append(f"Ticker: {group_ticker}")
        for i, order in enumerate(group_orders, start=1):
            lines.append(f"{i}. {_order_side(order)} | Price: {_order_price(order)} | Qty: {_order_quantity(order)} | ID: {_short_order_id(_order_id(order))}")
        lines.append("")

    lines.append("Buttons below can cancel one order or cancel all orders for a ticker.")
    return "\n".join(lines).strip()


def orders_panel_keyboard(ticker: Optional[str] = None) -> Dict[str, Any]:
    ticker = ticker.upper() if ticker else None
    rows: List[List[Dict[str, str]]] = []

    try:
        orders = get_open_orders(ticker)
    except Exception:
        orders = []

    if ticker:
        rows.append([
            {"text": "Refresh", "callback_data": f"orders_refresh_ticker|{ticker}"},
            {"text": "All Orders", "callback_data": "orders_refresh"},
        ])
        if orders:
            rows.append([{"text": f"Cancel ALL {ticker}", "callback_data": f"cancel_all_ticker|{ticker}"}])
    else:
        rows.append([{"text": "Refresh Orders", "callback_data": "orders_refresh"}])

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for order in orders:
        grouped.setdefault(_order_ticker(order), []).append(order)

    if not ticker:
        tickers = sorted(grouped.keys())[:20]
        for group_ticker in tickers:
            rows.append([{"text": f"View {group_ticker} ({len(grouped[group_ticker])})", "callback_data": f"open_orders_ticker|{group_ticker}"}])
    else:
        for order in orders[:20]:
            token = _cache_order(order)
            label = f"Cancel {_short_order_id(_order_id(order))} | {_order_price(order)}"
            rows.append([{"text": label[:60], "callback_data": f"cancel_order|{token}"}])

    rows.append([{"text": "Back To Main Menu", "callback_data": "main_menu"}])
    return {"inline_keyboard": rows}


def _orders_panel_text_from_orders(ticker: Optional[str], orders: List[Dict[str, Any]], error: Optional[Exception] = None) -> str:
    ticker = ticker.upper() if ticker else None
    title = f"OPEN ORDERS - {ticker}" if ticker else "OPEN ORDERS PANEL"

    if error:
        return f"""OPEN ORDERS PANEL

Status:
Could not load open orders.

Error:
{_clean_error(error)}

Check .env API key/private key settings, then refresh.""".strip()

    if not orders:
        scope = f" for {ticker}" if ticker else ""
        return f"""{title}

Status:
No active limit orders{scope}.

Use Manual Limit Order from a trade card to place one.""".strip()

    lines = [title, "", f"Active Orders: {len(orders)}", ""]

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for order in orders:
        grouped.setdefault(_order_ticker(order), []).append(order)

    for group_ticker, group_orders in grouped.items():
        lines.append(f"Ticker: {group_ticker}")
        for i, order in enumerate(group_orders, start=1):
            lines.append(f"{i}. {_order_side(order)} | Price: {_order_price(order)} | Qty: {_order_quantity(order)} | ID: {_short_order_id(_order_id(order))}")
        lines.append("")

    lines.append("Buttons below can cancel one order or cancel all orders for a ticker.")
    return "\n".join(lines).strip()


def _orders_panel_keyboard_from_orders(ticker: Optional[str], orders: List[Dict[str, Any]]) -> Dict[str, Any]:
    ticker = ticker.upper() if ticker else None
    rows: List[List[Dict[str, str]]] = []

    if ticker:
        rows.append([
            {"text": "Refresh", "callback_data": f"orders_refresh_ticker|{ticker}"},
            {"text": "All Orders", "callback_data": "orders_refresh"},
        ])
        if orders:
            rows.append([{"text": f"Cancel ALL {ticker}", "callback_data": f"cancel_all_ticker|{ticker}"}])
    else:
        rows.append([{"text": "Refresh Orders", "callback_data": "orders_refresh"}])

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for order in orders:
        grouped.setdefault(_order_ticker(order), []).append(order)

    if not ticker:
        for group_ticker in sorted(grouped.keys())[:20]:
            rows.append([{"text": f"View {group_ticker} ({len(grouped[group_ticker])})", "callback_data": f"open_orders_ticker|{group_ticker}"}])
    else:
        for order in orders[:20]:
            token = _cache_order(order)
            label = f"Cancel {_short_order_id(_order_id(order))} | {_order_price(order)}"
            rows.append([{"text": label[:60], "callback_data": f"cancel_order|{token}"}])

    rows.append([{"text": "Back To Main Menu", "callback_data": "main_menu"}])
    return {"inline_keyboard": rows}


def build_orders_panel(ticker: Optional[str] = None, force_refresh: bool = False) -> Tuple[str, Dict[str, Any]]:
    """Fast panel builder. Gets orders once, then builds both text and keyboard from the same data."""
    key = (ticker or "ALL").upper()
    now = time.time()

    if not force_refresh and PANEL_CACHE.get("key") == key and now - PANEL_CACHE.get("time", 0) < PANEL_CACHE_SECONDS:
        return PANEL_CACHE["text"], PANEL_CACHE["keyboard"]

    try:
        orders = get_open_orders(ticker)
        text = _orders_panel_text_from_orders(ticker, orders)
        keyboard = _orders_panel_keyboard_from_orders(ticker, orders)
    except Exception as e:
        text = _orders_panel_text_from_orders(ticker, [], error=e)
        keyboard = _orders_panel_keyboard_from_orders(ticker, [])

    PANEL_CACHE.update({"key": key, "time": now, "text": text, "keyboard": keyboard})
    return text, keyboard


def cancel_order(order_id: str) -> Dict[str, Any]:
    if not order_id:
        raise RuntimeError("Missing order id.")

    # Try the newer endpoint first, then the older event-order endpoint if needed.
    try:
        return _request("DELETE", f"/portfolio/orders/{order_id}")
    except Exception:
        return _request("DELETE", f"/portfolio/events/orders/{order_id}")


def cancel_order_by_token(token: str) -> Dict[str, Any]:
    _clean_cache()
    cached = ORDER_CACHE.get(token)
    if not cached:
        return {
            "ok": False,
            "ticker": None,
            "message": "CANCEL ORDER FAILED\n\nReason:\nThat order button expired. Refresh the orders panel and press cancel again.",
        }

    order_id = cached.get("order_id")
    ticker = cached.get("ticker")

    try:
        response = cancel_order(order_id)
        PANEL_CACHE["key"] = None
        return {
            "ok": True,
            "ticker": ticker,
            "response": response,
            "message": f"""ORDER CANCELED

Ticker:
{ticker}

Order ID:
{order_id}

Status:
Cancel request accepted by Kalshi.""".strip(),
        }
    except Exception as e:
        return {
            "ok": False,
            "ticker": ticker,
            "message": f"""CANCEL ORDER FAILED

Ticker:
{ticker}

Order ID:
{order_id}

Error:
{_clean_error(e)}""".strip(),
        }


def cancel_all_orders_for_ticker(ticker: str) -> Dict[str, Any]:
    ticker = ticker.upper()

    try:
        orders = get_open_orders(ticker)
    except Exception as e:
        return {
            "ok": False,
            "ticker": ticker,
            "message": f"""CANCEL ALL FAILED

Ticker:
{ticker}

Error loading orders:
{_clean_error(e)}""".strip(),
        }

    if not orders:
        return {
            "ok": True,
            "ticker": ticker,
            "message": f"""CANCEL ALL COMPLETE

Ticker:
{ticker}

Status:
No active orders found.""".strip(),
        }

    canceled = 0
    failed = []

    for order in orders:
        order_id = _order_id(order)
        try:
            cancel_order(order_id)
            canceled += 1
        except Exception as e:
            failed.append(f"{_short_order_id(order_id)}: {_clean_error(e)}")

    PANEL_CACHE["key"] = None

    if failed:
        return {
            "ok": False,
            "ticker": ticker,
            "message": f"""CANCEL ALL PARTIAL

Ticker:
{ticker}

Canceled:
{canceled}

Failed:
{len(failed)}

Details:
{chr(10).join(failed[:5])}""".strip(),
        }

    return {
        "ok": True,
        "ticker": ticker,
        "message": f"""CANCEL ALL COMPLETE

Ticker:
{ticker}

Canceled Orders:
{canceled}

Status:
All active orders for this ticker were sent for cancel.""".strip(),
    }


if __name__ == "__main__":
    print(orders_panel_text())
