from pathlib import Path
from datetime import datetime
import shutil

CONTINUOUS = Path("oracle_continuous_intelligence.py")
FINAL_ROUTER = Path("oracle_final_decision_router.py")

FINAL_ROUTER_PATCH = r'''

# ============================================================
# ORACLE-070 Learning-Aware Final Router Overlay
# ============================================================

if "OracleFinalDecisionRouter" in globals():
    if "_oracle070_original_route" not in globals():
        _oracle070_original_route = OracleFinalDecisionRouter.route

        def _oracle070_route(self, item, market_regime=None):
            base = _oracle070_original_route(self, item, market_regime)

            if not isinstance(base, dict) or not isinstance(item, dict):
                return base

            learning = item.get("learning_adapter") if isinstance(item.get("learning_adapter"), dict) else {}

            adjusted_score = float(
                item.get("learning_adjusted_score")
                or learning.get("adjusted_score")
                or base.get("final_score")
                or 0
            )

            learning_conf = str(
                item.get("learning_confidence")
                or learning.get("learning_confidence")
                or "NONE"
            ).upper()

            boost = float(item.get("learning_boost") or learning.get("learning_boost") or 0)
            penalty = float(item.get("learning_penalty") or learning.get("learning_penalty") or 0)

            original_action = base.get("final_action", "NO_TRADE")
            final_action = original_action
            notes = list(base.get("notes", []))
            blockers = list(base.get("blockers", []))
            supports = list(base.get("supports", []))

            if learning_conf in ("HIGH", "MEDIUM"):
                if penalty >= 8 and original_action in ("READY_FOR_EXECUTION", "HUMAN_REVIEW"):
                    final_action = "HUMAN_REVIEW" if original_action == "READY_FOR_EXECUTION" else "WATCH"
                    blockers.append("Learning memory downgraded this pattern")

                elif boost >= 8 and original_action == "WATCH" and adjusted_score >= 65:
                    final_action = "HUMAN_REVIEW"
                    supports.append("Learning memory upgraded WATCH to HUMAN_REVIEW")

                elif boost >= 8 and original_action == "HUMAN_REVIEW" and adjusted_score >= 85:
                    final_action = "READY_FOR_EXECUTION"
                    supports.append("Learning memory supports execution-ready upgrade")
            else:
                notes.append("Learning memory sample size not strong enough for major decision change")

            base["pre_learning_final_action"] = original_action
            base["final_action"] = final_action
            base["oracle_final_action"] = final_action
            base["final_score"] = round(adjusted_score, 2)
            base["oracle_final_score"] = round(adjusted_score, 2)
            base["notes"] = notes
            base["blockers"] = blockers
            base["supports"] = supports
            base["learning_router_overlay"] = {
                "version": "ORACLE-070",
                "status": "applied",
                "learning_confidence": learning_conf,
                "learning_boost": boost,
                "learning_penalty": penalty,
                "original_action": original_action,
                "final_action": final_action,
                "adjusted_score": round(adjusted_score, 2),
            }

            base["compact_card"] = self._card(base, base.get("reason", ""))

            return base

        OracleFinalDecisionRouter.route = _oracle070_route

# ============================================================
# END ORACLE-070
# ============================================================
'''

CONTINUOUS_PATCH = r'''

# ============================================================
# ORACLE-070 Learning-Aware Final Action Integration
# ============================================================

def _oracle070_apply_learning_final_overlay(ranked):
    if not isinstance(ranked, list):
        return ranked

    action_rank = {
        "READY_FOR_EXECUTION": 4,
        "HUMAN_REVIEW": 3,
        "WATCH": 2,
        "NO_TRADE": 1,
    }

    for item in ranked:
        if not isinstance(item, dict):
            continue

        learning = item.get("learning_adapter") if isinstance(item.get("learning_adapter"), dict) else {}
        final = item.get("final_decision") if isinstance(item.get("final_decision"), dict) else {}

        item["learning_final_overlay"] = {
            "version": "ORACLE-070",
            "status": "applied",
            "learning_confidence": learning.get("learning_confidence"),
            "learning_boost": learning.get("learning_boost"),
            "learning_penalty": learning.get("learning_penalty"),
            "adjusted_score": learning.get("adjusted_score"),
            "final_action": item.get("oracle_final_action"),
        }

        # If final router already ran before learning adapter in the patch chain,
        # apply conservative post-processing here too.
        conf = str(learning.get("learning_confidence") or "NONE").upper()
        boost = float(learning.get("learning_boost") or 0)
        penalty = float(learning.get("learning_penalty") or 0)
        adjusted = float(learning.get("adjusted_score") or item.get("oracle_final_score") or 0)
        action = str(item.get("oracle_final_action") or "NO_TRADE").upper()

        if conf in ("HIGH", "MEDIUM"):
            if penalty >= 8 and action in ("READY_FOR_EXECUTION", "HUMAN_REVIEW"):
                action = "HUMAN_REVIEW" if action == "READY_FOR_EXECUTION" else "WATCH"
            elif boost >= 8 and action == "WATCH" and adjusted >= 65:
                action = "HUMAN_REVIEW"

        item["oracle_final_action"] = action
        item["oracle_final_score"] = round(adjusted, 2)

    ranked.sort(
        key=lambda x: (
            action_rank.get(str(x.get("oracle_final_action") or "").upper(), 0),
            x.get("oracle_final_score", 0) or 0,
            x.get("learning_adjusted_score", 0) or 0,
        ) if isinstance(x, dict) else (0, 0, 0),
        reverse=True,
    )

    return ranked


def _oracle070_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            if isinstance(ranked, list):
                _state["last_ranked"] = _oracle070_apply_learning_final_overlay(ranked)

                counts = {}
                for item in _state["last_ranked"]:
                    if isinstance(item, dict):
                        a = item.get("oracle_final_action", "UNKNOWN")
                        counts[a] = counts.get(a, 0) + 1

                _state["learning_final_router_status"] = {
                    "version": "ORACLE-070",
                    "status": "ok",
                    "action_counts": counts,
                    "top": _state["last_ranked"][:5],
                }
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["learning_final_router_status"] = {
                "version": "ORACLE-070",
                "status": "error",
                "error": str(exc),
            }


if "_oracle070_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle070_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle070_original_run_cycle(*args, **kwargs)
        _oracle070_enrich_state()
        return result


if "_oracle070_original_status" not in globals() and "status" in globals():
    _oracle070_original_status = status

    def status(*args, **kwargs):
        result = _oracle070_original_status(*args, **kwargs)
        _oracle070_enrich_state()

        if isinstance(result, dict):
            result["learning_final_router_status"] = (
                globals().get("_state", {}).get("learning_final_router_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-070
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle070_{stamp}")
    shutil.copy2(path, b)
    return b


def patch(path, block, label):
    if not path.exists():
        print(f"[WARN] {path} not found; skipped")
        return

    text = path.read_text(encoding="utf-8", errors="ignore")
    if label in text:
        print(f"[SKIP] {label} already installed")
        return

    b = backup(path)
    marker = 'if __name__ == "__main__":'
    if marker in text:
        text = text.replace(marker, block + "\n\n" + marker, 1)
    else:
        text += "\n\n" + block + "\n"

    path.write_text(text, encoding="utf-8")
    print(f"[OK] Patched {path}")
    print(f"[OK] Backup created: {b}")


def main():
    print("===================================")
    print(" ORACLE-070 INSTALLER")
    print(" Learning-Aware Final Router")
    print("===================================")

    patch(FINAL_ROUTER, FINAL_ROUTER_PATCH, "ORACLE-070 Learning-Aware Final Router Overlay")
    patch(CONTINUOUS, CONTINUOUS_PATCH, "ORACLE-070 Learning-Aware Final Action Integration")

    print("")
    print("Tests:")
    print(" python oracle_final_decision_router.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('learning_final_router_status')); print(s.get('last_ranked',[{}])[0].get('learning_final_overlay')); print(s.get('last_ranked',[{}])[0].get('oracle_final_action'))\"")
    print("")
    print("[DONE] ORACLE-070 Learning-Aware Final Router installed")


if __name__ == "__main__":
    main()