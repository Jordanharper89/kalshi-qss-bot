import json
import math
import time
import uuid
import requests

from kalshi_auth import sign_request, KALSHI_BASE_URL
from order_preview import get_market, get_buy_price, get_sell_price, clear_market_cache
from trade_settings import load_settings
from position_manager import (
    add_position,
    get_position,
    get_all_positions,
    save_positions,
    delete_position,
)

REQUEST_TIMEOUT_SECONDS = 8
ORDER_TIMEOUT_SECONDS = 10
ORDER_LOCK_SECONDS = 12
ORDER_LOCKS = {}


class DuplicateOrderResponse:
    status_code = 409
    text = "Duplicate order blocked: another matching order is already being submitted."

    def json(self):
        return {"error": self.text}


def _clean_locks():
    now = time.time()
    expired = [key for key, ts in ORDER_LOCKS.items() if now - ts > ORDER_LOCK_SECONDS]
    for key in expired:
        ORDER_LOCKS.pop(key, None)


def _acquire_order_lock(key):
    _clean_locks()
    if key in ORDER_LOCKS:
        return False
    ORDER_LOCKS[key] = time.time()
    return True


def _release_order_lock(key):
    ORDER_LOCKS.pop(key, None)


def clean_api_error(text):
    text = str(text or "")
    if "INCORRECT_API_KEY_SIGNATURE" in text:
        return "KALSHI SIGNATURE ERROR - check API key ID and private key file in .env."
    if len(text) > 1200:
        return text[:1200] + "\n...error shortened..."
    return text



def dollars(price_cents):
    return f"{float(price_cents) / 100:.4f}"


def cents_from_dollars(value):
    if value is None:
        return None
    value = float(value)
    if value <= 1:
        value *= 100
    return round(value, 1)


def money(value):
    try:
        return f"${float(value):.2f}"
    except Exception:
        return "$0.00"


def kalshi_request(method, endpoint_path, payload=None, params=None, timeout=None):
    headers = sign_request(method, endpoint_path)
    headers["Content-Type"] = "application/json"
    url = KALSHI_BASE_URL + endpoint_path
    timeout = timeout or REQUEST_TIMEOUT_SECONDS

    if method == "GET":
        return requests.get(url, headers=headers, params=params, timeout=timeout)

    if method == "POST":
        return requests.post(url, headers=headers, json=payload, timeout=timeout or ORDER_TIMEOUT_SECONDS)

    if method == "DELETE":
        return requests.delete(url, headers=headers, json=payload, timeout=timeout)

    raise ValueError("Unsupported method")


def contracts_from_amount(amount, price_cents):
    return math.floor(float(amount) / (float(price_cents) / 100))


def calc_cost(contracts, price_cents):
    return round(float(contracts) * float(price_cents) / 100, 2)


def create_order(ticker, book_side, count, yes_side_price, tif="immediate_or_cancel", reduce_only=False):
    ticker = str(ticker).upper().strip()
    count = float(count)
    yes_side_price = float(yes_side_price)
    lock_key = f"{ticker}|{book_side}|{count:.2f}|{yes_side_price:.4f}|{tif}|{reduce_only}"

    if not _acquire_order_lock(lock_key):
        return DuplicateOrderResponse()

    payload = {
        "ticker": ticker,
        "client_order_id": str(uuid.uuid4()),
        "side": book_side,
        "count": f"{count:.2f}",
        "price": dollars(yes_side_price),
        "time_in_force": tif,
        "self_trade_prevention_type": "taker_at_cross",
        "post_only": False,
        "cancel_order_on_pause": True,
        "reduce_only": reduce_only,
        "exchange_index": 0,
    }

    try:
        return kalshi_request("POST", "/portfolio/events/orders", payload, timeout=ORDER_TIMEOUT_SECONDS)
    finally:
        _release_order_lock(lock_key)


def place_advanced_strategy_orders(ticker, side, entry_price, contracts, settings):
    """
    KQ-017.2 Advanced Orders Repair.

    Older builds tried to immediately place TP/STOP resting orders after a buy.
    Kalshi rejected those with 400 errors on some markets/order payloads.

    New behavior:
    - Do NOT place TP/STOP/BUY_DIP orders immediately.
    - Save/arm strategy on the local position.
    - position_monitor.py executes TP / Buy Dip / Stop only when triggers hit.
    """
    ticker = str(ticker).upper().strip()
    side = str(side).upper().strip()
    contracts = int(float(contracts or 0))

    if contracts <= 0:
        return "Advanced Strategy skipped: no filled contracts."

    try:
        from strategy_manager import get_strategy, save_strategy, normalize_strategy
    except Exception:
        return "Advanced Strategy: saved settings on position; monitor will manage triggers."

    try:
        strategy = get_strategy(ticker)
        strategy = normalize_strategy(strategy)
        strategy["enabled"] = True
        strategy["armed"] = True
        strategy["entry_price"] = float(entry_price)
        strategy["side"] = side
        strategy["contracts_at_arm"] = contracts
        save_strategy(ticker, strategy)

        return """ARMED BY MONITOR

TP / Buy Dip / Stop orders will NOT be placed immediately.

The position monitor will execute them only when each trigger percentage is hit.

This avoids Kalshi 400 errors from unsupported immediate advanced order payloads.""".strip()

    except Exception as e:
        return f"Advanced Strategy arm warning: {e}"
def place_live_buy_amount(ticker, side, amount):
    ticker = str(ticker).upper().strip()
    side = str(side).upper().strip()
    amount = float(amount)

    settings = load_settings()
    market = get_market(ticker)

    if not market:
        return f"LIVE BUY ERROR\nTicker not found: {ticker}"

    price = get_buy_price(market, side)

    if price is None or price <= 0:
        return f"LIVE BUY ERROR\nNo valid BUY {side} price found."

    contracts = contracts_from_amount(amount, price)

    if contracts <= 0:
        return f"""
LIVE BUY ERROR

Amount:
{money(amount)}

Price:
{price}c

Contracts:
0

Reason:
Buy amount is too small for this price.
""".strip()

    if side == "YES":
        book_side = "bid"
        yes_side_price = price
    else:
        book_side = "ask"
        yes_side_price = round(100 - price, 1)

    response = create_order(
        ticker=ticker,
        book_side=book_side,
        count=contracts,
        yes_side_price=yes_side_price,
        tif="immediate_or_cancel",
        reduce_only=False,
    )

    if response.status_code not in [200, 201]:
        return f"""
LIVE BUY FAILED

Status:
{response.status_code}

Response:
{clean_api_error(response.text)}
""".strip()

    data = response.json()
    fill_count = float(data.get("fill_count", "0") or 0)
    remaining_count = float(data.get("remaining_count", "0") or 0)
    avg_fill = data.get("average_fill_price")

    if avg_fill:
        entry_price = round(float(avg_fill) * 100, 1)
        if side == "NO":
            entry_price = round(100 - entry_price, 1)
    else:
        entry_price = price

    actual_cost = calc_cost(fill_count, entry_price)
    unused_cash = round(amount - actual_cost, 2)

    if fill_count > 0:
        existing = get_position(ticker)

        if existing:
            positions = get_all_positions()
            old_contracts = float(existing.get("remaining_contracts", existing.get("contracts", 0)))
            old_entry = float(existing.get("entry_price", entry_price))
            new_contracts = old_contracts + fill_count

            avg_entry = round(((old_contracts * old_entry) + (fill_count * entry_price)) / new_contracts, 1)

            positions[ticker]["entry_price"] = avg_entry
            positions[ticker]["contracts"] = int(new_contracts)
            positions[ticker]["remaining_contracts"] = int(new_contracts)
            positions[ticker]["buy_amount"] = float(existing.get("buy_amount", 0)) + actual_cost
            positions[ticker]["advanced_strategy"] = existing.get("advanced_strategy", settings.get("advanced_strategy", False))
            positions[ticker]["settings"] = settings
            save_positions(positions)

        else:
            add_position(
                ticker=ticker,
                side=side,
                entry_price=entry_price,
                buy_amount=actual_cost,
                contracts=int(fill_count),
                advanced_strategy=settings.get("advanced_strategy", False),
                settings=settings,
            )

    advanced_result = ""

    if fill_count > 0 and settings.get("advanced_strategy"):
        advanced_result = place_advanced_strategy_orders(
            ticker=ticker,
            side=side,
            entry_price=entry_price,
            contracts=int(fill_count),
            settings=settings,
        )

    if fill_count <= 0:
        return f"""
LIVE BUY SUBMITTED

Ticker:
{ticker}

Side:
BUY {side}

Limit:
{price}c

Requested:
{contracts} contract(s)

Filled:
0

Remaining:
{remaining_count}

Status:
ORDER SENT BUT NOT FILLED
""".strip()

    return f"""
POSITION CARD

Ticker:
{ticker}

Side:
{side}

Entry:
{entry_price}c

Filled:
{fill_count} contract(s)

Buy Preset:
{money(amount)}

Actual Cost:
{money(actual_cost)}

Unused Cash:
{money(unused_cash)}

Advanced Strategy:
{"ON" if settings.get("advanced_strategy") else "OFF"}

Status:
POSITION CREATED

Advanced Strategy Status:
{advanced_result if advanced_result else "OFF"}
""".strip()


def place_live_buy(ticker, side):
    settings = load_settings()
    return place_live_buy_amount(ticker, side, settings.get("default_buy_amount", 10))


def build_confirm_preview(ticker, side):
    ticker = str(ticker).upper().strip()
    side = str(side).upper().strip()

    settings = load_settings()
    market = get_market(ticker)

    if not market:
        return f"CONFIRM ERROR\nTicker not found: {ticker}"

    price = get_buy_price(market, side)

    if price is None or price <= 0:
        return f"CONFIRM ERROR\nNo valid BUY {side} price found."

    buy_amount = float(settings.get("default_buy_amount", 10))
    contracts = contracts_from_amount(buy_amount, price)
    estimated_cost = calc_cost(contracts, price)
    unused_cash = round(buy_amount - estimated_cost, 2)

    if contracts <= 0:
        return f"CONFIRM ERROR\nBuy amount too small.\nAmount: {money(buy_amount)}\nPrice: {price}c"

    return f"""
ORDER PREVIEW

Ticker:
{ticker}

Market:
{market.get("title")}

Side:
BUY {side}

Buy Amount:
{money(buy_amount)}

Limit Price:
{price}c

Estimated Contracts:
{contracts}

Estimated Cost:
{money(estimated_cost)}

Unused Cash:
{money(unused_cash)}

Advanced Strategy:
{"ON" if settings.get("advanced_strategy") else "OFF"}
""".strip()


def place_sell_percent(ticker, percent):
    ticker = str(ticker).upper().strip()
    percent = float(percent)

    position = get_position(ticker)

    if not position:
        return f"SELL ERROR\nNo local position found for {ticker}"

    side = position["side"]
    remaining = int(position.get("remaining_contracts", position.get("contracts", 0)))

    if remaining <= 0:
        return f"SELL ERROR\nNo remaining contracts for {ticker}"

    sell_count = math.floor(remaining * (percent / 100))

    if percent >= 100:
        sell_count = remaining

    if sell_count <= 0:
        sell_count = 1

    market = get_market(ticker)

    if not market:
        return f"SELL ERROR\nTicker not found: {ticker}"

    exit_price = get_sell_price(market, side)

    if exit_price is None or exit_price <= 0:
        return f"SELL ERROR\nCould not find valid SELL {side} price."

    if side == "YES":
        book_side = "ask"
        yes_side_price = exit_price
    else:
        book_side = "bid"
        yes_side_price = round(100 - exit_price, 1)

    response = create_order(
        ticker=ticker,
        book_side=book_side,
        count=sell_count,
        yes_side_price=yes_side_price,
        tif="immediate_or_cancel",
        reduce_only=True,
    )

    if response.status_code not in [200, 201]:
        return f"""
SELL FAILED

Status:
{response.status_code}

Response:
{clean_api_error(response.text)}
""".strip()

    data = response.json()
    filled = float(data.get("fill_count", "0") or 0)

    entry = float(position["entry_price"])
    cost_basis = calc_cost(filled, entry)
    return_value = calc_cost(filled, exit_price)
    pnl_dollars = round(return_value - cost_basis, 2)
    pnl_percent = round(((exit_price - entry) / entry) * 100, 2) if entry else 0

    if filled <= 0:
        return f"""
SELL SUBMITTED

Ticker:
{ticker}

Side:
SELL {side}

Requested:
{sell_count}

Filled:
0

Status:
ORDER SENT BUT NOT FILLED
""".strip()

    positions = get_all_positions()
    new_remaining = remaining - int(filled)

    if ticker in positions:
        if new_remaining <= 0 or percent >= 100:
            delete_position(ticker)

            return f"""
PNL CARD

Ticker:
{ticker}

Result:
{"WIN" if pnl_dollars >= 0 else "LOSS"}

Side:
{side}

Entry:
{entry}c

Exit:
{exit_price}c

Contracts Sold:
{filled}

Cost:
{money(cost_basis)}

Return:
{money(return_value)}

Profit:
{money(pnl_dollars)}

PnL:
{pnl_percent}%

Position:
CLOSED
""".strip()

        positions[ticker]["remaining_contracts"] = int(new_remaining)
        save_positions(positions)

    updated_pos = get_position(ticker)
    remaining_after = 0

    if updated_pos:
        remaining_after = updated_pos.get("remaining_contracts", updated_pos.get("contracts", 0))

    return f"""
POSITION UPDATED

Ticker:
{ticker}

Side:
{side}

Sold:
{filled} contract(s)

Remaining:
{remaining_after} contract(s)

Entry:
{entry}c

Exit:
{exit_price}c

Cost Basis:
{money(cost_basis)}

Return:
{money(return_value)}

Realized PnL:
{money(pnl_dollars)}

PnL:
{pnl_percent}%

Status:
POSITION STILL OPEN
""".strip()



def _is_percent_token(value):
    return str(value or "").strip().upper().startswith("PCT:")


def _percent_value(value):
    raw = str(value or "").strip()
    if raw.upper().startswith("PCT:"):
        return float(raw.split(":", 1)[1])
    return None


def _clamp_price(price):
    return round(max(1.0, min(99.0, float(price))), 1)


def _position_entry_price(ticker):
    position = get_position(ticker)
    if not position:
        return None
    try:
        entry = float(position.get("entry_price", 0))
        return entry if entry > 0 else None
    except Exception:
        return None


def resolve_percent_limit_price(ticker, side, order_type, price_or_trigger):
    """
    Converts percent triggers into a contract-side limit price in cents.

    BUY_DIP:
        PCT:-10 means buy if the selected side price drops 10% from current market buy price.

    TAKE_PROFIT:
        PCT:25 means sell if selected side price rises 25% from saved entry.

    STOP_LOSS:
        PCT:-20 means sell if selected side price drops 20% from saved entry.
    """
    ticker = str(ticker).upper().strip()
    side = str(side).upper().strip()
    order_type = str(order_type).upper().strip()

    if not _is_percent_token(price_or_trigger):
        return float(price_or_trigger), None

    trigger_pct = _percent_value(price_or_trigger)

    if order_type == "BUY_DIP":
        market = get_market(ticker, force_refresh=True)
        if not market:
            raise ValueError(f"Ticker not found: {ticker}")

        base_price = get_buy_price(market, side)
        if base_price is None or base_price <= 0:
            raise ValueError(f"No valid current BUY {side} price found for {ticker}")

        limit_price = _clamp_price(float(base_price) * (1.0 + trigger_pct / 100.0))

        return limit_price, {
            "trigger_pct": trigger_pct,
            "base_price": base_price,
            "basis": "current market buy price",
        }

    if order_type in ["TAKE_PROFIT", "STOP_LOSS"]:
        base_price = _position_entry_price(ticker)
        if base_price is None:
            raise ValueError(f"No saved entry price found for {ticker}")

        limit_price = _clamp_price(float(base_price) * (1.0 + trigger_pct / 100.0))

        return limit_price, {
            "trigger_pct": trigger_pct,
            "base_price": base_price,
            "basis": "saved position entry price",
        }

    raise ValueError(f"Unsupported percent limit order type: {order_type}")


def _fmt_trigger_meta(meta):
    if not meta:
        return ""

    trigger = meta.get("trigger_pct")
    sign = "+" if trigger and trigger > 0 else ""

    return f"""

Trigger:
{sign}{trigger:g}%

Basis:
{meta.get("basis")}

Base Price:
{meta.get("base_price")}c""".rstrip()


def place_limit_order(ticker, source, side, order_type, price, amount):
    ticker = str(ticker).upper().strip()
    side = str(side).upper().strip()
    order_type = str(order_type).upper().strip()

    try:
        price, trigger_meta = resolve_percent_limit_price(ticker, side, order_type, price)
    except Exception as e:
        return f"LIMIT ORDER ERROR\n{e}"

    if price <= 0 or price >= 100:
        return "LIMIT ORDER ERROR\nPrice must be between 1c and 99c."

    trigger_details = _fmt_trigger_meta(trigger_meta)

    if order_type == "BUY_DIP":
        buy_amount = float(amount)
        contracts = contracts_from_amount(buy_amount, price)

        if contracts <= 0:
            return f"LIMIT ORDER ERROR\nAmount too small.\nAmount: {money(buy_amount)}\nPrice: {price}c"

        if side == "YES":
            book_side = "bid"
            yes_side_price = price
        else:
            book_side = "ask"
            yes_side_price = round(100 - price, 1)

        reduce_only = False
        label = "BUY DIP LIMIT"
        amount_label = f"Buy Amount:\n{money(buy_amount)}"

    elif order_type in ["TAKE_PROFIT", "STOP_LOSS"]:
        sell_pct = float(amount)
        if sell_pct <= 0:
            return "LIMIT ORDER ERROR\nSell percent must be above 0%."
        if sell_pct > 100:
            sell_pct = 100.0

        position = get_position(ticker)

        if not position:
            return f"LIMIT ORDER ERROR\nNo local position found for {ticker}"

        remaining = int(float(position.get("remaining_contracts", position.get("contracts", 0))))

        if remaining <= 0:
            return f"LIMIT ORDER ERROR\nNo remaining contracts for {ticker}"

        contracts = math.floor(remaining * (sell_pct / 100.0))
        if sell_pct >= 100:
            contracts = remaining
        if contracts <= 0:
            contracts = 1

        if side == "YES":
            book_side = "ask"
            yes_side_price = price
        else:
            book_side = "bid"
            yes_side_price = round(100 - price, 1)

        reduce_only = True
        label = "TAKE PROFIT LIMIT" if order_type == "TAKE_PROFIT" else "STOP LOSS LIMIT"
        amount_label = f"Sell Percent:\n{sell_pct:g}%\n\nContracts To Sell:\n{contracts} of {remaining}"

    else:
        return f"LIMIT ORDER ERROR\nUnknown type: {order_type}"

    response = create_order(
        ticker=ticker,
        book_side=book_side,
        count=contracts,
        yes_side_price=yes_side_price,
        tif="good_till_canceled",
        reduce_only=reduce_only,
    )

    if response.status_code not in [200, 201]:
        return f"""
LIMIT ORDER FAILED

Status:
{response.status_code}

Response:
{clean_api_error(response.text)}
""".strip()

    data = response.json()

    return f"""
LIMIT ORDER PLACED

Type:
{label}

Ticker:
{ticker}

Side:
{side}

Limit:
{price}c{trigger_details}

{amount_label}

Order ID:
{data.get("order_id")}

Remaining:
{data.get("remaining_count")}

Status:
OPEN / RESTING
""".strip()


def list_orders(ticker=None):
    params = {
        "status": "resting",
        "limit": 100,
    }

    if ticker:
        params["ticker"] = ticker

    response = kalshi_request("GET", "/portfolio/orders", params=params)

    if response.status_code != 200:
        return f"""
OPEN LIMIT ORDERS ERROR

Status:
{response.status_code}

Response:
{clean_api_error(response.text)}
""".strip()

    orders = response.json().get("orders", [])

    if not orders:
        if ticker:
            return f"""
OPEN LIMIT ORDERS

Ticker:
{ticker}

No open limit orders found.
""".strip()

        return """
OPEN LIMIT ORDERS

No open limit orders found.
""".strip()

    lines = ["OPEN LIMIT ORDERS", ""]

    for i, order in enumerate(orders, start=1):
        yes_price = order.get("yes_price_dollars")
        no_price = order.get("no_price_dollars")
        price = cents_from_dollars(yes_price or no_price)

        lines.append(f"{i}. {order.get('ticker')}")
        lines.append(f"Order ID: {order.get('order_id')}")
        lines.append(f"Price: {price}c")
        lines.append(f"Initial: {order.get('initial_count_fp')}")
        lines.append(f"Remaining: {order.get('remaining_count_fp')}")
        lines.append("-" * 30)

    return "\n".join(lines)


def cancel_order(order_id):
    order_id = str(order_id).strip()

    response = kalshi_request("DELETE", f"/portfolio/events/orders/{order_id}")

    if response.status_code not in [200, 201]:
        return f"""
CANCEL ORDER FAILED

Order ID:
{order_id}

Status:
{response.status_code}

Response:
{clean_api_error(response.text)}
""".strip()

    data = response.json()

    return f"""
ORDER CANCELED

Order ID:
{data.get("order_id", order_id)}

Reduced By:
{data.get("reduced_by")}

Status:
CANCELED
""".strip()


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("python kalshi_orders.py buy_amount TICKER YES 5")
        print("python kalshi_orders.py sell_percent TICKER 100")
        print("python kalshi_orders.py limit TICKER scan YES BUY_DIP PCT:-10 5")
        print("python kalshi_orders.py orders")
        print("python kalshi_orders.py cancel ORDER_ID")
        return

    mode = sys.argv[1].lower()

    if mode == "preview":
        print(build_confirm_preview(sys.argv[2], sys.argv[3]))
        return

    if mode == "buy":
        print(place_live_buy(sys.argv[2], sys.argv[3]))
        return

    if mode == "buy_amount":
        print(place_live_buy_amount(sys.argv[2], sys.argv[3], sys.argv[4]))
        return

    if mode == "sell_percent":
        print(place_sell_percent(sys.argv[2], sys.argv[3]))
        return

    if mode == "limit":
        print(place_limit_order(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7]))
        return

    if mode == "orders":
        ticker = sys.argv[2] if len(sys.argv) >= 3 else None
        print(list_orders(ticker))
        return

    if mode == "cancel":
        print(cancel_order(sys.argv[2]))
        return

    print("Unknown mode")


if __name__ == "__main__":
    main()