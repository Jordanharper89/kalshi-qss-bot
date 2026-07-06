import os
import time
from copy import deepcopy
from dotenv import load_dotenv

from services.position_service import position_service

load_dotenv()

POSITIONS_FILE = os.getenv("POSITIONS_FILE", "positions.json")


def _now():
    return int(time.time())


def _ticker(ticker):
    return str(ticker or "").strip().upper()


def _to_float(value, default=0.0):
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


def _normalize_price(value):
    price = _to_float(value, None)
    if price is None:
        return None
    if 0 < price <= 1:
        return round(price * 100, 4)
    return round(price, 4)


def get_all_positions():
    return position_service.all_positions()


def load_positions():
    return get_all_positions()


def save_positions(positions):
    if not isinstance(positions, dict):
        positions = {}
    position_service.save_positions(positions)
    return positions


def get_position(ticker):
    return position_service.get_position(ticker)


def position_exists(ticker):
    return get_position(ticker) is not None


def _extract_quantity(position):
    for key in ["contracts", "quantity", "count", "shares", "position", "remaining_contracts"]:
        if key in position:
            return _to_float(position.get(key), 0.0)
    return 0.0


def _extract_entry(position):
    for key in [
        "entry_price",
        "avg_entry_price",
        "average_entry_price",
        "avg_price",
        "average_price",
        "buy_price",
        "price",
        "entry",
        "cost_basis_price",
        "yes_avg_price",
        "no_avg_price",
    ]:
        if key in position:
            price = _normalize_price(position.get(key))
            if price is not None and price > 0:
                return price
    return None


def _auto_state_defaults():
    return {
        "tp1_fired": False,
        "tp2_fired": False,
        "tp3_fired": False,
        "stop_fired": False,
        "highest_price_cents": None,
        "breakeven_active": False,
    }


def _ensure_position_defaults(ticker, position):
    ticker = _ticker(ticker)
    position.setdefault("ticker", ticker)
    position.setdefault("side", str(position.get("side") or "YES").upper())
    position.setdefault("status", "open")
    position.setdefault("created_at", _now())
    position["updated_at"] = _now()

    if "auto_state" not in position or not isinstance(position.get("auto_state"), dict):
        position["auto_state"] = _auto_state_defaults()
    else:
        for key, value in _auto_state_defaults().items():
            position["auto_state"].setdefault(key, value)

    return position


def add_position(ticker, side="YES", amount=None, price=None, contracts=None, **kwargs):
    ticker = _ticker(ticker)
    if not ticker:
        return None

    positions = get_all_positions()
    existing = positions.get(ticker, {})
    if not isinstance(existing, dict):
        existing = {}

    side = str(kwargs.get("side", side) or existing.get("side") or "YES").upper()

    new_contracts = _to_float(
        kwargs.get("contracts", kwargs.get("quantity", kwargs.get("count", kwargs.get("shares", contracts)))),
        0.0,
    )
    old_contracts = _extract_quantity(existing)
    total_contracts = old_contracts + new_contracts if new_contracts else old_contracts

    new_price = _normalize_price(kwargs.get("entry_price", kwargs.get("avg_price", kwargs.get("price", price))))
    old_price = _extract_entry(existing)

    if new_price is not None and new_contracts and old_contracts and old_price:
        avg_price = ((old_price * old_contracts) + (new_price * new_contracts)) / (old_contracts + new_contracts)
    elif new_price is not None:
        avg_price = new_price
    else:
        avg_price = old_price

    position = deepcopy(existing)
    position.update(kwargs)
    position["ticker"] = ticker
    position["side"] = side
    position["status"] = "open"

    if amount is not None:
        position["amount"] = _to_float(amount, amount)

    if total_contracts:
        position["contracts"] = total_contracts
        position["remaining_contracts"] = total_contracts

    if avg_price is not None:
        position["entry_price"] = round(avg_price, 4)
        position["avg_entry_price"] = round(avg_price, 4)

    positions[ticker] = _ensure_position_defaults(ticker, position)
    save_positions(positions)
    return positions[ticker]


def update_position(ticker, **updates):
    ticker = _ticker(ticker)
    positions = get_all_positions()
    position = positions.get(ticker, {})
    if not isinstance(position, dict):
        position = {}

    position.update(updates)
    positions[ticker] = _ensure_position_defaults(ticker, position)
    save_positions(positions)
    return positions[ticker]


def set_position(ticker, position):
    ticker = _ticker(ticker)
    positions = get_all_positions()
    positions[ticker] = _ensure_position_defaults(ticker, dict(position or {}))
    save_positions(positions)
    return positions[ticker]


def remove_position(ticker):
    ticker = _ticker(ticker)
    positions = get_all_positions()
    removed = positions.pop(ticker, None)
    save_positions(positions)
    return removed


def delete_position(ticker):
    return remove_position(ticker)


def close_position(ticker, **updates):
    ticker = _ticker(ticker)
    positions = get_all_positions()
    position = positions.get(ticker)
    if not isinstance(position, dict):
        return None

    position.update(updates)
    position["status"] = "closed"
    position["closed_at"] = _now()
    position["updated_at"] = _now()
    positions[ticker] = position
    save_positions(positions)
    return position


def reduce_position(ticker, percent=None, contracts=None, **kwargs):
    ticker = _ticker(ticker)
    positions = get_all_positions()
    position = positions.get(ticker)
    if not isinstance(position, dict):
        return None

    current_qty = _extract_quantity(position)
    sell_qty = _to_float(contracts, None)

    if sell_qty is None:
        pct = _to_float(percent if percent is not None else kwargs.get("sell_pct", kwargs.get("percent")), 100.0)
        sell_qty = current_qty * (pct / 100.0) if current_qty else 0.0

    remaining = max(0.0, current_qty - sell_qty)

    position["contracts"] = remaining
    position["remaining_contracts"] = remaining
    position["updated_at"] = _now()

    if remaining <= 0:
        position["status"] = "closed"
        position["closed_at"] = _now()

    positions[ticker] = position
    save_positions(positions)
    return position


def record_sell(ticker, percent=None, contracts=None, **kwargs):
    return reduce_position(ticker, percent=percent, contracts=contracts, **kwargs)


def calculate_pnl(position_or_ticker, current_price=None):
    if isinstance(position_or_ticker, str):
        position = get_position(position_or_ticker) or {}
    elif isinstance(position_or_ticker, dict):
        position = position_or_ticker
    else:
        position = {}

    entry = _extract_entry(position)
    current = _normalize_price(current_price)

    if current is None:
        for key in ["current_price", "mark_price", "last_price", "last_trade_price"]:
            if key in position:
                current = _normalize_price(position.get(key))
                break

    if entry is None or current is None or entry <= 0:
        return {
            "entry_price": entry,
            "current_price": current,
            "pnl_pct": 0.0,
            "pnl_dollars": 0.0,
            "pnl_text": "N/A",
        }

    pnl_pct = ((current - entry) / entry) * 100.0
    qty = _extract_quantity(position)
    pnl_dollars = ((current - entry) / 100.0) * qty

    return {
        "entry_price": entry,
        "current_price": current,
        "pnl_pct": pnl_pct,
        "pnl_dollars": pnl_dollars,
        "pnl_text": f"{pnl_pct:+.2f}%",
    }


def reset_auto_state(ticker):
    ticker = _ticker(ticker)
    positions = get_all_positions()
    position = positions.get(ticker)
    if not isinstance(position, dict):
        return None

    position["auto_state"] = _auto_state_defaults()
    position["updated_at"] = _now()
    positions[ticker] = position
    save_positions(positions)
    return position


def list_open_positions():
    positions = get_all_positions()
    return {
        ticker: pos
        for ticker, pos in positions.items()
        if isinstance(pos, dict) and str(pos.get("status", "open")).lower() not in {"closed", "settled", "inactive", "done"}
    }


if __name__ == "__main__":
    positions = get_all_positions()
    print(f"Loaded {len(positions)} saved positions from {POSITIONS_FILE}")