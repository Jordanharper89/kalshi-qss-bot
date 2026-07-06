from pathlib import Path

root = Path.cwd()

signal_file = root / "oracle_signal_engine.py"
engine_file = root / "oracle_research_engine.py"

signal_code = r'''
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
'''

signal_file.write_text(signal_code, encoding="utf-8")

print("[OK] Created oracle_signal_engine.py")

text = engine_file.read_text(encoding="utf-8")

backup = root / "oracle_research_engine.py.oracle034_backup"
backup.write_text(text, encoding="utf-8")

if "from oracle_signal_engine import build_signals" not in text:
    text = (
        "from oracle_signal_engine import build_signals\n"
        + text
    )

old = '''
            self.snapshot["opportunities"] = ranked[:25]
'''

new = '''
            ranked = build_signals(ranked)

            self.snapshot["opportunities"] = ranked[:25]
'''

if old in text:
    text = text.replace(old, new)

engine_file.write_text(text, encoding="utf-8")

print("[DONE] ORACLE-034 Signal Engine installed")