from pathlib import Path
from datetime import datetime

path = Path("oracle_market_intelligence.py")

if not path.exists():
    raise FileNotFoundError("oracle_market_intelligence.py not found.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

# Fix classification priority: elections/politics before financial/IPO keywords.
old_class = '''    if any(x in blob for x in ["ipo", "stock", "shares", "nasdaq", "nyse", "sec", "earnings"]):
        domain = "financials"
        subtype = "ipo_or_equity"

    elif any(x in blob for x in ["cpi", "inflation", "fed", "interest rate", "jobs", "unemployment", "gdp"]):
        domain = "economics"
        subtype = "macro_release"

    elif any(x in blob for x in ["temperature", "snow", "rain", "hurricane", "storm", "weather"]):
        domain = "weather"
        subtype = "weather"

    elif any(x in blob for x in ["election", "president", "senate", "house", "parliament", "seat", "vote"]):
        domain = "elections"
        subtype = "politics"
'''

new_class = '''    if any(x in blob for x in ["election", "president", "prime minister", "senate", "house", "parliament", "seat", "vote", "mayor", "governor"]):
        domain = "elections"
        subtype = "politics"

    elif any(x in blob for x in ["ipo", "stock", "shares", "nasdaq", "nyse", "sec filing", "earnings"]):
        domain = "financials"
        subtype = "ipo_or_equity"

    elif any(x in blob for x in ["cpi", "inflation", "fed", "interest rate", "jobs", "unemployment", "gdp"]):
        domain = "economics"
        subtype = "macro_release"

    elif any(x in blob for x in ["temperature", "snow", "rain", "hurricane", "storm", "weather"]):
        domain = "weather"
        subtype = "weather"
'''

if old_class not in text:
    raise RuntimeError("Could not find classification block.")

text = text.replace(old_class, new_class)

helper = r'''

def actionability_rank_score(card):
    """
    ORACLE-040.2:
    Rank score prioritizes actionable cards over raw score.
    PASS/WATCH cannot outrank good LEAN/BUY cards just because raw score is high.
    """
    rec = str(card.get("recommendation") or "PASS").upper()
    risk = str(card.get("risk") or "HIGH").upper()

    raw_score = safe_float(card.get("opportunity_score"))
    confidence = safe_float(card.get("confidence"))
    research = safe_float(card.get("research_score"))
    edge_abs = abs(safe_float(card.get("edge")))

    rank = 0.0

    if rec in ("BUY YES", "BUY NO"):
        rank += 50
    elif rec in ("LEAN YES", "LEAN NO"):
        rank += 30
    elif rec == "WATCH":
        rank += 8
    else:
        rank += 0

    rank += raw_score * 0.35
    rank += confidence * 0.25
    rank += research * 0.20
    rank += min(edge_abs * 400, 20)

    if risk == "LOW":
        rank += 10
    elif risk == "MEDIUM":
        rank += 3
    else:
        rank -= 12

    if rec in ("PASS", "WATCH"):
        rank = min(rank, 59.9)

    return round(clamp(rank), 2)

'''

if "def actionability_rank_score(card):" not in text:
    marker = "\ndef analyze_market(market):"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find analyze_market insertion point.")
    text = text[:idx] + helper + text[idx:]

old_return_piece = '''        "opportunity_score": round(opportunity_score, 2),
        "grade": grade,
        "recommendation": recommendation,
'''

new_return_piece = '''        "opportunity_score": round(opportunity_score, 2),
        "grade": grade,
        "recommendation": recommendation,
'''

# Add rank_score after card creation by replacing whole return with temp card is too risky.
# Safer: inject rank_score after created_at key area.
old_created = '''        "created_at": now(),
    }
'''

new_created = '''        "created_at": now(),
    }

    card["rank_score"] = actionability_rank_score(card)
    return card
'''

old_analyze_end = '''        "raw_market": market,
        "created_at": now(),
    }
'''

if old_analyze_end not in text:
    raise RuntimeError("Could not find analyze_market return end block.")

text = text.replace(old_analyze_end, '''        "raw_market": market,
        "created_at": now(),
    }

    card["rank_score"] = actionability_rank_score(card)
    return card
''')

# The replacement above assumes return { ... } was present. Need convert "return {" to "card = {" in analyze_market.
old_start_return = '''    return {
        "ticker": market.get("ticker"),
'''

new_start_return = '''    card = {
        "ticker": market.get("ticker"),
'''

if old_start_return not in text:
    raise RuntimeError("Could not find analyze_market return start block.")

text = text.replace(old_start_return, new_start_return, 1)

old_sort = '''    cards.sort(
        key=lambda x: (
            x.get("opportunity_score", 0),
            abs(x.get("edge", 0)),
            x.get("confidence", 0),
        ),
        reverse=True,
    )
'''

new_sort = '''    cards.sort(
        key=lambda x: (
            x.get("rank_score", 0),
            x.get("opportunity_score", 0),
            abs(x.get("edge", 0)),
            x.get("confidence", 0),
        ),
        reverse=True,
    )
'''

if old_sort not in text:
    raise RuntimeError("Could not find cards.sort block.")

text = text.replace(old_sort, new_sort)

# Add rank score display.
if "Rank Score:" not in text:
    text = text.replace(
        '''Opportunity Score:
{card.get("opportunity_score")}''',
        '''Opportunity Score:
{card.get("opportunity_score")}

Rank Score:
{card.get("rank_score")}'''
    )

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-040.2 INSTALLED")
print(" Ranking Calibration")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python oracle_market_intelligence.py")