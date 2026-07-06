from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
POLICY = ROOT / "oracle_execution_policy.py"
GATEKEEPER = ROOT / "oracle_execution_gatekeeper.py"

POLICY_CODE = r'''
"""
ORACLE-047.1 Adaptive Execution Policy

Purpose:
- Central configurable policy layer for Execution Gatekeeper.
- Supports PAPER, AGGRESSIVE, NORMAL, CONSERVATIVE.
- Does NOT place trades.
"""

from datetime import datetime, UTC

DEFAULT_PROFILE = "NORMAL"

PROFILES = {
    "PAPER": {
        "min_execute_confidence": 55,
        "min_execute_adaptive_score": 45,
        "min_watch_confidence": 50,
        "allow_pass_grade": True,
        "allow_high_risk": False,
        "requires_strong_consensus": False,
        "description": "Paper/simulation mode. Allows weak ideas through for tracking only.",
    },
    "AGGRESSIVE": {
        "min_execute_confidence": 62,
        "min_execute_adaptive_score": 52,
        "min_watch_confidence": 52,
        "allow_pass_grade": False,
        "allow_high_risk": False,
        "requires_strong_consensus": False,
        "description": "More signals, more risk. Good for discovery and watchlist expansion.",
    },
    "NORMAL": {
        "min_execute_confidence": 74,
        "min_execute_adaptive_score": 60,
        "min_watch_confidence": 58,
        "allow_pass_grade": False,
        "allow_high_risk": False,
        "requires_strong_consensus": True,
        "description": "Balanced production profile.",
    },
    "CONSERVATIVE": {
        "min_execute_confidence": 82,
        "min_execute_adaptive_score": 72,
        "min_watch_confidence": 65,
        "allow_pass_grade": False,
        "allow_high_risk": False,
        "requires_strong_consensus": True,
        "description": "Strict mode. Fewer trades, higher confirmation requirements.",
    },
}


class OracleExecutionPolicy:
    def __init__(self):
        self.version = "ORACLE-047.1"
        self.active_profile = DEFAULT_PROFILE

    def set_profile(self, profile):
        profile = str(profile or "").upper().strip()
        if profile not in PROFILES:
            raise ValueError(f"Unknown execution profile: {profile}. Valid: {list(PROFILES.keys())}")
        self.active_profile = profile
        return self.get_active_policy()

    def get_active_policy(self):
        data = dict(PROFILES[self.active_profile])
        data["profile"] = self.active_profile
        data["module"] = "oracle_execution_policy"
        data["version"] = self.version
        data["timestamp"] = datetime.now(UTC).isoformat()
        return data

    def evaluate_thresholds(self, opportunity):
        policy = self.get_active_policy()

        consensus = opportunity.get("consensus") if isinstance(opportunity.get("consensus"), dict) else {}

        confidence = float(
            opportunity.get("consensus_confidence")
            or consensus.get("consensus_confidence")
            or 0
        )

        adaptive_score = float(
            opportunity.get("adaptive_score")
            or opportunity.get("overall_score")
            or 0
        )

        grade = str(opportunity.get("grade", "PASS")).upper().strip()
        risk = str(opportunity.get("risk", "UNKNOWN")).upper().strip()
        strength = str(
            opportunity.get("consensus_strength")
            or consensus.get("consensus_strength")
            or "UNKNOWN"
        ).upper().strip()

        checks = {
            "confidence_ok": confidence >= policy["min_execute_confidence"],
            "adaptive_score_ok": adaptive_score >= policy["min_execute_adaptive_score"],
            "watch_confidence_ok": confidence >= policy["min_watch_confidence"],
            "grade_ok": policy["allow_pass_grade"] or grade != "PASS",
            "risk_ok": policy["allow_high_risk"] or risk != "HIGH",
            "strength_ok": (not policy["requires_strong_consensus"]) or strength in ("STRONG", "VERY STRONG"),
        }

        checks["execute_ready"] = all([
            checks["confidence_ok"],
            checks["adaptive_score_ok"],
            checks["grade_ok"],
            checks["risk_ok"],
            checks["strength_ok"],
        ])

        checks["watch_ready"] = checks["watch_confidence_ok"] and checks["risk_ok"]

        return {
            "module": "oracle_execution_policy",
            "version": self.version,
            "status": "ok",
            "policy": policy,
            "checks": checks,
            "inputs": {
                "confidence": confidence,
                "adaptive_score": adaptive_score,
                "grade": grade,
                "risk": risk,
                "strength": strength,
            },
        }

    def diagnostics(self):
        return {
            "module": "oracle_execution_policy",
            "version": self.version,
            "status": "ok",
            "active_profile": self.active_profile,
            "available_profiles": list(PROFILES.keys()),
            "profiles": PROFILES,
        }


oracle_execution_policy = OracleExecutionPolicy()


if __name__ == "__main__":
    print(oracle_execution_policy.diagnostics())
'''

PATCH_BLOCK = r'''

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
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle047_1_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-047.1 INSTALLER")
    print(" Adaptive Execution Policy")
    print("===================================")

    backup(POLICY)
    POLICY.write_text(POLICY_CODE, encoding="utf-8")
    print("[OK] Created oracle_execution_policy.py")

    if not GATEKEEPER.exists():
        print("[WARN] oracle_execution_gatekeeper.py not found; overlay skipped")
    else:
        text = GATEKEEPER.read_text(encoding="utf-8", errors="ignore")
        if "ORACLE-047.1 Adaptive Execution Policy Overlay" in text:
            print("[SKIP] Gatekeeper already patched")
        else:
            b = backup(GATEKEEPER)
            if 'if __name__ == "__main__":' in text:
                text = text.replace('if __name__ == "__main__":', PATCH_BLOCK + "\n\nif __name__ == \"__main__\":", 1)
            else:
                text += "\n\n" + PATCH_BLOCK + "\n"
            GATEKEEPER.write_text(text, encoding="utf-8")
            print("[OK] Patched oracle_execution_gatekeeper.py")
            print(f"[OK] Backup created: {b}")

    print("")
    print("Tests:")
    print(" python oracle_execution_policy.py")
    print(" python -c \"from oracle_execution_policy import oracle_execution_policy as p; p.set_profile('PAPER'); print(p.get_active_policy())\"")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); top=s.get('last_ranked',[{}])[0]; print(top.get('execution_gate',{}).get('policy_profile')); print(top.get('execution_card'))\"")
    print("")
    print("[DONE] ORACLE-047.1 Adaptive Execution Policy installed")


if __name__ == "__main__":
    main()