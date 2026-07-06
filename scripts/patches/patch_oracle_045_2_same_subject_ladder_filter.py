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

def subject_key(m):
    """
    Extract a rough same-subject key.
    Time ladders should compare same subject across different deadlines,
    not different candidates/people/teams.
    """
    raw = m.get("raw", {}) if isinstance(m.get("raw"), dict) else {}
    custom = raw.get("custom_strike", {}) if isinstance(raw.get("custom_strike"), dict) else {}

    subject_parts = []

    for key in [
        "Company",
        "Person",
        "Individual",
        "Artist",
        "Team",
        "Country",
        "City",
        "State",
        "golf_competitor",
    ]:
        if custom.get(key):
            subject_parts.append(str(custom.get(key)).lower())

    if subject_parts:
        return "|".join(subject_parts)

    title = str(m.get("title") or "").lower()
    title = re.sub(r"before\s+[a-z]{3,9}\s+\d{1,2},?\s+\d{4}", "before DATE", title)
    title = re.sub(r"before\s+\d{4}", "before YEAR", title)
    title = re.sub(r"\d{4}", "YEAR", title)
    title = re.sub(r"\d{1,2}[:/.-]\d{1,2}[:/.-]?\d*", "DATE", title)
    title = re.sub(r"\s+", " ", title).strip()

    return title


def same_subject(a, b):
    return subject_key(a) == subject_key(b)

'''

if "def subject_key(m):" not in text:
    marker = "\ndef alert(kind, title, markets, edge, confidence, recommendation, reason):"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find insertion point before alert().")
    text = text[:idx] + insert + text[idx:]

old = '''            y1 = yes_mid(early)
            y2 = yes_mid(later)

            if y1 <= 0 or y2 <= 0:
                continue

            violation = y1 - y2
'''

new = '''            if not same_subject(early, later):
                continue

            y1 = yes_mid(early)
            y2 = yes_mid(later)

            if y1 <= 0 or y2 <= 0:
                continue

            violation = y1 - y2
'''

if old not in text:
    raise RuntimeError("Could not find ladder comparison block.")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-045.2 INSTALLED")
print(" Same-Subject Ladder Filter")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python oracle_cross_market_arbitrage.py")