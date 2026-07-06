import time

from q4_series_edge import (
    MAX_SERIES_TO_SCAN,
    DELAY_SECONDS,
    get_series,
    get_series_markets,
    is_target_series,
    is_blocked_market,
    minutes_until_close,
    cap_grade_for_hold,
)
from q4_edge_engine import snapshot, detect_category, choose_side, bot_probability_for_market
from edge_engine import analyze_market


MAX_ROWS = 30


def analyze_market_row(market):
    if is_blocked_market(market):
        return None, "blocked KXMVE / multigame / crosscategory"

    snap = snapshot(market)

    if snap["yes_bid"] <= 0 or snap["yes_ask"] <= 0:
        return None, "dead bid/ask"

    if snap["spread"] <= 0:
        return None, "bad spread"

    if snap["spread"] > 8:
        return None, f"spread too wide: {snap['spread']}c"

    title_blob = f"{market.get('title')} {market.get('ticker')} {market.get('category')}"
    category = detect_category(title_blob)
    side, market_price = choose_side(snap)

    if market_price < 8:
        return None, f"entry too cheap / lotto: {market_price}c"

    if market_price > 75:
        return None, f"entry too expensive: {market_price}c"

    prob = bot_probability_for_market(
        market=market,
        snap=snap,
        category=category,
        side=side,
        market_price=market_price,
    )

    edge = analyze_market(
        bot_probability=prob["bot_probability"],
        market_probability=market_price,
    )

    row = {
        "category": category,
        "side": side,
        "market_price": market_price,
        "bot_probability": edge["bot_probability"],
        "market_probability": edge["market_probability"],
        "edge": edge["edge"],
        "grade": edge["grade"],
        "score": edge["score"],
        "decision": edge["decision"],
        "reasons": prob.get("reasons", []),
        "component_scores": prob.get("component_scores", {}),
    }

    if edge["grade"] not in ["A-", "A", "A+"]:
        return row, f"edge too weak: {edge['edge']}% / grade {edge['grade']}"

    return row, "QUALIFIED BEFORE HOLD CAP"


def run_q4_rejections():
    print()
    print("Q4 REJECTION / QUALIFIED DEBUG BOARD")
    print("Shows why markets are filtered and what qualified before caps")
    print("-" * 60)

    series_list = get_series()
    target_series = [s for s in series_list if is_target_series(s)]
    target_series = target_series[:MAX_SERIES_TO_SCAN]

    rows = []

    for series in target_series:
        series_ticker = series.get("ticker")
        if not series_ticker:
            continue

        print(f"Checking: {series_ticker} | {series.get('title')}")
        time.sleep(DELAY_SECONDS)

        try:
            markets = get_series_markets(series_ticker)
        except Exception as e:
            rows.append({
                "series": series_ticker,
                "title": "SERIES ERROR",
                "ticker": "",
                "reason": str(e),
                "analysis": None,
                "minutes_left": None,
                "after_cap": None,
            })
            continue

        for market in markets:
            minutes_left = minutes_until_close(market)
            analysis, reason = analyze_market_row(market)

            after_cap = None

            if analysis and reason == "QUALIFIED BEFORE HOLD CAP":
                fake_play = {
                    "grade": analysis["grade"],
                    "score": analysis["score"],
                }

                capped = cap_grade_for_hold(
                    fake_play,
                    "all",
                    minutes_left,
                )

                if capped is None:
                    after_cap = "REMOVED BY HOLD CAP"
                else:
                    after_cap = f"{capped['grade']} / {capped['score']}"

            rows.append({
                "series": series_ticker,
                "title": market.get("title"),
                "ticker": market.get("ticker"),
                "reason": reason,
                "analysis": analysis,
                "minutes_left": minutes_left,
                "after_cap": after_cap,
            })

    rows = rows[:MAX_ROWS]

    print("-" * 60)

    for i, row in enumerate(rows, start=1):
        print(f"#{i}")
        print(f"Series: {row['series']}")
        print(f"Market: {row['title']}")
        print(f"Ticker: {row['ticker']}")
        print(f"Minutes Left: {row.get('minutes_left')}")
        print(f"Reason: {row['reason']}")

        if row["analysis"]:
            a = row["analysis"]
            print(f"Category: {a['category']}")
            print(f"Side: {a['side']}")
            print(f"Entry: {a['market_price']}c")
            print(f"Bot Probability: {a['bot_probability']}%")
            print(f"Market Probability: {a['market_probability']}%")
            print(f"Edge: +{a['edge']}%")
            print(f"Grade Before Hold Cap: {a['grade']} / {a['score']}")
            if row["after_cap"]:
                print(f"After Hold Cap: {row['after_cap']}")

        print("-" * 60)


if __name__ == "__main__":
    run_q4_rejections()