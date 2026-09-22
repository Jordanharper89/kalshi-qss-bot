
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
