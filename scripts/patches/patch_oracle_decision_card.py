from pathlib import Path

path = Path("oracle_telegram.py")
text = path.read_text(encoding="utf-8")

backup = Path("oracle_telegram_backup_before_decision_card.py")
backup.write_text(text, encoding="utf-8")

start = text.find("def oracle_signal_text(")

if start == -1:
    raise SystemExit("Could not find oracle_signal_text() in oracle_telegram.py")

next_def = text.find("\ndef ", start + 1)

if next_def == -1:
    next_def = len(text)

new_function = r'''
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
'''

text = text[:start] + new_function + text[next_def:]

path.write_text(text, encoding="utf-8")

print("Patched oracle_telegram.py decision card.")
print("Backup saved as oracle_telegram_backup_before_decision_card.py")