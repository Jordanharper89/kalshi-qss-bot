import re

from services.market_data_service import market_data_service


def kalshi_url(ticker):
    return f"https://kalshi.com/markets/{str(ticker).lower()}"


def extract_ticker(text):
    text = str(text or "").strip()

    match = re.search(r"op_market_ticker=([A-Z0-9.\-_]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    match = re.search(r"(KX[A-Z0-9.\-_]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    return text.upper()


def to_cents(value):
    if value is None:
        return None

    try:
        value = float(value)

        if value <= 1:
            value *= 100

        return round(value, 1)

    except Exception:
        return None


def get_market_by_ticker(ticker):
    ticker = extract_ticker(ticker)
    market_data_service.register_ticker(ticker)
    return market_data_service.get_market(ticker)


def first_valid(market, keys):
    if not isinstance(market, dict):
        return None

    for key in keys:
        value = market.get(key)

        if value is None:
            continue

        price = to_cents(value)

        if price is not None and price > 0:
            return price

    return None


def market_title(market):
    if not market:
        return "Unknown market"

    return (
        market.get("title")
        or market.get("market_title")
        or market.get("subtitle")
        or "Unknown market"
    )


def get_yes_bid(market):
    return first_valid(
        market,
        [
            "yes_bid",
            "yes_bid_dollars",
            "yes_bid_price",
            "best_yes_bid",
            "bid",
        ],
    )


def get_yes_ask(market):
    return first_valid(
        market,
        [
            "yes_ask",
            "yes_ask_dollars",
            "yes_ask_price",
            "best_yes_ask",
            "ask",
        ],
    )


def get_no_bid(market):
    no_bid = first_valid(
        market,
        [
            "no_bid",
            "no_bid_dollars",
            "no_bid_price",
            "best_no_bid",
        ],
    )

    if no_bid is not None:
        return no_bid

    yes_ask = get_yes_ask(market)

    if yes_ask is not None:
        return round(100 - yes_ask, 1)

    return None


def get_no_ask(market):
    no_ask = first_valid(
        market,
        [
            "no_ask",
            "no_ask_dollars",
            "no_ask_price",
            "best_no_ask",
        ],
    )

    if no_ask is not None:
        return no_ask

    yes_bid = get_yes_bid(market)

    if yes_bid is not None:
        return round(100 - yes_bid, 1)

    return None


def format_price(value):
    value = to_cents(value)

    if value is None:
        return "n/a"

    return f"{value}c"


def answer_market_question(user_input):
    ticker = extract_ticker(user_input)
    market = get_market_by_ticker(ticker)

    if not market:
        return f"""
AI ANSWER

Ticker:
{ticker}

Status:
Market data unavailable.

Source:
MarketDataService
""".strip()

    yes_bid = get_yes_bid(market)
    yes_ask = get_yes_ask(market)
    no_bid = get_no_bid(market)
    no_ask = get_no_ask(market)

    last_price = (
        market.get("last_price_dollars")
        or market.get("last_price")
        or market.get("previous_price_dollars")
    )

    volume = market.get("volume") or market.get("volume_fp") or market.get("volume_24h_fp") or 0
    open_interest = market.get("open_interest") or market.get("open_interest_fp") or 0

    return f"""
AI MARKET ANSWER

Ticker:
{ticker}

Market:
{market_title(market)}

YES:
Bid {format_price(yes_bid)}
Ask {format_price(yes_ask)}

NO:
Bid {format_price(no_bid)}
Ask {format_price(no_ask)}

Last:
{format_price(last_price)}

Volume:
{volume}

Open Interest:
{open_interest}

Kalshi:
{kalshi_url(ticker)}

Source:
MarketDataService
""".strip()


def ask_ai(user_input):
    return answer_market_question(user_input)


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ai_answer.py TICKER_OR_KALSHI_LINK")
        return

    print(answer_market_question(" ".join(sys.argv[1:])))


if __name__ == "__main__":
    main()