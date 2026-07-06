from pathlib import Path

root = Path.cwd()

ranking_file = root / "oracle_opportunity_ranking.py"
engine_file = root / "oracle_research_engine.py"

ranking_code = r'''
"""
ORACLE-033 — Opportunity Ranking Engine

Purpose:
- Score normalized Oracle markets.
- Return highest-quality opportunities.
"""

def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def score_market(market):

    score = 50.0

    volume = float(market.get("volume", 0))
    liquidity = float(market.get("liquidity", 0))
    yes = float(market.get("yes_price", 0))

    if 20 <= yes <= 80:
        score += 10

    score += min(volume / 5000.0, 20)
    score += min(liquidity / 2000.0, 20)

    score = clamp(score)

    market["oracle_score"] = round(score, 2)

    if score >= 90:
        market["grade"] = "A+"
    elif score >= 85:
        market["grade"] = "A"
    elif score >= 80:
        market["grade"] = "A-"
    elif score >= 75:
        market["grade"] = "B+"
    elif score >= 70:
        market["grade"] = "B"
    else:
        market["grade"] = "C"

    return market


def rank_markets(markets):

    ranked = []

    for market in markets.values():
        ranked.append(score_market(dict(market)))

    ranked.sort(
        key=lambda m: m.get("oracle_score", 0),
        reverse=True,
    )

    return ranked
'''

ranking_file.write_text(ranking_code, encoding="utf-8")

print("[OK] Created oracle_opportunity_ranking.py")

text = engine_file.read_text(encoding="utf-8")

backup = root / "oracle_research_engine.py.oracle033_backup"
backup.write_text(text, encoding="utf-8")

if "from oracle_opportunity_ranking import rank_markets" not in text:
    text = (
        "from oracle_opportunity_ranking import rank_markets\n"
        + text
    )

old = '''
        cache_count = oracle_market_cache.market_count()

        with self.lock:
            self.snapshot["status"] = "running"
            self.snapshot["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.snapshot["markets_checked"] = cache_count
            self.snapshot["provider_results"] = provider_results
            self.snapshot["errors"] = (self.snapshot.get("errors", []) + provider_errors)[-10:]
            self.snapshot["opportunities"] = self.snapshot.get("opportunities", [])
'''

new = '''
        ranked = rank_markets(
            oracle_market_cache.get_all()
        )

        cache_count = oracle_market_cache.market_count()

        with self.lock:
            self.snapshot["status"] = "running"
            self.snapshot["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.snapshot["markets_checked"] = cache_count
            self.snapshot["provider_results"] = provider_results
            self.snapshot["errors"] = (self.snapshot.get("errors", []) + provider_errors)[-10:]
            self.snapshot["opportunities"] = ranked[:25]
'''

if old in text:
    text = text.replace(old, new)

engine_file.write_text(text, encoding="utf-8")

print("[DONE] ORACLE-033 Opportunity Ranking Engine installed")