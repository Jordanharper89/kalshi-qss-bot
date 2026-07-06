from pathlib import Path

path = Path("oracle_telegram.py")
text = path.read_text(encoding="utf-8")

backup = Path("oracle_telegram_backup_before_why.py")
backup.write_text(text, encoding="utf-8")

if "def oracle_why_text(" not in text:
    text += r'''


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
'''

path.write_text(text, encoding="utf-8")

print("Patched oracle_telegram.py with oracle_why_text.")
print("Backup saved as oracle_telegram_backup_before_why.py")