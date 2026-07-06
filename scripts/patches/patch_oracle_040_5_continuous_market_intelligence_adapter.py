from pathlib import Path
from datetime import datetime

path = Path("oracle_continuous_intelligence.py")

if not path.exists():
    raise FileNotFoundError("oracle_continuous_intelligence.py not found.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

old = '''def _safe_import_opportunities():
    """
    Best-effort opportunity loading.

    Tries current Oracle modules without requiring one exact interface.
    Returns a list.
    """
    # 1) Existing opportunity feed builder
    try:
        from oracle_opportunity_feed import build_oracle_opportunity_feed

        try:
            opportunities = build_oracle_opportunity_feed(
                watched_markets=[],
                min_grade="C",
                min_edge=0,
                min_confidence=0,
                max_items=50,
            )
        except TypeError:
            opportunities = build_oracle_opportunity_feed()

        if isinstance(opportunities, list):
            return opportunities

    except Exception:
        pass

    # 2) Research engine snapshot
    try:
        from oracle_research_engine import oracle_research_engine

        snap = oracle_research_engine.get_snapshot()

        if isinstance(snap, dict):
            for key in ("opportunities", "ranked", "signals", "markets"):
                value = snap.get(key)
                if isinstance(value, list):
                    return value

    except Exception:
        pass

    # 3) Market cache diagnostics only fallback: no opportunities
    return []
'''

new = '''def _safe_import_opportunities():
    """
    ORACLE-040.5:
    Primary source is now Market Intelligence.

    Flow:
    Kalshi event loader / universe file
        -> oracle_market_intelligence.analyze_universe()
        -> actionable intelligence cards
        -> continuous pipeline
    """
    # 1) Real market intelligence cards
    try:
        from oracle_market_intelligence import analyze_universe, get_top_intelligence

        analyze_universe(limit=500, top=50)
        cards = get_top_intelligence(limit=50)

        if isinstance(cards, list) and cards:
            return cards

    except Exception as e:
        print(f"[ORACLE-040.5] market intelligence source error: {e}")

    # 2) Live research adapter fallback
    try:
        from oracle_live_research_adapter import get_live_opportunities

        opportunities = get_live_opportunities(limit=100)
        if isinstance(opportunities, list) and opportunities:
            return opportunities

    except Exception as e:
        print(f"[ORACLE-040.5] live research adapter fallback error: {e}")

    # 3) Existing opportunity feed fallback
    try:
        from oracle_opportunity_feed import build_oracle_opportunity_feed

        try:
            opportunities = build_oracle_opportunity_feed(
                watched_markets=[],
                min_grade="C",
                min_edge=0,
                min_confidence=0,
                max_items=50,
            )
        except TypeError:
            opportunities = build_oracle_opportunity_feed()

        if isinstance(opportunities, list) and opportunities:
            return opportunities

    except Exception:
        pass

    # 4) Research engine snapshot fallback
    try:
        from oracle_research_engine import oracle_research_engine

        snap = oracle_research_engine.get_snapshot()

        if isinstance(snap, dict):
            for key in ("opportunities", "ranked", "signals", "markets"):
                value = snap.get(key)
                if isinstance(value, list) and value:
                    return value

    except Exception:
        pass

    return []
'''

if old not in text:
    raise RuntimeError("Could not find _safe_import_opportunities block.")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-040.5 INSTALLED")
print(" Continuous Market Intelligence Adapter")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python oracle_continuous_intelligence.py")
print(" python telegram_bot.py")
print()
print("Telegram:")
print(" /oracle_intel")