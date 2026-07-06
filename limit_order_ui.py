from services.order_manager import (
    order_manager,
    get_buy_price,
    money,
)


def manual_limit_text(ticker, source="scan", side="YES"):
    ticker = str(ticker).upper().strip()
    side = str(side).upper().strip()

    market = order_manager.get_market(ticker)

    if not market:
        return f"""
MANUAL LIMIT ORDER

Ticker:
{ticker}

Status:
Market unavailable.
""".strip()

    suggested_price = get_buy_price(market, side)

    return f"""
MANUAL LIMIT ORDER

Ticker:
{ticker}

Market:
{market.get("title") or market.get("market_title")}

Side:
BUY {side}

Suggested Limit:
{suggested_price}c

Choose order type below.
""".strip()


def manual_limit_keyboard(ticker, source="scan", side="YES"):
    ticker = str(ticker).upper().strip()
    source = str(source).strip()
    side = str(side).upper().strip()

    return {
        "inline_keyboard": [
            [
                {
                    "text": "Limit @ Market",
                    "callback_data": f"manual_limit_market|{ticker}|{source}|{side}",
                }
            ],
            [
                {
                    "text": "Limit Better -1c",
                    "callback_data": f"manual_limit_better|{ticker}|{source}|{side}|1",
                },
                {
                    "text": "Limit Better -2c",
                    "callback_data": f"manual_limit_better|{ticker}|{source}|{side}|2",
                },
            ],
            [
                {
                    "text": "Back",
                    "callback_data": f"scan_side|{ticker}|{source}|{side}",
                }
            ],
        ]
    }


def limit_price_text(ticker, source="scan", side="YES", amount=None):
    return manual_limit_text(ticker, source, side)


def limit_price_keyboard(ticker, source="scan", side="YES"):
    return manual_limit_keyboard(ticker, source, side)


def limit_amount_text(ticker, source="scan", side="YES", price=None):
    ticker = str(ticker).upper().strip()
    side = str(side).upper().strip()

    return f"""
LIMIT ORDER AMOUNT

Ticker:
{ticker}

Side:
BUY {side}

Limit Price:
{price if price is not None else "Market"}c

Choose amount below.
""".strip()


def limit_amount_keyboard(ticker, source="scan", side="YES", price=None):
    ticker = str(ticker).upper().strip()
    source = str(source).strip()
    side = str(side).upper().strip()
    price_value = price if price is not None else "market"

    return {
        "inline_keyboard": [
            [
                {
                    "text": "$1",
                    "callback_data": f"place_limit|{ticker}|{source}|{side}|limit|{price_value}|1",
                },
                {
                    "text": "$5",
                    "callback_data": f"place_limit|{ticker}|{source}|{side}|limit|{price_value}|5",
                },
            ],
            [
                {
                    "text": "$10",
                    "callback_data": f"place_limit|{ticker}|{source}|{side}|limit|{price_value}|10",
                },
                {
                    "text": "$25",
                    "callback_data": f"place_limit|{ticker}|{source}|{side}|limit|{price_value}|25",
                },
            ],
            [
                {
                    "text": "Back",
                    "callback_data": f"manual_limit_market|{ticker}|{source}|{side}",
                }
            ],
        ]
    }


def build_manual_limit_preview(ticker, source, side, order_type, price=None, amount=None):
    ticker = str(ticker).upper().strip()
    source = str(source).strip()
    side = str(side).upper().strip()
    order_type = str(order_type).strip()

    market = order_manager.get_market(ticker)

    if not market:
        return f"""
LIMIT ORDER PREVIEW ERROR

Ticker:
{ticker}

Market unavailable.
""".strip()

    market_price = get_buy_price(market, side)

    if price is None or str(price).lower() == "market":
        price = market_price

    if amount is None:
        amount = 10

    return f"""
LIMIT ORDER PREVIEW

Ticker:
{ticker}

Market:
{market.get("title") or market.get("market_title")}

Side:
BUY {side}

Order Type:
{order_type.replace("_", " ")}

Market Price:
{market_price}c

Limit Price:
{price}c

Amount:
{money(amount)}
""".strip()