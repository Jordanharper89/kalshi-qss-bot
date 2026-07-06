import sys

from services.order_manager import order_manager
from services.market_data_service import market_data_service


def to_cents(value):
    try:
        if value is None:
            return None
        value = float(value)
        if value <= 1:
            value *= 100
        return round(value, 1)
    except Exception:
        return None


def get_market(ticker, force_refresh=False):
    ticker = str(ticker).upper().strip()
    market_data_service.register_ticker(ticker)

    if force_refresh:
        return market_data_service.refresh_market(ticker)

    return market_data_service.get_market(ticker)


def prewarm_market(ticker):
    return get_market(ticker, force_refresh=True)


def clear_market_cache(ticker=None):
    if ticker:
        market_data_service.cache.remove(str(ticker).upper().strip())
    else:
        market_data_service.cache.clear()


def first_valid(market, keys):
    if not isinstance(market, dict):
        return None

    for key in keys:
        if market.get(key) is not None:
            price = to_cents(market.get(key))
            if price is not None and price > 0:
                return price

    return None


def get_yes_bid(market):
    return first_valid(market, ["yes_bid", "yes_bid_dollars", "yes_bid_price", "best_yes_bid", "bid"])


def get_yes_ask(market):
    return first_valid(market, ["yes_ask", "yes_ask_dollars", "yes_ask_price", "best_yes_ask", "ask"])


def get_no_bid(market):
    no_bid = first_valid(market, ["no_bid", "no_bid_dollars", "no_bid_price", "best_no_bid"])
    if no_bid is not None:
        return no_bid

    yes_ask = get_yes_ask(market)
    return round(100 - yes_ask, 1) if yes_ask is not None else None


def get_no_ask(market):
    no_ask = first_valid(market, ["no_ask", "no_ask_dollars", "no_ask_price", "best_no_ask"])
    if no_ask is not None:
        return no_ask

    yes_bid = get_yes_bid(market)
    return round(100 - yes_bid, 1) if yes_bid is not None else None


def get_buy_price(market, side):
    side = str(side).upper().strip()
    if side == "YES":
        return get_yes_ask(market)
    if side == "NO":
        return get_no_ask(market)
    return None


def get_sell_price(market, side):
    side = str(side).upper().strip()
    if side == "YES":
        return get_yes_bid(market)
    if side == "NO":
        return get_no_bid(market)
    return None


def contracts_from_amount(amount, price_cents):
    try:
        import math
        return math.floor(float(amount) / (float(price_cents) / 100))
    except Exception:
        return 0


def money(value):
    try:
        return f"${float(value):.2f}"
    except Exception:
        return "$0.00"


def build_order_preview(ticker, side):
    return order_manager.preview_text(ticker, side)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python order_preview.py TICKER YES_OR_NO")
    else:
        print(build_order_preview(sys.argv[1], sys.argv[2]))