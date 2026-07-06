from pathlib import Path
from datetime import datetime

path = Path("oracle_market_intelligence.py")

if not path.exists():
    raise FileNotFoundError("oracle_market_intelligence.py not found.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

old = '''def recommendation_from_edge(edge, confidence):
    edge = safe_float(edge)
    confidence = safe_float(confidence)

    if confidence < 60:
        return "WATCH"

    if edge >= 0.06 and confidence >= 75:
        return "BUY YES"
    if edge <= -0.06 and confidence >= 75:
        return "BUY NO"

    if abs(edge) >= 0.03 and confidence >= 70:
        return "LEAN YES" if edge > 0 else "LEAN NO"

    return "PASS"


def grade_from_score(score):
    score = clamp(score)

    if score >= 92:
        return "A+"
    if score >= 88:
        return "A"
    if score >= 84:
        return "A-"
    if score >= 78:
        return "B+"
    if score >= 72:
        return "B"
    if score >= 66:
        return "B-"
    if score >= 58:
        return "C"
    return "PASS"
'''

new = '''def recommendation_from_edge(edge, confidence):
    edge = safe_float(edge)
    confidence = safe_float(confidence)

    # No action without enough confidence.
    if confidence < 65:
        return "WATCH"

    if edge >= 0.07 and confidence >= 80:
        return "BUY YES"
    if edge <= -0.07 and confidence >= 80:
        return "BUY NO"

    if edge >= 0.04 and confidence >= 72:
        return "LEAN YES"
    if edge <= -0.04 and confidence >= 72:
        return "LEAN NO"

    return "PASS"


def grade_from_score(score, recommendation="PASS", confidence=0, risk="HIGH"):
    score = clamp(score)
    recommendation = str(recommendation or "PASS").upper()
    risk = str(risk or "HIGH").upper()
    confidence = safe_float(confidence)

    # Hard cap non-actionable cards.
    if recommendation in ("PASS", "WATCH"):
        if score >= 72:
            score = 71.9

    # Hard cap weak confidence.
    if confidence < 65:
        score = min(score, 63.9)
    elif confidence < 72:
        score = min(score, 74.9)
    elif confidence < 80:
        score = min(score, 83.9)

    # Hard cap high risk.
    if risk == "HIGH":
        score = min(score, 74.9)

    # A grades require real actionability.
    if score >= 92 and recommendation in ("BUY YES", "BUY NO") and confidence >= 85 and risk != "HIGH":
        return "A+"
    if score >= 88 and recommendation in ("BUY YES", "BUY NO") and confidence >= 82 and risk != "HIGH":
        return "A"
    if score >= 84 and recommendation in ("BUY YES", "BUY NO", "LEAN YES", "LEAN NO") and confidence >= 78:
        return "A-"
    if score >= 78:
        return "B+"
    if score >= 72:
        return "B"
    if score >= 66:
        return "B-"
    if score >= 58:
        return "C"
    return "PASS"
'''

if old not in text:
    raise RuntimeError("Could not find recommendation/grade block.")

text = text.replace(old, new)

old2 = '''    opportunity_score = clamp(
        abs(edge) * 500
        + confidence * 0.35
        + research * 0.35
        + liquidity_score(market) * 0.20
        + price_quality_score(market) * 0.10
    )

    recommendation = recommendation_from_edge(edge, confidence)
    grade = grade_from_score(opportunity_score)
'''

new2 = '''    liq = liquidity_score(market)
    pxq = price_quality_score(market)

    risk = "LOW" if confidence >= 82 and liq >= 70 else "MEDIUM" if confidence >= 70 else "HIGH"

    # Calibrated opportunity score:
    # Edge helps, but cannot dominate weak confidence / high risk.
    opportunity_score = clamp(
        abs(edge) * 260
        + confidence * 0.30
        + research * 0.30
        + liq * 0.25
        + pxq * 0.15
    )

    # Penalize purely speculative long-dated markets.
    close_time = str(market.get("close_time") or market.get("expiration_time") or "")
    if any(year in close_time for year in ["2030", "2031", "2035", "2040", "2099"]):
        opportunity_score = min(opportunity_score, 76)

    recommendation = recommendation_from_edge(edge, confidence)
    grade = grade_from_score(opportunity_score, recommendation=recommendation, confidence=confidence, risk=risk)
'''

if old2 not in text:
    raise RuntimeError("Could not find opportunity_score block.")

text = text.replace(old2, new2)

text = text.replace(
    '''        "risk": "LOW" if confidence >= 80 else "MEDIUM" if confidence >= 65 else "HIGH",''',
    '''        "risk": risk,''',
)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-040.1 INSTALLED")
print(" Scoring Calibration")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python oracle_market_intelligence.py")