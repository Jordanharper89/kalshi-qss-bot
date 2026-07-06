from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_execution_policy.py")

POLICY_CODE = r'''
"""
ORACLE-047.2 Persistent Execution Policy Config

Purpose:
- Persist active execution profile to oracle_execution_policy_config.json.
- Supports command line:
  python oracle_execution_policy.py status
  python oracle_execution_policy.py set PAPER
  python oracle_execution_policy.py set AGGRESSIVE
  python oracle_execution_policy.py set NORMAL
  python oracle_execution_policy.py set CONSERVATIVE
"""

from datetime import datetime, UTC
from pathlib import Path
import json
import sys

CONFIG_FILE = Path("oracle_execution_policy_config.json")
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
        self.version = "ORACLE-047.2"
        self.active_profile = self._load_profile()

    def _load_profile(self):
        try:
            if CONFIG_FILE.exists():
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                profile = str(data.get("active_profile", DEFAULT_PROFILE)).upper().strip()
                if profile in PROFILES:
                    return profile
        except Exception:
            pass
        return DEFAULT_PROFILE

    def _save_profile(self):
        data = {
            "module": "oracle_execution_policy",
            "version": self.version,
            "active_profile": self.active_profile,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    def set_profile(self, profile):
        profile = str(profile or "").upper().strip()
        if profile not in PROFILES:
            raise ValueError(f"Unknown execution profile: {profile}. Valid: {list(PROFILES.keys())}")
        self.active_profile = profile
        self._save_profile()
        return self.get_active_policy()

    def get_active_policy(self):
        self.active_profile = self._load_profile()
        data = dict(PROFILES[self.active_profile])
        data["profile"] = self.active_profile
        data["module"] = "oracle_execution_policy"
        data["version"] = self.version
        data["timestamp"] = datetime.now(UTC).isoformat()
        data["config_file"] = str(CONFIG_FILE)
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
            "active_profile": self._load_profile(),
            "available_profiles": list(PROFILES.keys()),
            "config_file": str(CONFIG_FILE),
            "config_exists": CONFIG_FILE.exists(),
            "profiles": PROFILES,
        }


oracle_execution_policy = OracleExecutionPolicy()


def _print_help():
    print("ORACLE-047.2 Execution Policy")
    print("")
    print("Commands:")
    print(" python oracle_execution_policy.py status")
    print(" python oracle_execution_policy.py set PAPER")
    print(" python oracle_execution_policy.py set AGGRESSIVE")
    print(" python oracle_execution_policy.py set NORMAL")
    print(" python oracle_execution_policy.py set CONSERVATIVE")


def main():
    args = [a.strip() for a in sys.argv[1:]]

    if not args or args[0].lower() in ("status", "diagnostics"):
        print(json.dumps(oracle_execution_policy.diagnostics(), indent=2))
        return

    if args[0].lower() == "set":
        if len(args) < 2:
            print("Missing profile name.")
            _print_help()
            raise SystemExit(1)

        policy = oracle_execution_policy.set_profile(args[1])
        print(json.dumps({
            "status": "ok",
            "message": f"Execution policy profile set to {policy['profile']}",
            "active_policy": policy,
        }, indent=2))
        return

    _print_help()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle047_2_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-047.2 INSTALLER")
    print(" Persistent Execution Policy Config")
    print("===================================")

    b = backup(TARGET)
    TARGET.write_text(POLICY_CODE, encoding="utf-8")

    print("[OK] Rebuilt oracle_execution_policy.py")
    if b:
        print(f"[OK] Backup created: {b}")

    print("")
    print("Tests:")
    print(" python oracle_execution_policy.py status")
    print(" python oracle_execution_policy.py set PAPER")
    print(" python oracle_execution_policy.py status")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); top=s.get('last_ranked',[{}])[0]; print(top.get('execution_gate',{}).get('policy_profile')); print(top.get('execution_card'))\"")
    print("")
    print("[DONE] ORACLE-047.2 Persistent Execution Policy installed")


if __name__ == "__main__":
    main()