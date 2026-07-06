from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_qseries_transfer_record_engine.py"
TEST = ROOT / "test_oi_120_oracle_qseries_transfer_record_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-120 Oracle Q Series Transfer Record Engine
Read-only Oracle Intelligence module.

Purpose:
- Create a final read-only transfer record from Oracle Intelligence to Q Series.
- Combine intake packet + intake audit into a durable transfer summary.
- Confirm Oracle does not execute and Q Series owns execution decisions.
"""

from datetime import datetime, timezone


class OracleQSeriesTransferRecordEngine:
    module = "oi_120_oracle_qseries_transfer_record_engine"

    def __init__(self):
        self.last_record = {}

    def build_transfer_record(self, intake_packet=None, intake_audit=None):
        intake_packet = intake_packet or {}
        intake_audit = intake_audit or {}

        intake_items = [
            x for x in intake_packet.get("intake_items", [])
            if isinstance(x, dict)
        ]

        audit_passed = intake_audit.get("audit_status") == "passed"
        safe_to_view = bool(intake_audit.get("q_series_safe_to_view", False))
        intake_ready = intake_packet.get("intake_status") in {"ready", "ready_with_warnings"}

        transfer_items = []
        for item in intake_items:
            score = self._transfer_score(item, audit_passed, safe_to_view)
            transfer_items.append({
                "market": item.get("market"),
                "transfer_score": round(score, 4),
                "transfer_tier": self._tier(score),
                "intake_rank": int(self._float(item.get("intake_rank"), 0)),
                "intake_score": round(self._float(item.get("intake_score")), 4),
                "intake_tier": item.get("intake_tier"),
                "handoff_score": round(self._float(item.get("handoff_score")), 4),
                "handoff_tier": item.get("handoff_tier"),
                "review_conclusion": item.get("review_conclusion"),
                "oracle_observation": item.get("oracle_observation"),
                "q_series_visibility": bool(item.get("q_series_visibility")),
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
                "transfer_note": self._note(item, score, audit_passed, safe_to_view),
            })

        transfer_items.sort(
            key=lambda x: (
                -x["transfer_score"],
                x["intake_rank"] if x["intake_rank"] else 999999,
            )
        )

        for idx, item in enumerate(transfer_items, start=1):
            item["transfer_rank"] = idx

        transfer_ready = bool(audit_passed and safe_to_view and intake_ready)

        record = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "input_modules": [
                "oi_118_qseries_intake_packet_engine",
                "oi_119_qseries_intake_audit_engine",
            ],
            "transfer_status": self._transfer_status(transfer_ready, intake_packet, intake_audit),
            "transfer_ready": transfer_ready,
            "audit_status": intake_audit.get("audit_status"),
            "audit_score": round(self._float(intake_audit.get("audit_score")), 4),
            "intake_status": intake_packet.get("intake_status"),
            "q_series_safe_to_view": safe_to_view,
            "transfer_count": len(transfer_items),
            "transfer_items": transfer_items,
            "top_transfer_items": transfer_items[:10],
            "blocked_transfer_items": [x for x in transfer_items if not x["q_series_visibility"]],
            "transfer_summary": self._summary(
                transfer_ready=transfer_ready,
                transfer_items=transfer_items,
                intake_packet=intake_packet,
                intake_audit=intake_audit,
            ),
            "oracle_to_qseries_rules": [
                "Oracle Intelligence is read-only.",
                "Oracle provides visibility packets only.",
                "Oracle does not execute.",
                "Oracle does not approve execution.",
                "Q Series owns execution evaluation.",
                "Q Series owns execution decisions.",
            ],
        }

        self.last_record = record
        return record

    def _transfer_score(self, item, audit_passed, safe_to_view):
        base = self._float(item.get("intake_score"))
        audit_bonus = 5 if audit_passed else -25
        visibility_bonus = 5 if safe_to_view and item.get("q_series_visibility") else -25
        tier_bonus = {
            "critical": 6,
            "high": 4,
            "elevated": 2,
            "watch": 0,
            "blocked": -10,
        }.get(str(item.get("intake_tier") or ""), 0)

        score = base + audit_bonus + visibility_bonus + tier_bonus
        return max(0.0, min(100.0, score))

    def _tier(self, score):
        if score >= 85:
            return "critical"
        if score >= 70:
            return "high"
        if score >= 50:
            return "elevated"
        if score >= 30:
            return "watch"
        return "blocked"

    def _transfer_status(self, transfer_ready, intake_packet, intake_audit):
        if transfer_ready:
            return "ready_for_q_series_visibility"
        if intake_audit.get("audit_status") == "passed_with_warnings":
            return "ready_with_warnings"
        if intake_audit.get("audit_status") in {"needs_review", "failed"}:
            return "blocked_by_audit"
        if intake_packet.get("intake_status") not in {"ready", "ready_with_warnings"}:
            return "blocked_by_intake"
        return "blocked"

    def _note(self, item, score, audit_passed, safe_to_view):
        market = item.get("market")
        if not audit_passed:
            return f"{market} transfer blocked because intake audit did not pass."
        if not safe_to_view:
            return f"{market} transfer blocked because Q Series visibility is not safe."
        return (
            f"{market} transfer tier is {self._tier(score)}. "
            "Oracle record is read-only and visible to Q Series for evaluation only."
        )

    def _summary(self, transfer_ready, transfer_items, intake_packet, intake_audit):
        counts = {}
        for item in transfer_items:
            tier = item["transfer_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        top = transfer_items[0] if transfer_items else None

        if transfer_ready and top:
            headline = f"Oracle-to-Q-Series transfer is ready; top transfer market is {top['market']}."
        elif transfer_ready:
            headline = "Oracle-to-Q-Series transfer is ready with no market items."
        else:
            headline = "Oracle-to-Q-Series transfer is blocked pending audit or intake readiness."

        return {
            "headline": headline,
            "transfer_ready": transfer_ready,
            "transfer_tier_counts": counts,
            "top_market": top["market"] if top else None,
            "top_transfer_tier": top["transfer_tier"] if top else None,
            "intake_status": intake_packet.get("intake_status"),
            "audit_status": intake_audit.get("audit_status"),
            "audit_score": intake_audit.get("audit_score"),
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
            "has_record": bool(self.last_record),
            "transfer_ready": self.last_record.get("transfer_ready", False),
            "transfer_count": self.last_record.get("transfer_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_qseries_transfer_record_engine = OracleQSeriesTransferRecordEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_qseries_transfer_record_engine import oracle_qseries_transfer_record_engine


def test_oi_120_oracle_qseries_transfer_record_engine():
    intake_packet = {
        "status": "ok",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "q_series_visibility_ready": True,
        "intake_status": "ready",
        "intake_items": [
            {
                "market": "CRYPTO",
                "intake_score": 100.0,
                "intake_tier": "critical",
                "intake_rank": 1,
                "handoff_score": 90.2,
                "handoff_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "oracle_observation": "Keep market in elevated Oracle observation rotation.",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "intake_score": 81.0,
                "intake_tier": "high",
                "intake_rank": 2,
                "handoff_score": 72.0,
                "handoff_tier": "high",
                "review_conclusion": "confirmed_review",
                "oracle_observation": "Oracle review packet is ready for read-only downstream visibility.",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    intake_audit = {
        "audit_status": "passed",
        "audit_score": 100.0,
        "q_series_safe_to_view": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
    }

    record = oracle_qseries_transfer_record_engine.build_transfer_record(intake_packet, intake_audit)

    assert record["status"] == "ok"
    assert record["read_only"] is True
    assert record["execution_allowed"] is False
    assert record["execution_owner"] == "Q Series"
    assert record["transfer_ready"] is True
    assert record["transfer_status"] == "ready_for_q_series_visibility"
    assert record["transfer_count"] == 2
    assert record["transfer_items"][0]["transfer_rank"] == 1
    assert record["transfer_items"][0]["market"] == "CRYPTO"
    assert record["transfer_summary"]["execution_allowed"] is False

    diag = oracle_qseries_transfer_record_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["transfer_ready"] is True

    print("[PASS] OI-120 Oracle Q Series Transfer Record Engine")
    print({
        "transfer_status": record["transfer_status"],
        "transfer_ready": record["transfer_ready"],
        "summary": record["transfer_summary"],
        "top": record["transfer_items"][0],
    })


if __name__ == "__main__":
    test_oi_120_oracle_qseries_transfer_record_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_qseries_transfer_record_engine import oracle_qseries_transfer_record_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-120 INSTALLER")
print(" Oracle Q Series Transfer Record Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-120 installed")
print()
print("Run:")
print("py test_oi_120_oracle_qseries_transfer_record_engine.py")