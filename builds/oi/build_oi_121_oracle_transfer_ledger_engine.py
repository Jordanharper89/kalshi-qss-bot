from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_transfer_ledger_engine.py"
TEST = ROOT / "test_oi_121_oracle_transfer_ledger_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-121 Oracle Transfer Ledger Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert OI-120 Oracle-to-Q-Series transfer records into durable read-only ledger entries.
- Preserve transfer traceability, boundary enforcement, and Q Series ownership.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from datetime import datetime, timezone
import hashlib
import json


class OracleTransferLedgerEngine:
    module = "oi_121_oracle_transfer_ledger_engine"

    def __init__(self):
        self.last_ledger = {}

    def build_ledger_entry(self, transfer_record=None):
        transfer_record = transfer_record or {}

        transfer_items = [
            x for x in transfer_record.get("transfer_items", [])
            if isinstance(x, dict)
        ]

        ledger_items = []
        for item in transfer_items:
            ledger_items.append({
                "market": item.get("market"),
                "transfer_rank": int(self._float(item.get("transfer_rank"), 0)),
                "transfer_score": round(self._float(item.get("transfer_score")), 4),
                "transfer_tier": item.get("transfer_tier"),
                "intake_tier": item.get("intake_tier"),
                "handoff_tier": item.get("handoff_tier"),
                "review_conclusion": item.get("review_conclusion"),
                "q_series_visibility": bool(item.get("q_series_visibility")),
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            })

        ledger_items.sort(
            key=lambda x: (
                x["transfer_rank"] if x["transfer_rank"] else 999999,
                -x["transfer_score"],
            )
        )

        ledger_hash = self._hash_record({
            "transfer_status": transfer_record.get("transfer_status"),
            "transfer_ready": transfer_record.get("transfer_ready"),
            "audit_status": transfer_record.get("audit_status"),
            "intake_status": transfer_record.get("intake_status"),
            "items": ledger_items,
        })

        entry = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "input_module": "oi_120_oracle_qseries_transfer_record_engine",
            "ledger_entry_id": ledger_hash,
            "ledger_status": self._ledger_status(transfer_record),
            "transfer_status": transfer_record.get("transfer_status"),
            "transfer_ready": bool(transfer_record.get("transfer_ready", False)),
            "audit_status": transfer_record.get("audit_status"),
            "intake_status": transfer_record.get("intake_status"),
            "q_series_safe_to_view": bool(transfer_record.get("q_series_safe_to_view", False)),
            "transfer_count": len(ledger_items),
            "ledger_items": ledger_items,
            "top_ledger_items": ledger_items[:10],
            "ledger_summary": self._summary(transfer_record, ledger_items, ledger_hash),
            "immutability_note": "Ledger entry is deterministic from transfer content and read-only metadata.",
            "oracle_boundaries": [
                "Oracle Intelligence is read-only.",
                "Oracle ledger does not execute.",
                "Oracle ledger does not approve execution.",
                "Q Series owns execution evaluation and execution decisions.",
            ],
        }

        self.last_ledger = entry
        return entry

    def _ledger_status(self, record):
        if record.get("transfer_ready") is True and record.get("transfer_status") == "ready_for_q_series_visibility":
            return "recorded_ready_transfer"
        if record.get("transfer_status") in {"ready_with_warnings"}:
            return "recorded_warning_transfer"
        return "recorded_blocked_transfer"

    def _hash_record(self, data):
        payload = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]

    def _summary(self, record, items, ledger_hash):
        counts = {}
        for item in items:
            tier = item["transfer_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        top = items[0] if items else None

        return {
            "ledger_entry_id": ledger_hash,
            "headline": (
                f"Oracle transfer ledger recorded; top market is {top['market']}."
                if top else
                "Oracle transfer ledger recorded with no market items."
            ),
            "transfer_tier_counts": counts,
            "top_market": top["market"] if top else None,
            "top_transfer_tier": top["transfer_tier"] if top else None,
            "transfer_ready": bool(record.get("transfer_ready", False)),
            "transfer_status": record.get("transfer_status"),
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
            "has_ledger": bool(self.last_ledger),
            "ledger_status": self.last_ledger.get("ledger_status"),
            "transfer_count": self.last_ledger.get("transfer_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_transfer_ledger_engine = OracleTransferLedgerEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_transfer_ledger_engine import oracle_transfer_ledger_engine


def test_oi_121_oracle_transfer_ledger_engine():
    transfer_record = {
        "transfer_status": "ready_for_q_series_visibility",
        "transfer_ready": True,
        "audit_status": "passed",
        "audit_score": 100.0,
        "intake_status": "ready",
        "q_series_safe_to_view": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "transfer_items": [
            {
                "market": "CRYPTO",
                "transfer_rank": 1,
                "transfer_score": 100.0,
                "transfer_tier": "critical",
                "intake_tier": "critical",
                "handoff_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "transfer_rank": 2,
                "transfer_score": 90.0,
                "transfer_tier": "critical",
                "intake_tier": "high",
                "handoff_tier": "high",
                "review_conclusion": "confirmed_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    ledger = oracle_transfer_ledger_engine.build_ledger_entry(transfer_record)

    assert ledger["status"] == "ok"
    assert ledger["read_only"] is True
    assert ledger["execution_allowed"] is False
    assert ledger["execution_owner"] == "Q Series"
    assert ledger["ledger_status"] == "recorded_ready_transfer"
    assert ledger["transfer_count"] == 2
    assert len(ledger["ledger_entry_id"]) == 24
    assert ledger["ledger_items"][0]["market"] == "CRYPTO"
    assert ledger["ledger_summary"]["execution_allowed"] is False

    diag = oracle_transfer_ledger_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False

    print("[PASS] OI-121 Oracle Transfer Ledger Engine")
    print({
        "ledger_status": ledger["ledger_status"],
        "ledger_entry_id": ledger["ledger_entry_id"],
        "summary": ledger["ledger_summary"],
        "top": ledger["ledger_items"][0],
    })


if __name__ == "__main__":
    test_oi_121_oracle_transfer_ledger_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_transfer_ledger_engine import oracle_transfer_ledger_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-121 INSTALLER")
print(" Oracle Transfer Ledger Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-121 installed")
print()
print("Run:")
print("py test_oi_121_oracle_transfer_ledger_engine.py")