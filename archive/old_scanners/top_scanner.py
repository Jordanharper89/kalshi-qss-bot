import requests
from datetime import datetime, timezone

from config import BASE_URL
from q4_edge_engine import score_market, snapshot
from q5_volume_scalp import q5_scalp_score
from q6_trend_filter import q6_trend_score
from final_trade_decision import final_trade_decision


MAX_SERIES_TO_SCAN = 100
MAX_PLAYS_TO_SHOW = 10


ALLOWED_CATEGORIES = [
    "crypto",
    "weather",
    "sports",
]


def minutes_until_close(market):
    close_time = market.get("close_time") or market.get("expiration_time")

    if not close_time:
        return None

    close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    return int((close_dt - now).total_seconds() / 60)


def get_series(limit=500):
    r = requests.get(
        f"{BASE_URL}/series",
        params={"limit": limit},
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("series", [])


def get_series_markets(series_ticker):
    r = requests.get(
        f"{BASE_URL}/markets",
        params={
            "series_ticker": series_ticker,
            "status": "open",
            "limit": 100,
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("markets", [])


def is_useful_market(play):
    category = str(play.get("category", "")).lower()
    ticker = str(play.get("ticker", "")).lower()
    title = str(play.get("title", "")).lower()
    series = str(play.get("series_title", "")).lower()
    sport = str(play.get("sport", "")).lower()

    text = f"{ticker} {title} {series}"

    if category == "weather":
        return True

    if category == "crypto":
        return (
            "btc" in text
            or "bitcoin" in text
            or "eth" in text
            or "ethereum" in text
            or "solana" in text
            or "kxbtc" in ticker
            or "kxbtcd" in ticker
            or "kxeth" in ticker
            or "kxsol" in ticker
            or "kxsold" in ticker
        )

    if category == "sports":
        return sport in ["mlb", "soccer"]

    return False


def build_final_play(play):
    snap = play.get("snap") or {}
    minutes_left = play.get("minutes_left")

    q5 = q5_scalp_score(
        market_probability=play["market_probability"],
        bot_probability=play["bot_probability"],
        spread=snap.get("spread", 99),
        volume_24h=snap.get("volume_24h", 0),
        move=snap.get("move", 0),
        minutes_left=minutes_left,
        side=None,
    )

    q6 = q6_trend_score(
        current_price=None,
        target_price=None,
        market_probability=play["market_probability"],
        move=snap.get("move", 0),
        volume_24h=snap.get("volume_24h", 0),
        minutes_left=minutes_left,
        chart_bias="unknown",
    )

    final = final_trade_decision(
        q4_grade=play["grade"],
        q4_edge=play["edge"],
        q5_score=q5["q5_score"],
        q5_grade=q5["q5_grade"],
        q6_score=q6["q6_score"],
        q6_grade=q6["q6_grade"],
        market_probability=play["market_probability"],
        minutes_left=minutes_left,
    )

    play["q5"] = q5
    play["q6"] = q6
    play["final"] = final

    return play


def run_top_scan():
    print()
    print("TOP OPPORTUNITIES")
    print("Final scanner: Q4 + Q5 + Q6")
    print("Sorted by final confidence")
    print("-" * 60)

    series_list = get_series()
    series_list = series_list[:MAX_SERIES_TO_SCAN]

    plays = []

    for series in series_list:
        series_ticker = series.get("ticker")
        series_title = series.get("title")

        if not series_ticker:
            continue

        try:
            markets = get_series_markets(series_ticker)
        except Exception:
            continue

        for market in markets:
            minutes_left = minutes_until_close(market)

            if minutes_left is None or minutes_left <= 0:
                continue

            market["series_title"] = series_title

            try:
                result = score_market(market)
            except Exception:
                continue

            if not result:
                continue

            result["series_title"] = series_title
            result["minutes_left"] = minutes_left

            try:
                result["snap"] = snapshot(market)
            except Exception:
                result["snap"] = {
                    "spread": 99,
                    "volume_24h": 0,
                    "move": 0,
                }

            if not is_useful_market(result):
                continue

            final_play = build_final_play(result)

            if final_play["final"]["final_grade"] == "PASS":
                continue

            plays.append(final_play)

    plays = sorted(
        plays,
        key=lambda x: x["final"]["confidence"],
        reverse=True,
    )

    plays = plays[:MAX_PLAYS_TO_SHOW]

    if not plays:
        print("NO QUALIFIED TOP PLAYS FOUND")
        return

    for i, play in enumerate(plays, start=1):
        final = play["final"]
        q5 = play["q5"]
        q6 = play["q6"]
        snap = play.get("snap", {})

        print("-" * 60)
        print(f"#{i}")
        print("Final Grade:", final["final_grade"])
        print("Confidence:", str(final["confidence"]) + "/100")
        print("Recommendation:", final["lean"])
        print("Best Use:", final["strategy"])
        print("Side:", play["side"])
        print("Category:", play["category"])

        if play.get("sport"):
            print("Sport:", play["sport"])

        print("Series:", play.get("series_title"))
        print("Minutes Left:", play.get("minutes_left"))
        print("Spread:", str(snap.get("spread")) + "c")
        print("Move:", str(snap.get("move")) + "c")
        print("Volume 24h:", snap.get("volume_24h"))
        print()
        print(play["title"])
        print("Ticker:", play["ticker"])
        print("Kalshi:", play["url"])
        print()
        print("Final Scores:")
        print("- Settlement:", str(final["settlement_score"]) + "/100")
        print("- Scalp:", str(final["scalp_score"]) + "/100")
        print("- Trend:", str(final["trend_score"]) + "/100")
        print()
        print("Settlement:")
        print("- Grade:", play["grade"])
        print("- Edge: +" + str(play["edge"]) + "%")
        print("- Entry:", str(play["rules"]["entry"]) + "c")
        print("- Target:", str(play["rules"]["target"]) + "c")
        print("- Strong Target:", str(play["rules"]["strong_target"]) + "c")
        print("- Stop:", str(play["rules"]["stop"]) + "c")
        print()
        print("Scalp:")
        print("- Grade:", q5["q5_grade"])
        print("- Score:", str(q5["q5_score"]) + "/100")
        print("- Setup:", q5["setup"])
        print("- Entry:", str(play["market_probability"]) + "c")
        print("- Quick Target:", str(q5["quick_target"]) + "c")
        print("- Strong Target:", str(q5["strong_target"]) + "c")
        print("- Stop:", str(q5["stop"]) + "c")

        if q5.get("reasons"):
            print()
            print("Scalp Reasons:")
            for reason in q5["reasons"][:5]:
                print("-", reason)

        if q6.get("reasons"):
            print()
            print("Trend Reasons:")
            for reason in q6["reasons"][:4]:
                print("-", reason)


if __name__ == "__main__":
    run_top_scan()