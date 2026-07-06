from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_consensus_engine.py")

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-046.0.3 Consensus Signal Adapter
# ============================================================

def _oracle04603_num(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _oracle04603_text(value):
    return str(value or "").strip()


def _oracle04603_direction_from_ranked(item):
    side = _oracle04603_text(item.get("side")).upper()
    grade = _oracle04603_text(item.get("grade")).upper()
    rec = _oracle04603_text(item.get("recommendation") or item.get("raw", {}).get("recommendation"))
    raw_rec = _oracle04603_text(item.get("raw", {}).get("raw", {}).get("recommendation"))
    combined = f"{side} {grade} {rec} {raw_rec}".lower()

    if "buy yes" in combined or side == "YES":
        return "BUY YES"
    if "buy no" in combined or side == "NO":
        return "BUY NO"
    if "pass" in combined or grade == "PASS":
        return "PASS"
    if "investigate" in combined or "relative value" in combined or "underpriced" in combined:
        return "WATCH"
    return "WATCH"


def _oracle04603_grade_confidence(grade, score):
    grade = _oracle04603_text(grade).upper()
    score = _oracle04603_num(score, 50)

    if grade == "A+":
        return 94
    if grade == "A":
        return 88
    if grade == "A-":
        return 82
    if grade == "B+":
        return 74
    if grade == "B":
        return 66
    if grade == "C":
        return 52
    if grade == "PASS":
        return max(35, min(58, score))
    return max(35, min(90, score))


def _oracle04603_edge_quality(edge, edge_pct=None):
    edge = abs(_oracle04603_num(edge, 0))
    ep = abs(_oracle04603_num(edge_pct, edge * 100))

    if ep >= 75:
        return 92
    if ep >= 50:
        return 86
    if ep >= 25:
        return 78
    if ep >= 10:
        return 66
    if ep >= 3:
        return 54
    return 38


def _oracle04603_build_adapted_opportunity(item):
    if not isinstance(item, dict):
        return item

    raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}
    raw_raw = raw.get("raw") if isinstance(raw.get("raw"), dict) else {}

    ticker = item.get("ticker") or raw.get("ticker") or raw_raw.get("ticker")
    title = item.get("title") or raw.get("title") or raw_raw.get("title")

    overall_score = _oracle04603_num(item.get("overall_score"), 50)
    adaptive_score = _oracle04603_num(item.get("adaptive_score"), overall_score)
    base_conf = _oracle04603_num(item.get("confidence") or raw.get("confidence") or raw_raw.get("confidence"), 50)
    edge = _oracle04603_num(item.get("edge") or raw.get("edge") or raw_raw.get("edge"), 0)
    edge_pct = _oracle04603_num(raw_raw.get("edge_pct"), edge * 100)
    grade = item.get("grade", "PASS")
    risk = _oracle04603_text(item.get("risk", "UNKNOWN")).upper()
    reason = item.get("reason") or raw.get("reason") or raw_raw.get("reason") or ""
    recommendation = raw.get("recommendation") or raw_raw.get("recommendation") or item.get("recommendation") or ""
    kind = raw_raw.get("kind") or raw.get("kind") or ""

    direction = _oracle04603_direction_from_ranked(item)

    edge_quality = _oracle04603_edge_quality(edge, edge_pct)
    grade_conf = _oracle04603_grade_confidence(grade, adaptive_score)

    risk_penalty = 0
    if risk == "HIGH":
        risk_penalty = 18
    elif risk == "MEDIUM":
        risk_penalty = 8
    elif risk == "LOW":
        risk_penalty = 0

    # If ranking already says PASS, make final fusion more cautious.
    fusion_direction = direction
    if _oracle04603_text(grade).upper() == "PASS":
        fusion_direction = "PASS" if adaptive_score < 55 else "WATCH"

    adapted = dict(item)

    adapted["market_intelligence"] = {
        "recommendation": direction if adaptive_score >= 58 else "WATCH",
        "confidence": max(35, min(95, adaptive_score)),
        "reason": f"Market intelligence score {overall_score:.2f}, adaptive score {adaptive_score:.2f}.",
    }

    adapted["evidence"] = {
        "recommendation": "WATCH" if base_conf >= 70 else "PASS",
        "confidence": max(35, min(95, base_conf)),
        "reason": f"Evidence confidence from opportunity confidence: {base_conf:.2f}.",
    }

    adapted["historical_similarity"] = {
        "recommendation": "WATCH",
        "confidence": 50,
        "reason": "Historical similarity vote is neutral until real matched analog outcomes are attached.",
    }

    adapted["learning_engine"] = {
        "recommendation": "WATCH" if item.get("learning_multiplier", 1.0) >= 1 else "PASS",
        "confidence": max(35, min(80, adaptive_score)),
        "reason": item.get("learning_note", "Learning engine neutral adjustment."),
    }

    adapted["final_fusion"] = {
        "recommendation": fusion_direction,
        "confidence": max(35, min(95, grade_conf - risk_penalty)),
        "reason": f"Final fusion derived from grade={grade}, risk={risk}, adaptive_score={adaptive_score:.2f}.",
    }

    adapted["arbitrage"] = {
        "recommendation": recommendation or direction,
        "confidence": max(35, min(98, edge_quality)),
        "reason": reason or f"Arbitrage kind={kind}, edge_pct={edge_pct:.2f}.",
        "kind": kind,
        "edge_pct": edge_pct,
    }

    adapted["research"] = {
        "recommendation": "WATCH" if recommendation else "PASS",
        "confidence": max(35, min(80, (base_conf * 0.55) + (adaptive_score * 0.45))),
        "reason": recommendation or reason or "No research recommendation attached.",
    }

    adapted["ranking"] = {
        "recommendation": fusion_direction,
        "confidence": max(35, min(95, adaptive_score)),
        "reason": f"Opportunity Ranking score={overall_score:.2f}, adaptive_score={adaptive_score:.2f}, grade={grade}.",
    }

    adapted["historical_memory"] = {
        "recommendation": "WATCH",
        "confidence": 25,
        "reason": "Historical Memory placeholder active; no stored memory vote yet.",
    }

    adapted["ticker"] = ticker
    adapted["title"] = title

    return adapted


if "OracleConsensusEngine" in globals():
    _oracle04603_original_calculate_consensus = OracleConsensusEngine.calculate_consensus

    def _oracle04603_calculate_consensus(self, opportunity):
        adapted = _oracle04603_build_adapted_opportunity(opportunity)
        result = _oracle04603_original_calculate_consensus(self, adapted)

        if isinstance(result, dict):
            result["adapter"] = {
                "version": "ORACLE-046.0.3",
                "status": "applied",
                "source_shape": "ranked_opportunity",
            }

        return result

    OracleConsensusEngine.calculate_consensus = _oracle04603_calculate_consensus

# ============================================================
# END ORACLE-046.0.3
# ============================================================
'''


def backup(path):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle046_0_3_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-046.0.3 INSTALLER")
    print(" Consensus Signal Adapter")
    print("===================================")

    if not TARGET.exists():
        raise FileNotFoundError("oracle_consensus_engine.py not found")

    text = TARGET.read_text(encoding="utf-8", errors="ignore")

    if "ORACLE-046.0.3 Consensus Signal Adapter" in text:
        print("[SKIP] ORACLE-046.0.3 already installed")
        return

    b = backup(TARGET)

    if 'if __name__ == "__main__":' in text:
        text = text.replace('if __name__ == "__main__":', PATCH_BLOCK + '\n\nif __name__ == "__main__":', 1)
    else:
        text += "\n\n" + PATCH_BLOCK + "\n"

    TARGET.write_text(text, encoding="utf-8")

    print(f"[OK] Patched {TARGET}")
    print(f"[OK] Backup created: {b}")
    print("")
    print("Tests:")
    print(" python oracle_consensus_engine.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); import pprint; c=o.status().get('last_ranked',[{}])[0].get('consensus'); pprint.pp({k:c.get(k) for k in ['final_recommendation','consensus_confidence','consensus_strength','direction_counts','weighted_direction_scores','adapter']})\"")
    print("")
    print("[DONE] ORACLE-046.0.3 installed")


if __name__ == "__main__":
    main()