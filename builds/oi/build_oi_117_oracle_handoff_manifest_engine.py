from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_handoff_manifest_engine.py"
TEST = ROOT / "test_oi_117_oracle_handoff_manifest_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-117 Oracle Handoff Manifest Engine
Read-only Oracle Intelligence module.

Purpose:
- Create the final Oracle handoff manifest after OI-116 validation.
- Package validation status, handoff metadata, top handoff items, and Q Series visibility flags.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from datetime import datetime, timezone


class OracleHandoffManifestEngine:
    module = "oi_117_oracle_handoff_manifest_engine"

    def __init__(self):
        self.last_manifest = {}

    def build_manifest(self, handoff_packet=None, validation_report=None):
        handoff_packet = handoff_packet or {}
        validation_report = validation_report or {}

        handoff_items = [
            x for x in handoff_packet.get("handoff_items", [])
            if isinstance(x, dict)
        ]

        validation_status = str(validation_report.get("validation_status") or "unknown")
        validation_score = self._float(validation_report.get("validation_score"))
        ready = bool(validation_report.get("handoff_ready_for_q_series_visibility", False))

        manifest_items = []
        for item in handoff_items:
            manifest_items.append({
                "market": item.get("market"),
                "handoff_rank": int(self._float(item.get("handoff_rank"), 0)),
                "handoff_score": round(self._float(item.get("handoff_score")), 4),
                "handoff_tier": item.get("handoff_tier"),
                "digest_tier": item.get("digest_tier"),
                "support_tier": item.get("support_tier"),
                "review_conclusion": item.get("review_conclusion"),
                "oracle_observation": item.get("oracle_observation"),
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "read_only": True,
            })

        manifest_items.sort(key=lambda x: (x["handoff_rank"] if x["handoff_rank"] else 999999, -x["handoff_score"]))

        manifest_status = self._manifest_status(ready, validation_status, validation_score)

        manifest = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "input_modules": [
                "oi_115_oracle_intelligence_handoff_engine",
                "oi_116_oracle_handoff_validation_engine",
            ],
            "manifest_status": manifest_status,
            "q_series_visibility_ready": ready and manifest_status == "ready",
            "validation_status": validation_status,
            "validation_score": round(validation_score, 4),
            "handoff_score": round(self._float(handoff_packet.get("handoff_score")), 4),
            "handoff_posture": handoff_packet.get("handoff_posture"),
            "handoff_count": len(manifest_items),
            "manifest_items": manifest_items,
            "top_manifest_items": manifest_items[:10],
            "manifest_summary": self._summary(
                manifest_status=manifest_status,
                ready=ready,
                validation_report=validation_report,
                handoff_packet=handoff_packet,
                items=manifest_items,
            ),
            "oracle_boundaries": [
                "Oracle Intelligence is read-only.",
                "Oracle Intelligence does not execute.",
                "Oracle Intelligence does not approve execution.",
                "Q Series owns execution evaluation and execution decisions.",
            ],
        }

        self.last_manifest = manifest
        return manifest

    def _manifest_status(self, ready, validation_status, validation_score):
        if ready and validation_status == "validated" and validation_score >= 100:
            return "ready"
        if ready and validation_score >= 85:
            return "ready_with_warnings"
        if validation_score >= 65:
            return "review_required"
        return "blocked"

    def _summary(self, manifest_status, ready, validation_report, handoff_packet, items):
        top = items[0] if items else None
        failed = int(self._float(validation_report.get("failed_checks"), 0))

        if manifest_status == "ready":
            headline = "Oracle handoff manifest is ready for Q Series visibility."
        elif manifest_status == "ready_with_warnings":
            headline = "Oracle handoff manifest is visible with validation warnings."
        elif manifest_status == "review_required":
            headline = "Oracle handoff manifest requires review before Q Series visibility."
        else:
            headline = "Oracle handoff manifest is blocked."

        return {
            "headline": headline,
            "manifest_status": manifest_status,
            "q_series_visibility_ready": ready and manifest_status in {"ready", "ready_with_warnings"},
            "failed_checks": failed,
            "top_market": top.get("market") if top else None,
            "top_handoff_tier": top.get("handoff_tier") if top else None,
            "handoff_posture": handoff_packet.get("handoff_posture"),
            "execution_allowed": False,
            "execution_owner": "Q Series",
        }

    def _float(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_manifest": bool(self.last_manifest),
            "manifest_status": self.last_manifest.get("manifest_status"),
            "q_series_visibility_ready": self.last_manifest.get("q_series_visibility_ready", False),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_handoff_manifest_engine = OracleHandoffManifestEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_handoff_manifest_engine import oracle_handoff_manifest_engine


def test_oi_117_oracle_handoff_manifest_engine():
    handoff = {
        "handoff_score": 86.2,
        "handoff_posture": "urgent_handoff",
        "handoff_items": [
            {
                "market": "CRYPTO",
                "handoff_rank": 1,
                "handoff_score": 90.2,
                "handoff_tier": "critical",
                "digest_tier": "critical",
                "support_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "oracle_observation": "Keep market in elevated Oracle observation rotation.",
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "handoff_rank": 2,
                "handoff_score": 72.0,
                "handoff_tier": "high",
                "digest_tier": "elevated",
                "support_tier": "high",
                "review_conclusion": "confirmed_review",
                "oracle_observation": "Oracle review packet is ready for read-only downstream visibility.",
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    validation = {
        "validation_status": "validated",
        "validation_score": 100.0,
        "failed_checks": 0,
        "handoff_ready_for_q_series_visibility": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
    }

    manifest = oracle_handoff_manifest_engine.build_manifest(handoff, validation)

    assert manifest["status"] == "ok"
    assert manifest["read_only"] is True
    assert manifest["execution_allowed"] is False
    assert manifest["execution_owner"] == "Q Series"
    assert manifest["manifest_status"] == "ready"
    assert manifest["q_series_visibility_ready"] is True
    assert manifest["handoff_count"] == 2
    assert manifest["manifest_items"][0]["market"] == "CRYPTO"
    assert manifest["manifest_summary"]["execution_allowed"] is False

    diag = oracle_handoff_manifest_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["q_series_visibility_ready"] is True

    print("[PASS] OI-117 Oracle Handoff Manifest Engine")
    print({
        "manifest_status": manifest["manifest_status"],
        "ready": manifest["q_series_visibility_ready"],
        "summary": manifest["manifest_summary"],
        "top": manifest["manifest_items"][0],
    })


if __name__ == "__main__":
    test_oi_117_oracle_handoff_manifest_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_handoff_manifest_engine import oracle_handoff_manifest_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-117 INSTALLER")
print(" Oracle Handoff Manifest Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-117 installed")
print()
print("Run:")
print("py test_oi_117_oracle_handoff_manifest_engine.py")