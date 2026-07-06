from pathlib import Path
from datetime import datetime

path = Path("oracle_market_intelligence.py")

if not path.exists():
    raise FileNotFoundError("oracle_market_intelligence.py not found.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

helper = r'''

def is_actionable_card(card):
    rec = str(card.get("recommendation") or "").upper()
    return rec in ("BUY YES", "BUY NO", "LEAN YES", "LEAN NO")


def get_actionable_intelligence(limit=10):
    if not INTELLIGENCE_FILE.exists():
        analyze_universe(top=50)

    data = json.loads(INTELLIGENCE_FILE.read_text(encoding="utf-8"))
    cards = data.get("cards", [])

    actionable = [c for c in cards if is_actionable_card(c)]
    watch = [c for c in cards if str(c.get("recommendation") or "").upper() == "WATCH"]

    ordered = actionable + watch

    return ordered[:int(limit)]

'''

if "def get_actionable_intelligence(limit=10):" not in text:
    marker = "\ndef format_card(card, rank=None):"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find insertion point before format_card.")
    text = text[:idx] + helper + text[idx:]

old = '''def get_top_intelligence(limit=10):
    if not INTELLIGENCE_FILE.exists():
        analyze_universe(top=limit)

    data = json.loads(INTELLIGENCE_FILE.read_text(encoding="utf-8"))
    return data.get("cards", [])[:int(limit)]
'''

new = '''def get_top_intelligence(limit=10):
    """
    ORACLE-040.3:
    Top intelligence means actionable first.
    PASS cards are hidden from Top 10.
    """
    return get_actionable_intelligence(limit=limit)
'''

if old not in text:
    raise RuntimeError("Could not find get_top_intelligence block.")

text = text.replace(old, new)

old_diag = '''            for c in payload.get("cards", [])[:5]
'''

new_diag = '''            for c in get_top_intelligence(limit=5)
'''

text = text.replace(old_diag, new_diag)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-040.3 INSTALLED")
print(" Actionable Top 10 Filter")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python oracle_market_intelligence.py")