from threading import RLock
import math

from services.base_service import BaseService
from services.market_data_service import market_data_service
from services.trade_journal import trade_journal
from trade_settings import load_settings


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
        return math.floor(float(amount) / (float(price_cents) / 100))
    except Exception:
        return 0


def money(value):
    try:
        return f"${float(value):.2f}"
    except Exception:
        return "$0.00"


class OrderManager(BaseService):
    def __init__(self):
        super().__init__("order_manager")
        self._lock = RLock()
        self.preview_count = 0
        self.buy_count = 0
        self.sell_count = 0
        self.limit_count = 0

    def start(self):
        self.mark_started()

    def stop(self):
        self.mark_stopped()

    def get_market(self, ticker, force_refresh=False):
        ticker = str(ticker).upper().strip()
        market_data_service.register_ticker(ticker)

        if force_refresh:
            return market_data_service.refresh_market(ticker)

        return market_data_service.get_market(ticker)

    def preview(self, ticker, side, amount=None):
        ticker = str(ticker).upper().strip()
        side = str(side).upper().strip()

        market = self.get_market(ticker)

        if not market:
            trade_journal.record_event(
                "ORDER_PREVIEW_FAILED",
                ticker,
                {"side": side, "reason": "market unavailable"},
            )
            return None

        settings = load_settings()
        buy_amount = float(amount or settings.get("default_buy_amount", 10))
        price = get_buy_price(market, side)

        if price is None or price <= 0:
            trade_journal.record_event(
                "ORDER_PREVIEW_FAILED",
                ticker,
                {"side": side, "reason": "invalid price"},
            )
            return None

        contracts = contracts_from_amount(buy_amount, price)
        estimated_cost = round(contracts * price / 100, 2)

        with self._lock:
            self.preview_count += 1

        preview = {
            "ticker": ticker,
            "title": market.get("title") or market.get("market_title") or "",
            "side": side,
            "price": price,
            "amount": buy_amount,
            "contracts": contracts,
            "estimated_cost": estimated_cost,
            "unused_cash": round(buy_amount - estimated_cost, 2),
            "advanced_strategy": bool(settings.get("advanced_strategy")),
            "settings": settings,
        }

        trade_journal.record_event("ORDER_PREVIEW", ticker, preview)

        return preview

    def preview_text(self, ticker, side, amount=None):
        preview = self.preview(ticker, side, amount=amount)

        if not preview:
            return f"""
ORDER PREVIEW ERROR

Ticker:
{str(ticker).upper().strip()}

Side:
BUY {str(side).upper().strip()}

Status:
Unable to build preview.
""".strip()

        settings = preview["settings"]
        advanced = "ON" if preview["advanced_strategy"] else "OFF"

        return f"""
ORDER PREVIEW

Ticker:
{preview["ticker"]}

Market:
{preview["title"]}

Side:
BUY {preview["side"]}

Buy Amount:
{money(preview["amount"])}

Price:
{preview["price"]}c

Estimated Contracts:
{preview["contracts"]}

Estimated Cost:
{money(preview["estimated_cost"])}

Unused Cash:
{money(preview["unused_cash"])}

Advanced Strategy:
{advanced}

Take Profit:
TP1 +{settings.get("tp1_pct")}% | Sell {settings.get("tp1_sell_pct")}%
TP2 +{settings.get("tp2_pct")}% | Sell {settings.get("tp2_sell_pct")}%
TP3 +{settings.get("tp3_pct")}% | Sell {settings.get("tp3_sell_pct")}%

Stop Loss:
-{settings.get("stop_loss_pct")}%
""".strip()

    def sell_preview(self, ticker, side):
        ticker = str(ticker).upper().strip()
        side = str(side).upper().strip()

        market = self.get_market(ticker)

        if not market:
            return None

        price = get_sell_price(market, side)

        with self._lock:
            self.sell_count += 1

        result = {
            "ticker": ticker,
            "title": market.get("title") or market.get("market_title") or "",
            "side": side,
            "sell_price": price,
        }

        trade_journal.record_event("SELL_PREVIEW", ticker, result)

        return result

    def buy(self, ticker, amount):
        with self._lock:
            self.buy_count += 1

        result = {
            "success": False,
            "message": "Execution not connected to OrderManager yet.",
            "ticker": ticker,
            "amount": amount,
        }

        trade_journal.record_event("BUY_REQUEST", ticker, result)
        return result

    def sell(self, ticker, amount):
        with self._lock:
            self.sell_count += 1

        result = {
            "success": False,
            "message": "Execution not connected to OrderManager yet.",
            "ticker": ticker,
            "amount": amount,
        }

        trade_journal.record_event("SELL_REQUEST", ticker, result)
        return result

    def limit(self, ticker, side, price, amount):
        with self._lock:
            self.limit_count += 1

        result = {
            "success": False,
            "message": "Limit execution not connected to OrderManager yet.",
            "ticker": ticker,
            "side": side,
            "price": price,
            "amount": amount,
        }

        trade_journal.record_event("LIMIT_REQUEST", ticker, result)
        return result

    def diagnostics(self):
        data = super().diagnostics()
        data.update(
            {
                "preview_count": self.preview_count,
                "buy_count": self.buy_count,
                "sell_count": self.sell_count,
                "limit_count": self.limit_count,
            }
        )
        return data


order_manager = OrderManager()