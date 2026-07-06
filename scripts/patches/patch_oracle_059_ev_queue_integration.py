from pathlib import Path
from datetime import datetime
import shutil

QUEUE = Path("oracle_execution_queue_manager.py")
CONTINUOUS = Path("oracle_continuous_intelligence.py")

QUEUE_PATCH = r'''

# ============================================================
# ORACLE-059 EV Queue Calibration
# ============================================================

if "OracleExecutionQueueManager" in globals():
    if "_oracle059_original_queue_decision" not in globals():
        _oracle059_original_queue_decision = OracleExecutionQueueManager._queue_decision

        def _oracle059_queue_decision(self, c):
            base = _oracle059_original_queue_decision(self, c)
            if not isinstance(base, dict):
                return base

            ev_decision = str(c.get("ev_decision") or "").upper()
            ev_score = float(c.get("ev_score") or 0)

            original = base.get("decision", "REJECTED")
            decision = original
            reason = base.get("reason", "")
            flags = list(base.get("flags", []))
            score = float(base.get("score") or 0)

            if ev_decision == "NEGATIVE_EV":
                decision = "REJECTED"
                score = min(score, 15)
                flags.append("negative_ev_block")
                reason += " EV overlay rejected negative EV candidate."

            elif ev_decision == "WEAK_EV":
                if decision == "EXECUTION_READY":
                    decision = "REVIEW_REQUIRED"
                    flags.append("weak_ev_downgrade")
                    reason += " EV overlay downgraded execution-ready to review."
                score = min(score, 65)

            elif ev_decision == "WATCH_EV":
                if decision == "EXECUTION_READY" and ev_score < 10:
                    decision = "REVIEW_REQUIRED"
                    flags.append("watch_ev_review_required")
                    reason += " EV overlay requires review because EV is only WATCH_EV."

            elif ev_decision == "POSITIVE_EV":
                score = min(100, score + 8)
                flags.append("positive_ev_support")
                reason += " EV overlay supports queue priority."

            base["decision"] = decision
            base["score"] = round(max(0, min(100, score)), 2)
            base["reason"] = reason.strip()
            base["flags"] = flags
            base["ev_overlay"] = {
                "version": "ORACLE-059",
                "status": "applied",
                "ev_decision": ev_decision,
                "ev_score": ev_score,
                "original_queue_decision": original,
                "final_queue_decision": decision,
            }
            return base

        OracleExecutionQueueManager._queue_decision = _oracle059_queue_decision


if "OracleExecutionQueueManager" in globals():
    if "_oracle059_original_candidate" not in globals():
        _oracle059_original_candidate = OracleExecutionQueueManager._candidate

        def _oracle059_candidate(self, item, alert):
            c = _oracle059_original_candidate(self, item, alert)
            if isinstance(c, dict):
                c["ev_decision"] = str(item.get("ev_decision") or "").upper()
                c["ev_score"] = float(item.get("ev_score") or 0)
            return c

        OracleExecutionQueueManager._candidate = _oracle059_candidate

# ============================================================
# END ORACLE-059
# ============================================================
'''

CONTINUOUS_PATCH = r'''

# ============================================================
# ORACLE-059 EV Ranked Opportunity Calibration
# ============================================================

def _oracle059_apply_ev_rank_calibration(ranked):
    if not isinstance(ranked, list):
        return ranked

    ev_rank = {
        "POSITIVE_EV": 4,
        "WATCH_EV": 3,
        "WEAK_EV": 2,
        "NEGATIVE_EV": 1,
    }

    for item in ranked:
        if not isinstance(item, dict):
            continue

        ev_decision = str(item.get("ev_decision") or "").upper()
        ev_score = float(item.get("ev_score") or 0)
        queue_decision = str(item.get("queue_decision") or "").upper()

        item["ev_queue_overlay"] = {
            "version": "ORACLE-059",
            "status": "applied",
            "ev_decision": ev_decision,
            "ev_score": ev_score,
            "queue_decision": queue_decision,
        }

        if ev_decision == "NEGATIVE_EV":
            item["oracle_final_action"] = "AVOID"
        elif ev_decision == "WEAK_EV":
            item["oracle_final_action"] = "WATCH_ONLY"
        elif ev_decision == "WATCH_EV":
            item["oracle_final_action"] = "REVIEW"
        elif ev_decision == "POSITIVE_EV":
            item["oracle_final_action"] = "PRIORITY_REVIEW"
        else:
            item["oracle_final_action"] = "UNKNOWN"

    ranked.sort(
        key=lambda x: (
            ev_rank.get(str(x.get("ev_decision") or "").upper(), 0),
            x.get("ev_score", 0) or 0,
            x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0))),
        ) if isinstance(x, dict) else (0, 0, 0),
        reverse=True,
    )

    return ranked


def _oracle059_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            if isinstance(ranked, list):
                _state["last_ranked"] = _oracle059_apply_ev_rank_calibration(ranked)

                counts = {}
                for item in _state["last_ranked"]:
                    if isinstance(item, dict):
                        action = item.get("oracle_final_action", "UNKNOWN")
                        counts[action] = counts.get(action, 0) + 1

                _state["ev_queue_overlay_status"] = {
                    "status": "ok",
                    "version": "ORACLE-059",
                    "final_action_counts": counts,
                    "top": _state["last_ranked"][:5],
                }
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["ev_queue_overlay_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle059_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle059_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle059_original_run_cycle(*args, **kwargs)
        _oracle059_enrich_state()
        return result


if "_oracle059_original_status" not in globals() and "status" in globals():
    _oracle059_original_status = status

    def status(*args, **kwargs):
        result = _oracle059_original_status(*args, **kwargs)
        _oracle059_enrich_state()

        if isinstance(result, dict):
            result["ev_queue_overlay_status"] = (
                globals().get("_state", {}).get("ev_queue_overlay_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-059
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle059_{stamp}")
    shutil.copy2(path, b)
    return b


def patch_file(path, block, label):
    if not path.exists():
        print(f"[WARN] {path} not found; skipped {label}")
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
    print(" ORACLE-059 INSTALLER")
    print(" EV Queue Integration")
    print("===================================")

    patch_file(QUEUE, QUEUE_PATCH, "ORACLE-059 EV Queue Calibration")
    patch_file(CONTINUOUS, CONTINUOUS_PATCH, "ORACLE-059 EV Ranked Opportunity Calibration")

    print("")
    print("Tests:")
    print(" python oracle_execution_queue_manager.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('ev_queue_overlay_status')); print(s.get('last_ranked',[{}])[0].get('oracle_final_action')); print(s.get('execution_queue_status',{}).get('counts'))\"")
    print("")
    print("[DONE] ORACLE-059 EV Queue Integration installed")


if __name__ == "__main__":
    main()