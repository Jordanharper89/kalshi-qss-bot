from position_manager import (
    get_all_positions,
    get_position,
    format_position_card,
)
from trade_settings import load_settings


def position_list_text():
    positions = get_all_positions()

    if not positions:
        return "NO OPEN POSITIONS"

    lines = []
    lines.append("OPEN POSITIONS")
    lines.append("=" * 40)

    for i, pos in enumerate(positions.values(), start=1):
        lines.append(f"{i}. {pos['ticker']}")
        lines.append(f"Side: {pos['side']}")
        lines.append(f"Entry: {pos['entry_price']}c")
        lines.append(f"Remaining: {pos['remaining_contracts']}")
        lines.append("-" * 40)

    return "\n".join(lines)


def position_list_keyboard():
    positions = get_all_positions()

    buttons = []

    for pos in positions.values():
        ticker = pos["ticker"]
        side = pos["side"]

        buttons.append([
            {
                "text": f"View {side} {ticker[:18]}",
                "callback_data": f"view_position|{ticker}",
            }
        ])

    return {
        "inline_keyboard": buttons
    }


def position_card_text(ticker, current_price=None):
    position = get_position(ticker)

    if not position:
        return "POSITION NOT FOUND"

    return format_position_card(position, current_price=current_price)


def position_card_keyboard(ticker):
    settings = load_settings()
    buy_amounts = settings.get("quick_buy_amounts", [5, 10, 25, 50])[:4]

    b1 = buy_amounts[0] if len(buy_amounts) > 0 else 5
    b2 = buy_amounts[1] if len(buy_amounts) > 1 else 10
    b3 = buy_amounts[2] if len(buy_amounts) > 2 else 25
    b4 = buy_amounts[3] if len(buy_amounts) > 3 else 50

    return {
        "inline_keyboard": [
            [
                {
                    "text": f"Buy ${b1}",
                    "callback_data": f"buy_more|{ticker}|{b1}",
                },
                {
                    "text": f"Buy ${b2}",
                    "callback_data": f"buy_more|{ticker}|{b2}",
                },
            ],
            [
                {
                    "text": f"Buy ${b3}",
                    "callback_data": f"buy_more|{ticker}|{b3}",
                },
                {
                    "text": f"Buy ${b4}",
                    "callback_data": f"buy_more|{ticker}|{b4}",
                },
            ],
            [
                {
                    "text": "Sell 25%",
                    "callback_data": f"sell_position|{ticker}|25",
                },
                {
                    "text": "Sell 50%",
                    "callback_data": f"sell_position|{ticker}|50",
                },
            ],
            [
                {
                    "text": "Sell 75%",
                    "callback_data": f"sell_position|{ticker}|75",
                },
                {
                    "text": "Sell 100%",
                    "callback_data": f"sell_position|{ticker}|100",
                },
            ],
            [
                {
                    "text": "Refresh",
                    "callback_data": f"refresh_position|{ticker}",
                },
            ],
            [
                {
                    "text": "Strategy",
                    "callback_data": f"position_strategy|{ticker}",
                },
            ],
            [
                {
                    "text": "Back To Positions",
                    "callback_data": "positions_main",
                },
            ],
        ]
    }


def position_strategy_text(ticker):
    position = get_position(ticker)

    if not position:
        return "POSITION NOT FOUND"

    settings = position.get("settings") or load_settings()

    auto_tp = "ON" if settings.get("auto_take_profit", True) else "OFF"
    auto_sl = "ON" if settings.get("auto_stop_loss", True) else "OFF"
    dip = "ON" if settings.get("dip_buy_enabled", False) else "OFF"
    trailing = "ON" if settings.get("trailing_stop", False) else "OFF"
    breakeven = "ON" if settings.get("move_stop_to_breakeven", True) else "OFF"

    return f"""
POSITION STRATEGY
========================================
Ticker: {ticker}
Side: {position["side"]}

Auto Take Profit: {auto_tp}
Auto Stop Loss: {auto_sl}

Take Profit:
- TP1: +{settings.get("tp1_pct", 20)}% | Sell {settings.get("tp1_sell_pct", 25)}%
- TP2: +{settings.get("tp2_pct", 40)}% | Sell {settings.get("tp2_sell_pct", 50)}%
- TP3: +{settings.get("tp3_pct", 75)}% | Sell {settings.get("tp3_sell_pct", 25)}%

Stop Loss:
- {settings.get("stop_loss_pct", 20)}%

Dip Buy: {dip}
Trailing Stop: {trailing}
Move Stop To Breakeven: {breakeven}
========================================
""".strip()


def position_strategy_keyboard(ticker):
    return {
        "inline_keyboard": [
            [
                {
                    "text": "Edit TP1",
                    "callback_data": f"position_tp|{ticker}|1",
                },
                {
                    "text": "Edit TP2",
                    "callback_data": f"position_tp|{ticker}|2",
                },
                {
                    "text": "Edit TP3",
                    "callback_data": f"position_tp|{ticker}|3",
                },
            ],
            [
                {
                    "text": "Edit Stop Loss",
                    "callback_data": f"position_stop|{ticker}",
                },
            ],
            [
                {
                    "text": "Toggle Auto TP",
                    "callback_data": f"toggle_position_auto_tp|{ticker}",
                },
                {
                    "text": "Toggle Auto SL",
                    "callback_data": f"toggle_position_auto_sl|{ticker}",
                },
            ],
            [
                {
                    "text": "Toggle Dip Buy",
                    "callback_data": f"toggle_position_dip|{ticker}",
                },
            ],
            [
                {
                    "text": "Toggle Trailing",
                    "callback_data": f"toggle_position_trailing|{ticker}",
                },
            ],
            [
                {
                    "text": "Back To Position",
                    "callback_data": f"view_position|{ticker}",
                },
            ],
        ]
    }


if __name__ == "__main__":
    print(position_list_text())