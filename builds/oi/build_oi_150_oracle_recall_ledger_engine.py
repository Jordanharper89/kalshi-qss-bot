from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_recall_ledger_engine.py"
TEST = ROOT / "test_oi_150_oracle_recall_ledger_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-150 Oracle Recall Ledger Engine
Read-only Oracle Intelligence module.

Purpose:
- Record confirmed Oracle recall receipts into a read-only recall ledger.
- Preserve recall receipt lineage, receipt item summaries, event receipt references,
  validation status, and Q Series execution ownership.
- Produce immutable-style ledger entries for downstream integrity checks.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import hashlib
import json
import time


class OracleRecallLedgerEngine:
    module = "oi_150_oracle_recall_ledger_engine"

    def __init__(self):
        self.last_ledger_report = {}

    def record_recall_ledger(self, recall_receipt_report=None):
        recall_receipt_report = recall_receipt_report or {}

        receipt_items = [
            x for x in recall_receipt_report.get("receipt_items", [])
            if isinstance(x, dict)
        ]

        ledger_entries = []
        for item in receipt_items:
            ledger_entries.append(self._ledger_entry(item, recall_receipt_report))

        ledger_entries.sort(
            key=lambda x: (
                x["ledger_score"],
                x["receipt_score"],
                x["market"],
            ),
            reverse=True,
        )

        for idx, entry in enumerate(ledger_entries, start=1):
            entry["ledger_rank"] = idx

        ledger_id = self._ledger_id(recall_receipt_report, ledger_entries)

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_149_oracle_recall_receipt_engine",
            ],
            "ledger_id": ledger_id,
            "ledger_status": self._ledger_status(recall_receipt_report, ledger_entries),
            "ledger_confirmed": self._ledger_confirmed(recall_receipt_report, ledger_entries),
            "source_receipt_id": recall_receipt_report.get("receipt_id"),
            "source_receipt_status": recall_receipt_report.get("receipt_status"),
            "source_receipt_confirmed": recall_receipt_report.get("receipt_confirmed"),
            "ledger_entry_count": len(ledger_entries),
            "ledger_entries": ledger_entries,
            "top_ledger_entries": ledger_entries[:10],
            "ledger_summary": self._summary(ledger_id, recall_receipt_report, ledger_entries),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "recall_ledger_context_only",
            },
        }

        self.last_ledger_report = report
        return report

    def _ledger_entry(self, receipt_item, receipt_report):
        market = str(receipt_item.get("market") or "UNKNOWN")
        receipt_score = self._float(receipt_item.get("receipt_score"), 0)
        event_receipts = [
            x for x in receipt_item.get("event_receipts", [])
            if isinstance(x, dict)
        ]

        ledger_score = self._ledger_score(
            receipt_score=receipt_score,
            receipt_confirmed=receipt_report.get("receipt_confirmed") is True,
            event_receipt_count=len(event_receipts),
        )

        entry_seed = {
            "market": market,
            "receipt_id": receipt_report.get("receipt_id"),
            "receipt_score": receipt_score,
            "receipt_tier": receipt_item.get("receipt_tier"),
            "event_receipt_count": len(event_receipts),
        }

        return {
            "ledger_entry_id": self._short_hash(entry_seed),
            "market": market,
            "ledger_score": round(ledger_score, 4),
            "ledger_tier": self._tier(ledger_score),
            "ledger_entry_status": self._entry_status(ledger_score, receipt_item, receipt_report),
            "receipt_id": receipt_report.get("receipt_id"),
            "receipt_score": round(receipt_score, 4),
            "receipt_tier": receipt_item.get("receipt_tier"),
            "receipt_status": receipt_item.get("receipt_status"),
            "recall_score": receipt_item.get("recall_score"),
            "recall_tier": receipt_item.get("recall_tier"),
            "packet_validation_status": receipt_item.get("packet_validation_status"),
            "knowledge_tier": receipt_item.get("knowledge_tier"),
            "knowledge_status": receipt_item.get("knowledge_status"),
            "timeline_phase": receipt_item.get("timeline_phase"),
            "confidence_tier": receipt_item.get("confidence_tier"),
            "memory_tier": receipt_item.get("memory_tier"),
            "event_receipt_count": len(event_receipts),
            "event_receipt_refs": self._event_refs(event_receipts),
            "lineage_hash": self._short_hash(receipt_item),
            "ledger_note": self._note(market, ledger_score, receipt_item),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "read_only": True,
        }

    def _event_refs(self, event_receipts):
        refs = []
        for idx, event in enumerate(event_receipts, start=1):
            refs.append({
                "event_ref_id": event.get("event_receipt_id") or f"event-ref-{idx:03d}",
                "event_type": event.get("event_type"),
                "event_source": event.get("event_source"),
                "event_receipt_score": self._float(event.get("event_receipt_score"), 0),
                "event_receipt_status": event.get("event_receipt_status"),
                "execution_allowed": False,
                "read_only": True,
            })
        return refs

    def _ledger_score(self, receipt_score, receipt_confirmed, event_receipt_count):
        confirmation_component = 18 if receipt_confirmed else -20
        event_component = min(event_receipt_count * 4, 14)
        score = receipt_score * 0.68 + confirmation_component + event_component
        return max(0.0, min(100.0, score))

    def _tier(self, score):
        if score >= 85:
            return "institutional_ledger"
        if score >= 70:
            return "strong_ledger"
        if score >= 50:
            return "developing_ledger"
        if score >= 30:
            return "thin_ledger"
        return "ledger_trace"

    def _entry_status(self, score, receipt_item, receipt_report):
        if receipt_report.get("receipt_confirmed") is not True:
            return "receipt_unconfirmed"
        if receipt_item.get("receipt_status") not in {"confirmed", "confirmed_with_notes"}:
            return "needs_review"
        if score >= 85:
            return "recorded_confirmed"
        if score >= 70:
            return "recorded"
        return "recorded_low_confidence"

    def _ledger_status(self, receipt_report, entries):
        if receipt_report.get("receipt_confirmed") is not True:
            return "receipt_unconfirmed"
        if not entries:
            return "empty"
        if all(x["ledger_entry_status"] == "recorded_confirmed" for x in entries):
            return "recorded_confirmed"
        if any(x["ledger_entry_status"] == "needs_review" for x in entries):
            return "recorded_with_review"
        return "recorded"

    def _ledger_confirmed(self, receipt_report, entries):
        return (
            receipt_report.get("receipt_confirmed") is True
            and len(entries) > 0
            and all(x.get("execution_allowed") is False for x in entries)
        )

    def _summary(self, ledger_id, receipt_report, entries):
        tier_counts = {}
        status_counts = {}
        market_counts = {}

        for entry in entries:
            tier = entry["ledger_tier"]
            status = entry["ledger_entry_status"]
            market = entry["market"]

            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1
            market_counts[market] = market_counts.get(market, 0) + 1

        top = entries[0] if entries else None
        ledger_status = self._ledger_status(receipt_report, entries)

        return {
            "headline": self._headline(ledger_status, top),
            "ledger_id": ledger_id,
            "ledger_status": ledger_status,
            "ledger_confirmed": self._ledger_confirmed(receipt_report, entries),
            "ledger_entry_count": len(entries),
            "ledger_tier_counts": tier_counts,
            "ledger_entry_status_counts": status_counts,
            "market_counts": market_counts,
            "top_market": top["market"] if top else None,
            "top_ledger_tier": top["ledger_tier"] if top else None,
            "source_receipt_id": receipt_report.get("receipt_id"),
            "source_receipt_status": receipt_report.get("receipt_status"),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "read_only": True,
        }

    def _headline(self, ledger_status, top):
        if ledger_status in {"recorded_confirmed", "recorded"} and top:
            return f"Oracle recall ledger recorded; top ledger market is {top['market']}."
        if ledger_status == "empty":
            return "Oracle recall ledger has no entries."
        return "Oracle recall ledger requires review."

    def _note(self, market, score, receipt_item):
        return (
            f"{market} recall ledger score is {round(score, 2)} from receipt tier "
            f"{receipt_item.get('receipt_tier')} and recall tier {receipt_item.get('recall_tier')}. "
            "Oracle ledger is read-only; Q Series owns execution."
        )

    def _ledger_id(self, receipt_report, entries):
        payload = {
            "receipt_id": receipt_report.get("receipt_id"),
            "receipt_status": receipt_report.get("receipt_status"),
            "entries": [
                {
                    "market": x.get("market"),
                    "ledger_score": x.get("ledger_score"),
                    "ledger_tier": x.get("ledger_tier"),
                    "lineage_hash": x.get("lineage_hash"),
                }
                for x in entries
            ],
        }
        return self._short_hash(payload)

    def _short_hash(self, payload):
        text = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]

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
            "has_ledger_report": bool(self.last_ledger_report),
            "ledger_status": self.last_ledger_report.get("ledger_status"),
            "ledger_confirmed": self.last_ledger_report.get("ledger_confirmed"),
            "ledger_entry_count": self.last_ledger_report.get("ledger_entry_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_recall_ledger_engine = OracleRecallLedgerEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_recall_ledger_engine import (
    oracle_recall_ledger_engine,
)


def test_oi_150_oracle_recall_ledger_engine():
    receipt_report = {
        "read_only": True,
        "execution_allowed": False,
        "receipt_id": "receipt-abc123",
        "receipt_status": "confirmed",
        "receipt_confirmed": True,
        "receipt_item_count": 1,
        "receipt_items": [
            {
                "market": "CRYPTO",
                "receipt_score": 94.0,
                "receipt_tier": "institutional_receipt",
                "receipt_status": "confirmed",
                "recall_score": 100.0,
                "recall_tier": "institutional_recall",
                "packet_validation_status": "validated",
                "knowledge_tier": "institutional_knowledge",
                "knowledge_status": "executive_ready_knowledge",
                "timeline_phase": "executive_timeline_active",
                "confidence_tier": "institutional_confidence",
                "memory_tier": "institutional_memory",
                "event_receipts": [
                    {
                        "event_receipt_id": "evt-rec-001",
                        "event_type": "executive_trend",
                        "event_source": "trend",
                        "event_receipt_score": 87.0,
                        "event_receipt_status": "confirmed",
                        "read_only": True,
                        "execution_allowed": False,
                    },
                    {
                        "event_receipt_id": "evt-rec-002",
                        "event_type": "confidence_evolution",
                        "event_source": "confidence",
                        "event_receipt_score": 84.0,
                        "event_receipt_status": "confirmed",
                        "read_only": True,
                        "execution_allowed": False,
                    },
                ],
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "read_only": True,
            }
        ],
    }

    report = oracle_recall_ledger_engine.record_recall_ledger(receipt_report)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["ledger_status"] == "recorded_confirmed"
    assert report["ledger_confirmed"] is True
    assert report["source_receipt_id"] == "receipt-abc123"
    assert report["ledger_entry_count"] == 1
    assert report["ledger_entries"][0]["ledger_rank"] == 1
    assert report["ledger_entries"][0]["market"] == "CRYPTO"
    assert report["ledger_entries"][0]["ledger_entry_status"] == "recorded_confirmed"
    assert report["ledger_entries"][0]["execution_allowed"] is False
    assert report["ledger_entries"][0]["read_only"] is True
    assert report["ledger_entries"][0]["event_receipt_refs"][0]["execution_allowed"] is False
    assert report["ledger_summary"]["execution_allowed"] is False
    assert report["ledger_summary"]["execution_owner"] == "Q Series"
    assert report["ledger_summary"]["ledger_confirmed"] is True

    diag = oracle_recall_ledger_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["ledger_status"] == "recorded_confirmed"

    print("[PASS] OI-150 Oracle Recall Ledger Engine")
    print({
        "ledger_id": report["ledger_id"],
        "ledger_status": report["ledger_status"],
        "ledger_confirmed": report["ledger_confirmed"],
        "summary": report["ledger_summary"],
        "top": report["ledger_entries"][0],
    })


if __name__ == "__main__":
    test_oi_150_oracle_recall_ledger_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_recall_ledger_engine import oracle_recall_ledger_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-150 INSTALLER")
print(" Oracle Recall Ledger Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-150 installed")
print()
print("Run:")
print("py test_oi_150_oracle_recall_ledger_engine.py")