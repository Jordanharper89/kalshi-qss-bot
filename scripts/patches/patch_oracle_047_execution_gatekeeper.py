from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
GATEKEEPER = ROOT / "oracle_execution_gatekeeper.py"
CONTINUOUS = ROOT / "oracle_continuous_intelligence.py"

GATEKEEPER_CODE = r'''
"""
ORACLE-047 Execution Gatekeeper

Purpose:
- Final safety gate before Q Series execution.
- Does NOT place trades.
- Converts Oracle Consensus + opportunity risk into:
  EXECUTE
  WATCH_ONLY
  BLOCK
  REQUIRES_REVIEW
"""

from datetime import datetime, UTC


def _num(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _txt(value):
    return str(value or "").strip()


class OracleExecutionGatekeeper:
    def __init__(self):
        self.version = "ORACLE-047"

    def evaluate(self, opportunity):
        if not isinstance(opportunity, dict):
            return self._decision("BLOCK", "Invalid opportunity object", opportunity)

        consensus = opportunity.get("consensus") or {}

        final = _txt(
            opportunity.get("consensus_final_recommendation")
            or consensus.get("final_recommendation")
            or "WATCH"
        ).upper()

        confidence = _num(
            opportunity.get("consensus_confidence")
            or consensus.get("consensus_confidence"),
            0,
        )

        strength = _txt(
            opportunity.get("consensus_strength")
            or consensus.get("consensus_strength")
            or "UNKNOWN"
        ).upper()

        grade = _txt(opportunity.get("grade", "PASS")).upper()
        risk = _txt(opportunity.get("risk", "UNKNOWN")).upper()
        edge = abs(_num(opportunity.get("edge"), 0))
        adaptive_score = _num(opportunity.get("adaptive_score", opportunity.get("overall_score")), 0)

        warnings = opportunity.get("warnings") or []
        if not isinstance(warnings, list):
            warnings = [str(warnings)]

        raw = opportunity.get("raw") if isinstance(opportunity.get("raw"), dict) else {}
        raw_raw = raw.get("raw") if isinstance(raw.get("raw"), dict) else {}
        kind = _txt(raw_raw.get("kind") or raw.get("kind"))

        reasons = []
        blockers = []

        if final == "PASS":
            blockers.append("Consensus final recommendation is PASS")

        if grade == "PASS":
            blockers.append("Opportunity ranking grade is PASS")

        if risk == "HIGH":
            blockers.append("Risk is HIGH")

        if confidence < 58:
            blockers.append(f"Consensus confidence too low: {confidence:.2f}%")

        if adaptive_score < 55:
            blockers.append(f"Adaptive score too low: {adaptive_score:.2f}")

        if edge <= 0:
            blockers.append("No positive edge detected")

        if any("liquidity" in str(w).lower() for w in warnings):
            reasons.append("Liquidity warning present")

        if kind in {
            "related_market_price_disagreement",
            "mutually_exclusive_underpriced",
        }:
            reasons.append(f"Arbitrage kind requires human verification: {kind}")

        if blockers:
            return self._decision(
                "BLOCK",
                "; ".join(blockers),
                opportunity,
                reasons=reasons,
                blockers=blockers,
            )

        if final in ("BUY YES", "BUY NO"):
            if confidence >= 74 and strength in ("STRONG", "VERY STRONG") and risk != "HIGH":
                return self._decision(
                    "EXECUTE",
                    f"Execution-grade consensus: {final}, confidence {confidence:.2f}%, strength {strength}",
                    opportunity,
                    reasons=reasons,
                )

            return self._decision(
                "REQUIRES_REVIEW",
                f"Directional signal exists but does not meet full auto-execution gate: {final}",
                opportunity,
                reasons=reasons,
            )

        if final == "WATCH":
            if confidence >= 62:
                return self._decision(
                    "WATCH_ONLY",
                    f"Consensus supports monitoring but not execution: confidence {confidence:.2f}%",
                    opportunity,
                    reasons=reasons,
                )

            return self._decision(
                "REQUIRES_REVIEW",
                f"Watch signal has weak confidence: {confidence:.2f}%",
                opportunity,
                reasons=reasons,
            )

        return self._decision(
            "REQUIRES_REVIEW",
            f"Unknown final recommendation: {final}",
            opportunity,
            reasons=reasons,
        )

    def _decision(self, action, reason, opportunity=None, reasons=None, blockers=None):
        opportunity = opportunity if isinstance(opportunity, dict) else {}
        consensus = opportunity.get("consensus") if isinstance(opportunity.get("consensus"), dict) else {}

        return {
            "module": "oracle_execution_gatekeeper",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "execution_decision": action,
            "action": action,
            "reason": reason,
            "reasons": reasons or [],
            "blockers": blockers or [],
            "ticker": opportunity.get("ticker"),
            "title": opportunity.get("title"),
            "consensus_final_recommendation": opportunity.get("consensus_final_recommendation") or consensus.get("final_recommendation"),
            "consensus_confidence": opportunity.get("consensus_confidence") or consensus.get("consensus_confidence"),
            "consensus_strength": opportunity.get("consensus_strength") or consensus.get("consensus_strength"),
            "grade": opportunity.get("grade"),
            "risk": opportunity.get("risk"),
            "edge": opportunity.get("edge"),
            "compact_card": self._format_card(action, reason, opportunity, reasons or [], blockers or []),
        }

    def _format_card(self, action, reason, opportunity, reasons, blockers):
        ticker = opportunity.get("ticker", "UNKNOWN")
        title = opportunity.get("title", "Untitled opportunity")

        lines = [
            "🛡️ ORACLE EXECUTION GATEKEEPER",
            f"Ticker: {ticker}",
            f"Market: {title}",
            "",
            f"Decision: {action}",
            f"Reason: {reason}",
        ]

        if blockers:
            lines.append("")
            lines.append("Blockers:")
            for b in blockers:
                lines.append(f"- {b}")

        if reasons:
            lines.append("")
            lines.append("Notes:")
            for r in reasons:
                lines.append(f"- {r}")

        return "\n".join(lines)

    def diagnostics(self):
        return {
            "module": "oracle_execution_gatekeeper",
            "version": self.version,
            "status": "ok",
            "decisions": ["EXECUTE", "WATCH_ONLY", "BLOCK", "REQUIRES_REVIEW"],
        }


oracle_execution_gatekeeper = OracleExecutionGatekeeper()


if __name__ == "__main__":
    sample = {
        "ticker": "TEST",
        "title": "Sample opportunity",
        "grade": "B+",
        "risk": "MEDIUM",
        "edge": 0.12,
        "adaptive_score": 68,
        "consensus": {
            "final_recommendation": "WATCH",
            "consensus_confidence": 67.21,
            "consensus_strength": "MODERATE",
        },
    }

    result = oracle_execution_gatekeeper.evaluate(sample)
    print(result["compact_card"])
    print(result)
'''


PATCH_BLOCK = r'''

# ============================================================
# ORACLE-047 Execution Gatekeeper Integration
# ============================================================

try:
    from oracle_execution_gatekeeper import oracle_execution_gatekeeper
except Exception:
    oracle_execution_gatekeeper = None


def _oracle047_apply_execution_gatekeeper(ranked):
    if oracle_execution_gatekeeper is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            gate = oracle_execution_gatekeeper.evaluate(item)
            item["execution_gate"] = gate
            item["execution_decision"] = gate.get("execution_decision")
            item["execution_reason"] = gate.get("reason")
            item["execution_card"] = gate.get("compact_card")
        except Exception as exc:
            item["execution_gate"] = {
                "status": "error",
                "execution_decision": "BLOCK",
                "reason": str(exc),
            }
            item["execution_decision"] = "BLOCK"
            item["execution_reason"] = str(exc)

        enriched.append(item)

    decision_rank = {
        "EXECUTE": 4,
        "REQUIRES_REVIEW": 3,
        "WATCH_ONLY": 2,
        "BLOCK": 1,
    }

    enriched.sort(
        key=lambda x: (
            decision_rank.get(x.get("execution_decision"), 0),
            x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0))),
        ) if isinstance(x, dict) else (0, 0),
        reverse=True,
    )

    return enriched


def _oracle047_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            if isinstance(_state.get("last_ranked"), list):
                _state["last_ranked"] = _oracle047_apply_execution_gatekeeper(_state["last_ranked"])

            ranked = _state.get("last_ranked") or []
            counts = {}
            for item in ranked:
                if isinstance(item, dict):
                    d = item.get("execution_decision", "UNKNOWN")
                    counts[d] = counts.get(d, 0) + 1

            _state["execution_gatekeeper_status"] = {
                "status": "ok" if oracle_execution_gatekeeper is not None else "missing",
                "decision_counts": counts,
                "top": ranked[:5],
            }
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["execution_gatekeeper_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle047_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle047_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle047_original_run_cycle(*args, **kwargs)
        _oracle047_enrich_state()
        return result


if "_oracle047_original_status" not in globals() and "status" in globals():
    _oracle047_original_status = status

    def status(*args, **kwargs):
        result = _oracle047_original_status(*args, **kwargs)
        _oracle047_enrich_state()

        if isinstance(result, dict):
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = _oracle047_apply_execution_gatekeeper(result["last_ranked"])

            if isinstance(result.get("pipeline_status"), dict):
                ps = result["pipeline_status"]
                if isinstance(ps.get("last_ranked"), list):
                    ps["last_ranked"] = _oracle047_apply_execution_gatekeeper(ps["last_ranked"])

            result["execution_gatekeeper_status"] = (
                globals().get("_state", {}).get("execution_gatekeeper_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )

        return result

# ============================================================
# END ORACLE-047
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle047_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-047 INSTALLER")
    print(" Execution Gatekeeper")
    print("===================================")

    backup(GATEKEEPER)
    GATEKEEPER.write_text(GATEKEEPER_CODE, encoding="utf-8")
    print("[OK] Created oracle_execution_gatekeeper.py")

    if not CONTINUOUS.exists():
        print("[WARN] oracle_continuous_intelligence.py not found; integration skipped")
    else:
        text = CONTINUOUS.read_text(encoding="utf-8", errors="ignore")
        if "ORACLE-047 Execution Gatekeeper Integration" in text:
            print("[SKIP] Continuous Intelligence already patched")
        else:
            b = backup(CONTINUOUS)
            marker = 'if __name__ == "__main__":'
            if marker in text:
                text = text.replace(marker, PATCH_BLOCK + "\n\n" + marker, 1)
            else:
                text += "\n\n" + PATCH_BLOCK + "\n"
            CONTINUOUS.write_text(text, encoding="utf-8")
            print(f"[OK] Patched oracle_continuous_intelligence.py")
            print(f"[OK] Backup created: {b}")

    print("")
    print("Tests:")
    print(" python oracle_execution_gatekeeper.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('execution_gatekeeper_status')); print(s.get('last_ranked',[{}])[0].get('execution_card'))\"")
    print("")
    print("[DONE] ORACLE-047 Execution Gatekeeper installed")


if __name__ == "__main__":
    main()