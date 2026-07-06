from pathlib import Path
from datetime import datetime

path = Path("oracle_cross_market_arbitrage.py")

if not path.exists():
    raise FileNotFoundError("oracle_cross_market_arbitrage.py not found.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

insert = r'''

def is_candidate_set_market(m):
    """
    True when markets are different candidates/options in the same event,
    not a time ladder.
    """
    blob = " ".join([
        str(m.get("title") or ""),
        str(m.get("event_title") or ""),
        str(m.get("ticker") or ""),
    ]).lower()

    phrases = [
        "who will",
        "which ",
        "next prime minister",
        "next speaker",
        "next ceo",
        "first to leave office",
        "ipo first",
        "host for",
        "perform as",
        "next james bond",
        "country will",
        "person will",
        "team will",
    ]

    return any(p in blob for p in phrases)


def is_true_time_ladder_group(items):
    """
    Time ladder groups should be same underlying event with different dates/deadlines.
    Candidate sets must be excluded.
    """
    if len(items) < 2:
        return False

    if any(is_candidate_set_market(m) for m in items):
        return False

    years = [extract_year(m) for m in items if extract_year(m) is not None]
    if len(set(years)) < 2:
        return False

    blob = " ".join(
        (str(m.get("title") or "") + " " + str(m.get("event_title") or "")).lower()
        for m in items
    )

    ladder_terms = [
        "before",
        "by ",
        "through",
        "end of",
        "on or before",
        "at least",
        "above",
        "below",
        "over",
        "under",
    ]

    return any(term in blob for term in ladder_terms)

'''

if "def is_true_time_ladder_group(items):" not in text:
    marker = "\ndef alert(kind, title, markets, edge, confidence, recommendation, reason):"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find insertion point before alert().")
    text = text[:idx] + insert + text[idx:]

old = '''    for key, items in groups.items():
        if len(items) < 2:
            continue

        items = sorted(items, key=lambda x: extract_year(x) or 9999)
'''

new = '''    for key, items in groups.items():
        if len(items) < 2:
            continue

        if not is_true_time_ladder_group(items):
            continue

        items = sorted(items, key=lambda x: extract_year(x) or 9999)
'''

if old not in text:
    raise RuntimeError("Could not find time ladder group loop.")

text = text.replace(old, new)

# Make mutually exclusive formatting clearer.
text = text.replace(
    '''recommendation="Avoid buying YES basket; look for overpriced YES or cheap NO legs",''',
    '''recommendation="Mutually exclusive set appears overpriced; investigate NO on overpriced legs",'''
)

text = text.replace(
    '''recommendation="YES basket may be underpriced if all outcomes are represented",''',
    '''recommendation="Mutually exclusive set appears underpriced; investigate YES basket only if all outcomes are represented",'''
)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-045.1 INSTALLED")
print(" Arbitrage False Positive Filter")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python oracle_cross_market_arbitrage.py")