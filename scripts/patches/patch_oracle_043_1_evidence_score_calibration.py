from pathlib import Path
from datetime import datetime

path = Path("oracle_evidence_fusion.py")

if not path.exists():
    raise FileNotFoundError("oracle_evidence_fusion.py not found.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

old = '''    evidence_score = clamp(50 + net, 0, 100)

    rec = recommendation_from_evidence(evidence_score, card)
    grade = grade_from_evidence(evidence_score, rec, confidence(card))
'''

new = '''    evidence_score = clamp(50 + net, 0, 100)

    # ORACLE-043.1 calibration:
    # A card should not get elite evidence scoring unless the edge is real.
    e_abs = abs(edge(card))
    c_val = confidence(card)

    if e_abs < 0.02:
        evidence_score = min(evidence_score, 72)
    elif e_abs < 0.035:
        evidence_score = min(evidence_score, 82)
    elif e_abs < 0.05:
        evidence_score = min(evidence_score, 90)

    if c_val < 65:
        evidence_score = min(evidence_score, 62)
    elif c_val < 74:
        evidence_score = min(evidence_score, 76)

    rec = recommendation_from_evidence(evidence_score, card)

    if rec in ("PASS", "WATCH"):
        evidence_score = min(evidence_score, 84)

    grade = grade_from_evidence(evidence_score, rec, confidence(card))
'''

if old not in text:
    raise RuntimeError("Could not find evidence_score block.")

text = text.replace(old, new)

old2 = '''    if price <= 0.02 or price >= 0.98:
        negative.append(evidence_item("Extreme price risk", -10, f"Market price is {price}.", "negative"))
'''

new2 = '''    if price <= 0.02 or price >= 0.98:
        negative.append(evidence_item("Extreme price risk", -14, f"Market price is {price}.", "negative"))
    elif price <= 0.05 or price >= 0.95:
        negative.append(evidence_item("Near-extreme price risk", -7, f"Market price is {price}.", "negative"))
'''

if old2 in text:
    text = text.replace(old2, new2)

old3 = '''    if any(year in close_time for year in ["2035", "2040", "2045", "2099"]):
        negative.append(evidence_item("Long-dated market risk", -12, f"Market closes far in the future: {close_time}.", "negative"))
    elif any(year in close_time for year in ["2030", "2031"]):
        negative.append(evidence_item("Moderately long-dated market", -6, f"Market closes in {close_time}.", "negative"))
'''

new3 = '''    if any(year in close_time for year in ["2035", "2040", "2045", "2099"]):
        negative.append(evidence_item("Long-dated market risk", -18, f"Market closes far in the future: {close_time}.", "negative"))
    elif any(year in close_time for year in ["2030", "2031"]):
        negative.append(evidence_item("Moderately long-dated market", -9, f"Market closes in {close_time}.", "negative"))
'''

if old3 in text:
    text = text.replace(old3, new3)

old4 = '''def recommendation_from_evidence(net_points, card):
    e = edge(card)
    c = confidence(card)

    if net_points >= 65 and c >= 82 and abs(e) >= 0.06:
        return "BUY YES" if e > 0 else "BUY NO"

    if net_points >= 48 and c >= 74 and abs(e) >= 0.035:
        return "LEAN YES" if e > 0 else "LEAN NO"

    if net_points >= 35:
        return "WATCH"

    return "PASS"
'''

new4 = '''def recommendation_from_evidence(net_points, card):
    e = edge(card)
    c = confidence(card)

    if net_points >= 72 and c >= 84 and abs(e) >= 0.07:
        return "BUY YES" if e > 0 else "BUY NO"

    if net_points >= 58 and c >= 76 and abs(e) >= 0.04:
        return "LEAN YES" if e > 0 else "LEAN NO"

    if net_points >= 45:
        return "WATCH"

    return "PASS"
'''

if old4 not in text:
    raise RuntimeError("Could not find recommendation_from_evidence block.")

text = text.replace(old4, new4)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-043.1 INSTALLED")
print(" Evidence Score Calibration")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python oracle_evidence_fusion.py")
print(" python oracle_final_fusion.py")