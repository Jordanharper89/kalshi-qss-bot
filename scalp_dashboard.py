from services.market_data_service import market_data_service


def cents(value):
    try:
        if value is None:
            return None
        value = float(value)
        if value <= 1:
            return round(value * 100, 2)
        return round(value, 2)
    except Exception:
        return None


def get_market(ticker):
    ticker = str(ticker).upper().strip()
    market_data_service.register_ticker(ticker)
    return market_data_service.get_market(ticker)


def price_line(label, value):
    value = cents(value)
    if value is None:
        return f"{label}: n/a"
    return f"{label}: {value}c"


def build_scalp_dashboard(ticker):
    ticker = str(ticker).upper().strip()
    market = get_market(ticker)

    if not market:
        return f"""
SCALP DASHBOARD

Ticker:
{ticker}

Status:
Market data unavailable.
""".strip()

    title = market.get("title") or market.get("market_title") or "Unknown market"

    return f"""
SCALP DASHBOARD

Ticker:
{ticker}

Market:
{title}

YES:
{price_line("Bid", market.get("yes_bid_dollars"))}
{price_line("Ask", market.get("yes_ask_dollars"))}

NO:
{price_line("Bid", market.get("no_bid_dollars"))}
{price_line("Ask", market.get("no_ask_dollars"))}

Last:
{price_line("Price", market.get("last_price_dollars"))}

Source:
MarketDataService
""".strip()


if __name__ == "__main__":
    import sys

    ticker = sys.argv[1] if len(sys.argv) > 1 else "KXBTCD-26JUN2717-T59749.99"
    print(build_scalp_dashboard(ticker))