
"""
ORACLE-034 — Signal Engine

Purpose:
- Convert ranked opportunities into Oracle trading signals.
"""

def build_signals(opportunities):

    signals = []

    for market in opportunities:

        score = market.get("oracle_score", 0)

        if score >= 90:
            signal = "STRONG BUY"

        elif score >= 85:
            signal = "BUY"

        elif score >= 80:
            signal = "WATCH"

        elif score >= 70:
            signal = "NEUTRAL"

        else:
            signal = "IGNORE"

        m = dict(market)
        m["oracle_signal"] = signal

        signals.append(m)

    return signals
