from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_execution_gatekeeper.py")

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-048.1 Microstructure Gatekeeper Integration
# ============================================================

def _oracle0481_microstructure_overlay(base, opportunity):
    if not isinstance(base, dict) or not isinstance(opportunity, dict):
        return base

    micro = opportunity.get("microstructure") if isinstance(opportunity.get("microstructure"), dict) else {}

    tradability = str(
        opportunity.get("tradability")
        or micro.get("tradability")
        or "UNKNOWN"
    ).upper().strip()

    micro_score = float(
        opportunity.get("microstructure_score")
        or micro.get("microstructure_score")
        or micro.get("score")
        or 0
    )

    blockers = micro.get("blockers") or opportunity.get("microstructure_blockers") or []
    risks = micro.get("risks") or opportunity.get("microstructure_risks") or []

    if not isinstance(blockers, list):
        blockers = [str(blockers)]
    if not isinstance(risks, list):
        risks = [str(risks)]

    original_decision = base.get("execution_decision", "BLOCK")
    final_decision = original_decision
    micro_reason = "Microstructure did not change decision."

    if tradability == "UNTRADABLE":
        final_decision = "BLOCK"
        micro_reason = "Microstructure blocked opportunity as UNTRADABLE."

    elif tradability == "POOR":
        if original_decision == "EXECUTE":
            final_decision = "REQUIRES_REVIEW"
            micro_reason = "Microstructure downgraded EXECUTE to REQUIRES_REVIEW because tradability is POOR."
        elif original_decision in ("WATCH_ONLY", "REQUIRES_REVIEW"):
            final_decision = "WATCH_ONLY"
            micro_reason = "Microstructure allows monitoring only because tradability is POOR."
        else:
            final_decision = original_decision
            micro_reason = "Microstructure preserved BLOCK because tradability is POOR."

    elif tradability == "CAUTION":
        if original_decision == "EXECUTE" and micro_score < 65:
            final_decision = "REQUIRES_REVIEW"
            micro_reason = "Microstructure downgraded EXECUTE because CAUTION score is below 65."
        else:
            micro_reason = "Microstructure permits current decision with caution."

    elif tradability == "GOOD":
        micro_reason = "Microstructure supports current decision."

    else:
        if original_decision == "EXECUTE":
            final_decision = "REQUIRES_REVIEW"
            micro_reason = "Microstructure data missing/unknown; execution requires review."

    base["legacy_microstructure_decision"] = original_decision
    base["execution_decision"] = final_decision
    base["action"] = final_decision
    base["microstructure_gate"] = {
        "version": "ORACLE-048.1",
        "status": "applied",
        "tradability": tradability,
        "microstructure_score": micro_score,
        "original_decision": original_decision,
        "final_decision": final_decision,
        "reason": micro_reason,
        "blockers": blockers,
        "risks": risks,
    }

    base["compact_card"] = (
        base.get("compact_card", "")
        + "\n\nMicrostructure:"
        + f"\n- Tradability: {tradability}"
        + f"\n- Score: {micro_score}"
        + f"\n- Decision after microstructure: {final_decision}"
        + f"\n- Reason: {micro_reason}"
    )

    return base


if "OracleExecutionGatekeeper" in globals():
    if "_oracle0481_original_evaluate" not in globals():
        _oracle0481_original_evaluate = OracleExecutionGatekeeper.evaluate

        def _oracle0481_evaluate(self, opportunity):
            base = _oracle0481_original_evaluate(self, opportunity)
            return _oracle0481_microstructure_overlay(base, opportunity)

        OracleExecutionGatekeeper.evaluate = _oracle0481_evaluate

# ============================================================
# END ORACLE-048.1
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle048_1_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-048.1 INSTALLER")
    print(" Microstructure Gatekeeper Integration")
    print("===================================")

    if not TARGET.exists():
        raise FileNotFoundError("oracle_execution_gatekeeper.py not found")

    text = TARGET.read_text(encoding="utf-8", errors="ignore")

    if "ORACLE-048.1 Microstructure Gatekeeper Integration" in text:
        print("[SKIP] ORACLE-048.1 already installed")
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
    print(" python oracle_execution_gatekeeper.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); top=s.get('last_ranked',[{}])[0]; g=top.get('execution_gate',{}); print(g.get('execution_decision')); print(g.get('microstructure_gate')); print(top.get('execution_card'))\"")
    print("")
    print("[DONE] ORACLE-048.1 Microstructure Gatekeeper Integration installed")


if __name__ == "__main__":
    main()