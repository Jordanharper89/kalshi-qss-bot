from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_consensus_engine.py")

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-046.0.4 Consensus Recommendation Calibration
# ============================================================

def _oracle04604_calibrated_direction_value(self, direction):
    """
    Calibrated vote power.

    Old issue:
    PASS returned 0.0, so PASS votes appeared in direction_counts
    but had no weighted power.

    New behavior:
    BUY YES = positive directional conviction
    BUY NO  = negative directional conviction
    WATCH   = neutral-but-actionable monitoring conviction
    PASS    = defensive rejection conviction
    """
    direction = str(direction or "").upper().strip()

    if direction == "BUY YES":
        return 1.0
    if direction == "BUY NO":
        return -1.0
    if direction == "WATCH":
        return 0.35
    if direction == "PASS":
        return 0.70

    return 0.20


def _oracle04604_recommendation_overlay(result):
    if not isinstance(result, dict):
        return result

    scores = result.get("weighted_direction_scores") or {}
    counts = result.get("direction_counts") or {}

    buy_yes = float(scores.get("BUY YES", 0) or 0)
    buy_no = float(scores.get("BUY NO", 0) or 0)
    watch = float(scores.get("WATCH", 0) or 0)
    passed = float(scores.get("PASS", 0) or 0)

    confidence = float(result.get("consensus_confidence", 0) or 0)
    weighted_agreement = float(result.get("weighted_agreement", 0) or 0)

    original = result.get("final_recommendation", "WATCH")

    # Defensive override: if PASS is strongest, do not allow fake strong WATCH.
    if passed > max(watch, buy_yes, buy_no):
        if confidence >= 60:
            result["final_recommendation"] = "PASS"
        else:
            result["final_recommendation"] = "WATCH"

    # Watch override: if WATCH is strongest but PASS is close, downgrade confidence.
    elif watch >= max(buy_yes, buy_no) and passed >= watch * 0.55:
        result["final_recommendation"] = "WATCH"
        result["consensus_strength"] = "CAUTIOUS WATCH"

    # Directional buy gates.
    elif buy_yes > max(watch, passed, buy_no):
        if confidence >= 72 and weighted_agreement >= 60:
            result["final_recommendation"] = "BUY YES"
        elif confidence >= 58:
            result["final_recommendation"] = "WATCH"
        else:
            result["final_recommendation"] = "PASS"

    elif buy_no > max(watch, passed, buy_yes):
        if confidence >= 72 and weighted_agreement >= 60:
            result["final_recommendation"] = "BUY NO"
        elif confidence >= 58:
            result["final_recommendation"] = "WATCH"
        else:
            result["final_recommendation"] = "PASS"

    result["calibration"] = {
        "version": "ORACLE-046.0.4",
        "status": "applied",
        "original_recommendation": original,
        "calibrated_recommendation": result.get("final_recommendation"),
        "pass_power": round(passed, 2),
        "watch_power": round(watch, 2),
        "buy_yes_power": round(buy_yes, 2),
        "buy_no_power": round(buy_no, 2),
        "direction_counts": counts,
    }

    return result


if "OracleConsensusEngine" in globals():
    OracleConsensusEngine._direction_value = _oracle04604_calibrated_direction_value

    if "_oracle04604_original_calculate_consensus" not in globals():
        _oracle04604_original_calculate_consensus = OracleConsensusEngine.calculate_consensus

        def _oracle04604_calculate_consensus(self, opportunity):
            result = _oracle04604_original_calculate_consensus(self, opportunity)
            return _oracle04604_recommendation_overlay(result)

        OracleConsensusEngine.calculate_consensus = _oracle04604_calculate_consensus

# ============================================================
# END ORACLE-046.0.4
# ============================================================
'''


def backup(path):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle046_0_4_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-046.0.4 INSTALLER")
    print(" Consensus Recommendation Calibration")
    print("===================================")

    if not TARGET.exists():
        raise FileNotFoundError("oracle_consensus_engine.py not found")

    text = TARGET.read_text(encoding="utf-8", errors="ignore")

    if "ORACLE-046.0.4 Consensus Recommendation Calibration" in text:
        print("[SKIP] ORACLE-046.0.4 already installed")
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
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); import pprint; c=o.status().get('last_ranked',[{}])[0].get('consensus'); pprint.pp({k:c.get(k) for k in ['final_recommendation','consensus_confidence','consensus_strength','direction_counts','weighted_direction_scores','adapter','calibration']})\"")
    print("")
    print("[DONE] ORACLE-046.0.4 installed")


if __name__ == "__main__":
    main()