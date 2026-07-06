from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_recall_receipt_engine.py"
TEST = ROOT / "test_oi_149_oracle_recall_receipt_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-149 Oracle Recall Receipt Engine
Read-only Oracle Intelligence module.

Purpose:
- Create a receipt for validated Oracle knowledge recall packets.
- Confirm recall validation status, recall packet integrity, event recall lineage,
  and Q Series execution ownership.
- Produce institutional read-only recall receipt records for downstream audit/history.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import hashlib
import json
import time


class OracleRecallReceiptEngine:
    module = "oi_149_oracle_recall_receipt_engine"

    def __init__(self):
        self.last_receipt_report = {}

    def build_recall_receipt(self, recall_report=None, validation_report=None):
        recall_report = recall_report or {}
        validation_report = validation_report or {}

        recall_packets = [
            x for x in recall_report.get("recall_packets", [])
            if isinstance(x, dict)
        ]
        packet_validations = [
            x for x in validation_report.get("packet_validations", [])
            if isinstance(x, dict)
        ]

        validation_index = self._index(packet_validations, "market")

        receipt_items = []
        for packet in recall_packets:
            market = str(packet.get("market") or "UNKNOWN")
            validation = validation_index.get(market, {})
            receipt_items.append(self._receipt_item(packet, validation))

        receipt_items.sort(
            key=lambda x: (
                x["receipt_score"],
                x["recall_score"],
                x["market"],
            ),
            reverse=True,
        )

        for idx, item in enumerate(receipt_items, start=1):
            item["receipt_rank"] = idx

        receipt_id = self._receipt_id(receipt_items, validation_report)

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_147_oracle_knowledge_recall_engine",
                "oi_148_oracle_recall_validation_engine",
            ],
            "receipt_id": receipt_id,
            "receipt_status": self._receipt_status(validation_report, receipt_items),
            "receipt_confirmed": self._receipt_confirmed(validation_report, receipt_items),
            "source_recall_count": len(recall_packets),
            "receipt_item_count": len(receipt_items),
            "receipt_items": receipt_items,
            "top_receipt_items": receipt_items[:10],
            "receipt_summary": self._summary(receipt_id, validation_report, receipt_items),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "recall_receipt_context_only",
            },
        }

        self.last_receipt_report = report
        return report

    def _receipt_item(self, packet, validation):
        market = str(packet.get("market") or "UNKNOWN")
        recall_score = self._float(packet.get("recall_score"), 0)
        validation_score = self._float(validation.get("packet_validation_score"), 0)
        event_count = len(packet.get("event_recall", []) or [])

        receipt_score = self._receipt_score(
            recall_score=recall_score,
            validation_score=validation_score,
            event_count=event_count,
            critical_failures=self._float(validation.get("critical_failure_count"), 0),
        )

        return {
            "market": market,
            "receipt_score": round(receipt_score, 4),
            "receipt_tier": self._tier(receipt_score),
            "receipt_status": self._item_status(receipt_score, validation),
            "recall_score": round(recall_score, 4),
            "recall_tier": packet.get("recall_tier"),
            "recall_status": packet.get("recall_status"),
            "packet_validation_score": round(validation_score, 4),
            "packet_validation_status": validation.get("packet_validation_status"),
            "event_recall_count": event_count,
            "knowledge_tier": packet.get("knowledge_tier"),
            "knowledge_status": packet.get("knowledge_status"),
            "timeline_phase": packet.get("timeline_phase"),
            "confidence_tier": packet.get("confidence_tier"),
            "memory_tier": packet.get("memory_tier"),
            "event_receipts": self._event_receipts(packet.get("event_recall", [])),
            "receipt_note": self._note(market, receipt_score, packet, validation),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "read_only": True,
        }

    def _event_receipts(self, events):
        receipts = []

        for idx, event in enumerate(events or [], start=1):
            if not isinstance(event, dict):
                continue

            event_score = self._float(event.get("event_score"), 0)
            recall_weight = self._float(event.get("recall_weight"), 0)
            receipt_score = max(0.0, min(100.0, event_score * 0.45 + recall_weight * 0.45 + 10))

            receipts.append({
                "event_receipt_id": self._short_hash({
                    "idx": idx,
                    "event_type": event.get("event_type"),
                    "event_score": event_score,
                    "recall_weight": recall_weight,
                }),
                "event_type": event.get("event_type"),
                "event_source": event.get("event_source"),
                "event_score": round(event_score, 4),
                "recall_weight": round(recall_weight, 4),
                "event_receipt_score": round(receipt_score, 4),
                "event_tier": event.get("event_tier"),
                "event_label": event.get("event_label"),
                "event_receipt_status": "confirmed" if event.get("read_only") is True and event.get("execution_allowed") is False else "needs_review",
                "execution_allowed": False,
                "read_only": True,
            })

        receipts.sort(
            key=lambda x: (
                x["event_receipt_score"],
                x["event_type"] or "",
            ),
            reverse=True,
        )

        for idx, receipt in enumerate(receipts, start=1):
            receipt["event_receipt_rank"] = idx

        return receipts

    def _receipt_score(self, recall_score, validation_score, event_count, critical_failures):
        if critical_failures > 0:
            penalty = min(critical_failures * 25, 70)
        else:
            penalty = 0

        event_component = min(event_count * 4, 16)
        score = recall_score * 0.48 + validation_score * 0.36 + event_component - penalty
        return max(0.0, min(100.0, score))

    def _tier(self, score):
        if score >= 85:
            return "institutional_receipt"
        if score >= 70:
            return "strong_receipt"
        if score >= 50:
            return "developing_receipt"
        if score >= 30:
            return "thin_receipt"
        return "receipt_trace"

    def _item_status(self, score, validation):
        validation_status = str(validation.get("packet_validation_status") or "")

        if validation_status == "validated" and score >= 85:
            return "confirmed"
        if validation_status in {"validated", "validated_with_warnings"}:
            return "confirmed_with_notes"
        if validation_status:
            return "needs_review"
        return "unvalidated"

    def _receipt_status(self, validation_report, items):
        validation_status = str(validation_report.get("validation_status") or "")
        critical = self._float(validation_report.get("critical_failure_count"), 0)

        if critical > 0:
            return "failed"
        if validation_status == "validated" and items:
            return "confirmed"
        if validation_status == "validated_with_warnings":
            return "confirmed_with_warnings"
        if not items:
            return "empty"
        return "needs_review"

    def _receipt_confirmed(self, validation_report, items):
        return (
            self._receipt_status(validation_report, items) in {"confirmed", "confirmed_with_warnings"}
            and validation_report.get("execution_allowed") is False
            and validation_report.get("read_only") is True
        )

    def _summary(self, receipt_id, validation_report, items):
        tier_counts = {}
        status_counts = {}
        market_counts = {}

        for item in items:
            tier = item["receipt_tier"]
            status = item["receipt_status"]
            market = item["market"]

            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1
            market_counts[market] = market_counts.get(market, 0) + 1

        top = items[0] if items else None
        confirmed = self._receipt_status(validation_report, items)

        return {
            "headline": self._headline(confirmed, top),
            "receipt_id": receipt_id,
            "receipt_status": confirmed,
            "receipt_confirmed": confirmed in {"confirmed", "confirmed_with_warnings"},
            "receipt_item_count": len(items),
            "receipt_tier_counts": tier_counts,
            "receipt_status_counts": status_counts,
            "market_counts": market_counts,
            "top_market": top["market"] if top else None,
            "top_receipt_tier": top["receipt_tier"] if top else None,
            "validation_status": validation_report.get("validation_status"),
            "validation_score": validation_report.get("validation_score"),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "read_only": True,
        }

    def _headline(self, status, top):
        if status in {"confirmed", "confirmed_with_warnings"} and top:
            return f"Oracle recall receipt confirmed; top receipt market is {top['market']}."
        if status == "empty":
            return "Oracle recall receipt is empty."
        return "Oracle recall receipt requires review."

    def _note(self, market, score, packet, validation):
        return (
            f"{market} recall receipt score is {round(score, 2)} from recall tier "
            f"{packet.get('recall_tier')} and validation status "
            f"{validation.get('packet_validation_status')}. Oracle receipt is read-only; "
            "Q Series owns execution."
        )

    def _receipt_id(self, items, validation_report):
        payload = {
            "items": [
                {
                    "market": x.get("market"),
                    "receipt_score": x.get("receipt_score"),
                    "receipt_tier": x.get("receipt_tier"),
                }
                for x in items
            ],
            "validation_status": validation_report.get("validation_status"),
            "validation_score": validation_report.get("validation_score"),
        }
        return self._short_hash(payload)

    def _short_hash(self, payload):
        text = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]

    def _index(self, rows, key):
        out = {}
        for row in rows:
            value = str(row.get(key) or "UNKNOWN")
            if value not in out:
                out[value] = row
        return out

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
            "has_receipt_report": bool(self.last_receipt_report),
            "receipt_status": self.last_receipt_report.get("receipt_status"),
            "receipt_confirmed": self.last_receipt_report.get("receipt_confirmed"),
            "receipt_item_count": self.last_receipt_report.get("receipt_item_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_recall_receipt_engine = OracleRecallReceiptEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_recall_receipt_engine import (
    oracle_recall_receipt_engine,
)


def test_oi_149_oracle_recall_receipt_engine():
    recall_report = {
        "read_only": True,
        "execution_allowed": False,
        "recall_count": 1,
        "recall_packets": [
            {
                "market": "CRYPTO",
                "recall_score": 100.0,
                "recall_tier": "institutional_recall",
                "recall_status": "executive_recall_ready",
                "knowledge_tier": "institutional_knowledge",
                "knowledge_status": "executive_ready_knowledge",
                "timeline_phase": "executive_timeline_active",
                "confidence_tier": "institutional_confidence",
                "memory_tier": "institutional_memory",
                "event_recall": [
                    {
                        "event_recall_id": "recall-event-002",
                        "event_type": "executive_trend",
                        "event_source": "trend",
                        "event_score": 89.4486,
                        "event_tier": "dominant_historical_trend",
                        "event_label": "executive_priority_watch",
                        "timeline_position": 2,
                        "recall_weight": 82.614,
                        "read_only": True,
                        "execution_allowed": False,
                        "event_recall_rank": 1,
                    },
                    {
                        "event_recall_id": "recall-event-001",
                        "event_type": "confidence_evolution",
                        "event_source": "confidence",
                        "event_score": 89.175,
                        "event_tier": "institutional_confidence",
                        "event_label": "stable",
                        "timeline_position": 1,
                        "recall_weight": 80.4225,
                        "read_only": True,
                        "execution_allowed": False,
                        "event_recall_rank": 2,
                    },
                ],
                "read_only": True,
                "execution_allowed": False,
            }
        ],
    }

    validation_report = {
        "read_only": True,
        "execution_allowed": False,
        "validation_status": "validated",
        "validation_score": 100.0,
        "validated": True,
        "critical_failure_count": 0,
        "packet_validations": [
            {
                "market": "CRYPTO",
                "recall_score": 100.0,
                "packet_validation_score": 100.0,
                "packet_validation_status": "validated",
                "failed_check_count": 0,
                "critical_failure_count": 0,
                "event_recall_count": 2,
                "read_only": True,
                "execution_allowed": False,
            }
        ],
    }

    report = oracle_recall_receipt_engine.build_recall_receipt(
        recall_report,
        validation_report,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["receipt_status"] == "confirmed"
    assert report["receipt_confirmed"] is True
    assert report["source_recall_count"] == 1
    assert report["receipt_item_count"] == 1
    assert report["receipt_items"][0]["receipt_rank"] == 1
    assert report["receipt_items"][0]["market"] == "CRYPTO"
    assert report["receipt_items"][0]["receipt_status"] == "confirmed"
    assert report["receipt_items"][0]["execution_allowed"] is False
    assert report["receipt_items"][0]["read_only"] is True
    assert report["receipt_items"][0]["event_receipts"][0]["execution_allowed"] is False
    assert report["receipt_summary"]["execution_allowed"] is False
    assert report["receipt_summary"]["execution_owner"] == "Q Series"
    assert report["receipt_summary"]["receipt_confirmed"] is True

    diag = oracle_recall_receipt_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["receipt_status"] == "confirmed"

    print("[PASS] OI-149 Oracle Recall Receipt Engine")
    print({
        "receipt_id": report["receipt_id"],
        "receipt_status": report["receipt_status"],
        "receipt_confirmed": report["receipt_confirmed"],
        "summary": report["receipt_summary"],
        "top": report["receipt_items"][0],
    })


if __name__ == "__main__":
    test_oi_149_oracle_recall_receipt_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_recall_receipt_engine import oracle_recall_receipt_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-149 INSTALLER")
print(" Oracle Recall Receipt Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-149 installed")
print()
print("Run:")
print("py test_oi_149_oracle_recall_receipt_engine.py")