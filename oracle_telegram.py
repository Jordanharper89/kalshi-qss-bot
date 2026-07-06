from oracle.api.signal_feed import (
    get_top_signals,
    get_watchlist_signals,
    get_signal_by_ticker,
    get_latest_quality_report,
)


def short_title(title, limit=90):
    if not title:
        return "Untitled market"
    return title if len(title) <= limit else title[:limit] + "..."


def oracle_menu_text():
    return """
ORACLE RESEARCH

Oracle = research brain.
Q Series = execution layer.

Commands:
/oracle_top = Clean B+ signals only
/oracle_watch = Research watchlist
/oracle_quality = Data quality report
/oracle_signal TICKER = Signal detail
""".strip()


def oracle_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "Top Signals", "callback_data": "oracle_top"}],
            [{"text": "Research Watchlist", "callback_data": "oracle_watch"}],
            [{"text": "Quality Report", "callback_data": "oracle_quality"}],
            [{"text": "Back To Main Menu", "callback_data": "main_menu"}],
        ]
    }


def oracle_back_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "Oracle Menu", "callback_data": "oracle_menu"}],
            [{"text": "Back To Main Menu", "callback_data": "main_menu"}],
        ]
    }


def oracle_top_text(limit=10):
    signals = get_top_signals(limit=limit, min_grade="B", hide_multileg=True)

    if not signals:
        return """
ORACLE TOP SIGNALS

No clean B+ or better signals yet.

This is good. Oracle is not forcing bad plays.

Use /oracle_watch to see lower-grade research candidates.
""".strip()

    lines = ["ORACLE TOP SIGNALS", "Clean B+ or better only", ""]

    for i, s in enumerate(signals, start=1):
        lines.append(f"{i}. {s['grade']} | Edge {round(s['edge_percent'] or 0, 2)} | Conf {round(s['confidence_score'] or 0, 2)}")
        lines.append(f"Market: {round(s['market_probability'] or 0, 2)}")
        lines.append(f"Oracle: {round(s['oracle_fair_value'] or 0, 2)}")
        lines.append(f"Title: {short_title(s.get('market_title'))}")
        lines.append(f"Ticker: {s['ticker']}")
        lines.append("")

    return "\n".join(lines).strip()


def oracle_watch_text(limit=10):
    signals = get_watchlist_signals(limit=limit)

    if not signals:
        return "ORACLE WATCHLIST\n\nNo watchlist signals found yet."

    lines = ["ORACLE WATCHLIST", "Lower-grade research candidates", ""]

    for i, s in enumerate(signals, start=1):
        lines.append(f"{i}. {s['grade']} | Edge {round(s['edge_percent'] or 0, 2)} | Conf {round(s['confidence_score'] or 0, 2)}")
        lines.append(f"Market: {round(s['market_probability'] or 0, 2)}")
        lines.append(f"Oracle: {round(s['oracle_fair_value'] or 0, 2)}")
        lines.append(f"Title: {short_title(s.get('market_title'))}")
        lines.append(f"Ticker: {s['ticker']}")
        lines.append("")

    return "\n".join(lines).strip()


def oracle_quality_text():
    r = get_latest_quality_report()

    if not r:
        return "ORACLE QUALITY REPORT\n\nNo report found yet. Run Oracle first."

    return f"""
ORACLE QUALITY REPORT

Run ID:
{r.get("run_id")}

Markets:
Total: {r.get("total_markets")}
Unique: {r.get("unique_markets")}
Useful Priced: {r.get("useful_priced_markets")}

Data:
Snapshots: {r.get("snapshots_total")}
Features: {r.get("features_total")}
Signals: {r.get("signals_total")}

Missing:
Probability: {r.get("missing_market_probability")}
Spread Score: {r.get("missing_spread_score")}

Signal Grades:
A+: {r.get("grade_a_plus")}
A: {r.get("grade_a")}
A-: {r.get("grade_a_minus")}
B: {r.get("grade_b")}
C: {r.get("grade_c")}
D: {r.get("grade_d")}

Average Confidence:
{round(r.get("avg_confidence") or 0, 2)}
""".strip()



def oracle_signal_text(ticker):
    from oracle.api.ticker_ingest import ensure_ticker_in_oracle
    from oracle.engines.trade_decision import decide_trade

    cleaned_ticker = ensure_ticker_in_oracle(ticker)
    s = get_signal_by_ticker(cleaned_ticker)

    if not s:
        return f"""
ORACLE SIGNAL

No signal found yet for:
{cleaned_ticker}

Oracle checked the ticker, but no usable signal was created yet.
""".strip()

    decision = decide_trade(
        s.get("yes_price"),
        s.get("no_price"),
        s.get("oracle_fair_value"),
        s.get("confidence_score"),
    )

    reasons = s.get("reasons") or []
    reason_text = "\n".join([f"- {r}" for r in reasons]) if reasons else "- No reasons stored"

    return f"""
ORACLE SIGNAL

Ticker:
{s.get("ticker")}

Market:
{short_title(s.get("market_title"), 250)}

Grade:
{s.get("grade")}

YES Price:
{s.get("yes_price")}c

NO Price:
{s.get("no_price")}c

Market Probability:
{round(s.get("market_probability") or 0, 2)}%

Oracle Fair Value:
{round(s.get("oracle_fair_value") or 0, 2)}%

YES Edge:
{decision["yes_edge"]}c

NO Edge:
{decision["no_edge"]}c

Confidence:
{round(s.get("confidence_score") or 0, 2)}%

====================
ORACLE DECISION
====================

Bias:
{decision["bias"]}

Action:
{decision["action"]}

Selected Edge:
{decision["selected_edge"]}c

Suggested Entry:
{decision["suggested_entry"]}

Maximum Entry:
{decision["max_entry"] if decision["max_entry"] is not None else "N/A"}

Take Profit:
{decision["take_profit"]}

Expected Hold:
{decision["expected_hold"]}

Stop Rule:
{decision["stop_rule"]}

Decision Reason:
{decision["reason"]}

Research Reasons:
{reason_text}
""".strip()


def oracle_signal_decision_keyboard(ticker, action="PASS"):
    ticker = str(ticker).upper().strip()
    action = str(action or "PASS").upper().strip()

    buttons = []

    if action in {"BUY YES", "BUY NO"}:
        side = "YES" if action == "BUY YES" else "NO"
        buttons.append(
            [
                {"text": "Ape In", "callback_data": f"scan_side|{ticker}|oracle|{side}"},
                {"text": "Manual Limit", "callback_data": f"manual_limit|{ticker}|oracle|{side}"},
            ]
        )

    buttons.append(
        [
            {"text": "Refresh Oracle", "callback_data": f"oracle_signal|{ticker}"},
            {"text": "Watch", "callback_data": f"oracle_watch_ticker|{ticker}"},
        ]
    )

    buttons.append(
        [
            {"text": "Why", "callback_data": f"oracle_why|{ticker}"},
            {"text": "Back", "callback_data": "oracle_menu"},
        ]
    )

    return {"inline_keyboard": buttons}



def oracle_why_text(ticker):
    from oracle.api.ticker_ingest import ensure_ticker_in_oracle
    from oracle.engines.trade_decision import decide_trade

    cleaned_ticker = ensure_ticker_in_oracle(ticker)
    s = get_signal_by_ticker(cleaned_ticker)

    if not s:
        return f"""
ORACLE WHY

No research found for:
{cleaned_ticker}
""".strip()

    decision = decide_trade(
        s.get("yes_price"),
        s.get("no_price"),
        s.get("oracle_fair_value"),
        s.get("confidence_score"),
    )

    reasons = s.get("reasons") or []
    reason_text = "\n".join([f"- {r}" for r in reasons]) if reasons else "- No stored research reasons"

    return f"""
ORACLE WHY

Ticker:
{s.get("ticker")}

Market:
{short_title(s.get("market_title"), 250)}

Decision:
{decision["action"]}

Bias:
{decision["bias"]}

Why Oracle sees value:
{decision["reason"]}

YES Edge:
{decision["yes_edge"]}c

NO Edge:
{decision["no_edge"]}c

Confidence:
{decision["confidence_score"]}%

Research Factors:
{reason_text}

Risk Note:
{decision["stop_rule"]}
""".strip()
