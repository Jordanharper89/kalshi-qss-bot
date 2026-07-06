from services.position_service import position_service
from trade_settings import load_settings


def money(value):
    try:
        return f"${float(value):.2f}"
    except Exception:
        return "$0.00"


def fmt_num(value):
    try:
        return round(float(value), 2)
    except Exception:
        return 0


def get_all_positions():
    return position_service.all_positions()


def get_position(ticker):
    return position_service.get_position(ticker)


def calculate_pnl(pos, current_price=None):
    if not pos:
        return {
            "entry_price": 0,
            "current_price": 0,
            "change_pct": 0,
            "unrealized_pnl": 0,
        }

    entry_price = pos.get("entry_price") or pos.get("avg_price") or 0
    qty = pos.get("contracts") or pos.get("quantity") or pos.get("count") or 0

    if current_price is None:
        current_price = pos.get("current_price")

    try:
        entry_price = float(entry_price)
        current_price = float(current_price or 0)
        qty = float(qty or 0)

        change_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price else 0
        unrealized_pnl = ((current_price - entry_price) / 100) * qty

        return {
            "entry_price": entry_price,
            "current_price": current_price,
            "change_pct": round(change_pct, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
        }

    except Exception:
        return {
            "entry_price": entry_price,
            "current_price": current_price,
            "change_pct": 0,
            "unrealized_pnl": 0,
        }


def position_list_text():
    positions = get_all_positions()

    if not positions:
        return """
POSITIONS

No open positions found.
""".strip()

    lines = ["POSITIONS", ""]

    for pos in positions.values():
        ticker = pos.get("ticker") or "UNKNOWN"
        side = pos.get("side") or "YES"
        qty = pos.get("contracts") or pos.get("quantity") or pos.get("count") or 0
        entry = pos.get("entry_price") or pos.get("avg_price") or 0
        current = pos.get("current_price")
        change = pos.get("change_pct")

        lines.append(f"{ticker}")
        lines.append(f"Side: {side} | Contracts: {qty}")
        lines.append(f"Entry: {entry}c | Current: {current if current is not None else 'n/a'}c")
        lines.append(f"Change: {change if change is not None else 'n/a'}%")
        lines.append("")

    return "\n".join(lines).strip()


def position_list_keyboard():
    positions = get_all_positions()
    buttons = []

    for pos in positions.values():
        ticker = pos.get("ticker")
        if not ticker:
            continue

        buttons.append(
            [
                {
                    "text": ticker[:32],
                    "callback_data": f"view_position|{ticker}",
                }
            ]
        )

    buttons.append([{"text": "Back", "callback_data": "main_menu"}])

    return {"inline_keyboard": buttons}


def position_card_text(ticker, current_price=None):
    ticker = str(ticker).upper().strip()

    position_service.refresh_position(ticker)
    pos = get_position(ticker)

    if not pos:
        return f"""
POSITION CARD

Ticker:
{ticker}

Position not found.
""".strip()

    side = pos.get("side", "YES")
    qty = pos.get("contracts") or pos.get("quantity") or pos.get("count") or 0
    entry = pos.get("entry_price") or pos.get("avg_price") or 0

    if current_price is None:
        current_price = pos.get("current_price")

    pnl = calculate_pnl(pos, current_price=current_price)

    return f"""
POSITION CARD

Ticker:
{ticker}

Side:
{side}

Contracts:
{qty}

Entry:
{fmt_num(entry)}c

Current:
{fmt_num(pnl.get("current_price"))}c

Change:
{fmt_num(pnl.get("change_pct"))}%

Unrealized P/L:
{money(pnl.get("unrealized_pnl"))}
""".strip()


def position_card_keyboard(ticker):
    ticker = str(ticker).upper().strip()

    settings = load_settings()
    advanced = "ON" if settings.get("advanced_strategy") else "OFF"

    return {
        "inline_keyboard": [
            [
                {"text": "Sell 25%", "callback_data": f"sell_position|{ticker}|25"},
                {"text": "Sell 50%", "callback_data": f"sell_position|{ticker}|50"},
            ],
            [
                {"text": "Sell 75%", "callback_data": f"sell_position|{ticker}|75"},
                {"text": "Sell 100%", "callback_data": f"sell_position|{ticker}|100"},
            ],
            [{"text": "Strategy Builder", "callback_data": f"strategy_position|{ticker}"}],
            [{"text": f"Advanced Strategy: {advanced}", "callback_data": f"toggle_position_advanced|{ticker}"}],
            [{"text": "Manual Limit Order", "callback_data": f"manual_limit|{ticker}|position|KEEP"}],
            [{"text": "Refresh Position", "callback_data": f"view_position|{ticker}"}],
            [{"text": "Back", "callback_data": "positions_main"}],
        ]
    }