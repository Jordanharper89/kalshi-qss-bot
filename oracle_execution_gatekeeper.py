
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




# ============================================================
# ORACLE-047.1 Adaptive Execution Policy Overlay
# ============================================================

try:
    from oracle_execution_policy import oracle_execution_policy
except Exception:
    oracle_execution_policy = None


if "OracleExecutionGatekeeper" in globals():
    if "_oracle0471_original_evaluate" not in globals():
        _oracle0471_original_evaluate = OracleExecutionGatekeeper.evaluate

        def _oracle0471_evaluate(self, opportunity):
            base = _oracle0471_original_evaluate(self, opportunity)

            if not isinstance(base, dict):
                return base

            if oracle_execution_policy is None:
                base["execution_policy"] = {
                    "status": "missing",
                    "profile": "LEGACY",
                }
                return base

            policy_result = oracle_execution_policy.evaluate_thresholds(opportunity)
            policy = policy_result.get("policy", {})
            checks = policy_result.get("checks", {})

            original_decision = base.get("execution_decision", "BLOCK")
            final = str(base.get("consensus_final_recommendation") or "").upper()

            calibrated_decision = original_decision
            calibration_reason = "Legacy gatekeeper decision preserved."

            if original_decision == "EXECUTE" and not checks.get("execute_ready"):
                calibrated_decision = "REQUIRES_REVIEW"
                calibration_reason = "Policy downgraded EXECUTE because one or more execution thresholds failed."

            elif original_decision in ("WATCH_ONLY", "REQUIRES_REVIEW"):
                if final in ("BUY YES", "BUY NO") and checks.get("execute_ready"):
                    calibrated_decision = "EXECUTE"
                    calibration_reason = "Policy upgraded directional signal to EXECUTE."
                elif checks.get("watch_ready"):
                    calibrated_decision = "WATCH_ONLY"
                    calibration_reason = "Policy allows this opportunity as WATCH_ONLY."
                else:
                    calibrated_decision = "BLOCK"
                    calibration_reason = "Policy blocked weak watch/review signal."

            elif original_decision == "BLOCK":
                if policy.get("profile") == "PAPER" and checks.get("watch_ready"):
                    calibrated_decision = "WATCH_ONLY"
                    calibration_reason = "PAPER profile converted BLOCK to WATCH_ONLY for tracking."
                else:
                    calibration_reason = "Policy preserved BLOCK."

            base["execution_policy"] = policy_result
            base["legacy_execution_decision"] = original_decision
            base["execution_decision"] = calibrated_decision
            base["action"] = calibrated_decision
            base["policy_profile"] = policy.get("profile", "UNKNOWN")
            base["policy_reason"] = calibration_reason

            base["compact_card"] = (
                base.get("compact_card", "")
                + "\n\nPolicy:"
                + f"\n- Profile: {policy.get('profile', 'UNKNOWN')}"
                + f"\n- Decision after policy: {calibrated_decision}"
                + f"\n- Policy reason: {calibration_reason}"
            )

            return base

        OracleExecutionGatekeeper.evaluate = _oracle0471_evaluate

# ============================================================
# END ORACLE-047.1
# ============================================================




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
