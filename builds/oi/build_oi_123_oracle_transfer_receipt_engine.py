from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_transfer_receipt_engine.py"
TEST = ROOT / "test_oi_123_oracle_transfer_receipt_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-123 Oracle Transfer Receipt Engine
Read-only Oracle Intelligence module.

Purpose:
- Create a final receipt after Oracle transfer ledger integrity is verified.
- Confirm Oracle-to-Q-Series transfer status, visibility readiness, ledger integrity,
  and execution ownership boundaries.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from datetime import datetime, timezone


class OracleTransferReceiptEngine:
    module = "oi_123_oracle_transfer_receipt_engine"

    def __init__(self):
        self.last_receipt = {}

    def build_receipt(self, transfer_ledger=None, ledger_integrity=None):
        transfer_ledger = transfer_ledger or {}
        ledger_integrity = ledger_integrity or {}

        ledger_items = [
            x for x in transfer_ledger.get("ledger_items", [])
            if isinstance(x, dict)
        ]

        integrity_confirmed = bool(ledger_integrity.get("ledger_integrity_confirmed", False))
        integrity_status = str(ledger_integrity.get("integrity_status") or "unknown")
        ledger_status = str(transfer_ledger.get("ledger_status") or "unknown")
        transfer_ready = bool(transfer_ledger.get("transfer_ready", False))

        receipt_items = []
        for item in ledger_items:
            receipt_score = self._receipt_score(item, integrity_confirmed, transfer_ready)

            receipt_items.append({
                "market": item.get("market"),
                "receipt_score": round(receipt_score, 4),
                "receipt_tier": self._tier(receipt_score),
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
                "receipt_note": self._note(item, receipt_score, integrity_confirmed, transfer_ready),
            })

        receipt_items.sort(
            key=lambda x: (
                -x["receipt_score"],
                x["transfer_rank"] if x["transfer_rank"] else 999999,
            )
        )

        for idx, item in enumerate(receipt_items, start=1):
            item["receipt_rank"] = idx

        receipt_status = self._receipt_status(
            integrity_confirmed=integrity_confirmed,
            integrity_status=integrity_status,
            ledger_status=ledger_status,
            transfer_ready=transfer_ready,
        )

        receipt = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "input_modules": [
                "oi_121_oracle_transfer_ledger_engine",
                "oi_122_oracle_ledger_integrity_engine",
            ],
            "receipt_status": receipt_status,
            "receipt_confirmed": receipt_status == "confirmed",
            "ledger_entry_id": transfer_ledger.get("ledger_entry_id") or ledger_integrity.get("ledger_entry_id"),
            "ledger_status": ledger_status,
            "integrity_status": integrity_status,
            "integrity_score": round(self._float(ledger_integrity.get("integrity_score")), 4),
            "ledger_integrity_confirmed": integrity_confirmed,
            "transfer_ready": transfer_ready,
            "transfer_status": transfer_ledger.get("transfer_status"),
            "receipt_count": len(receipt_items),
            "receipt_items": receipt_items,
            "top_receipt_items": receipt_items[:10],
            "receipt_summary": self._summary(
                receipt_status=receipt_status,
                transfer_ledger=transfer_ledger,
                ledger_integrity=ledger_integrity,
                items=receipt_items,
            ),
            "oracle_boundary_receipt": [
                "Oracle transfer receipt is read-only.",
                "Oracle transfer receipt confirms visibility only.",
                "Oracle does not execute.",
                "Oracle does not approve execution.",
                "Q Series owns execution evaluation and decisions.",
            ],
        }

        self.last_receipt = receipt
        return receipt

    def _receipt_score(self, item, integrity_confirmed, transfer_ready):
        base = self._float(item.get("transfer_score"))
        integrity_bonus = 6 if integrity_confirmed else -30
        ready_bonus = 4 if transfer_ready else -20
        visibility_bonus = 4 if item.get("q_series_visibility") is True else -20
        tier_bonus = {
            "critical": 5,
            "high": 3,
            "elevated": 1,
            "watch": 0,
            "blocked": -10,
        }.get(str(item.get("transfer_tier") or ""), 0)

        score = base + integrity_bonus + ready_bonus + visibility_bonus + tier_bonus
        return max(0.0, min(100.0, score))

    def _receipt_status(self, integrity_confirmed, integrity_status, ledger_status, transfer_ready):
        if integrity_confirmed and integrity_status == "verified" and ledger_status == "recorded_ready_transfer" and transfer_ready:
            return "confirmed"
        if integrity_status == "verified_with_warnings":
            return "confirmed_with_warnings"
        if integrity_status in {"needs_review", "failed"}:
            return "blocked_by_integrity"
        if not transfer_ready:
            return "blocked_by_transfer"
        return "review_required"

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

    def _note(self, item, score, integrity_confirmed, transfer_ready):
        market = item.get("market")
        if not integrity_confirmed:
            return f"{market} receipt not confirmed because ledger integrity is not verified."
        if not transfer_ready:
            return f"{market} receipt not confirmed because transfer is not ready."
        return (
            f"{market} receipt tier is {self._tier(score)}. "
            "Oracle confirms read-only visibility transfer to Q Series; no execution permission is granted."
        )

    def _summary(self, receipt_status, transfer_ledger, ledger_integrity, items):
        counts = {}
        for item in items:
            tier = item["receipt_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        top = items[0] if items else None

        if receipt_status == "confirmed" and top:
            headline = f"Oracle transfer receipt confirmed; top receipt market is {top['market']}."
        elif receipt_status == "confirmed":
            headline = "Oracle transfer receipt confirmed with no market items."
        else:
            headline = f"Oracle transfer receipt status is {receipt_status}; review required."

        return {
            "headline": headline,
            "receipt_status": receipt_status,
            "receipt_tier_counts": counts,
            "top_market": top["market"] if top else None,
            "top_receipt_tier": top["receipt_tier"] if top else None,
            "ledger_entry_id": transfer_ledger.get("ledger_entry_id") or ledger_integrity.get("ledger_entry_id"),
            "integrity_score": ledger_integrity.get("integrity_score"),
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
            "has_receipt": bool(self.last_receipt),
            "receipt_status": self.last_receipt.get("receipt_status"),
            "receipt_confirmed": self.last_receipt.get("receipt_confirmed", False),
            "receipt_count": self.last_receipt.get("receipt_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_transfer_receipt_engine = OracleTransferReceiptEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_transfer_receipt_engine import oracle_transfer_receipt_engine


def test_oi_123_oracle_transfer_receipt_engine():
    ledger = {
        "ledger_entry_id": "abc123def456ghi789jkl012",
        "ledger_status": "recorded_ready_transfer",
        "transfer_status": "ready_for_q_series_visibility",
        "transfer_ready": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
        "ledger_items": [
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

    integrity = {
        "ledger_entry_id": "abc123def456ghi789jkl012",
        "integrity_status": "verified",
        "integrity_score": 100.0,
        "ledger_integrity_confirmed": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
    }

    receipt = oracle_transfer_receipt_engine.build_receipt(ledger, integrity)

    assert receipt["status"] == "ok"
    assert receipt["read_only"] is True
    assert receipt["execution_allowed"] is False
    assert receipt["execution_owner"] == "Q Series"
    assert receipt["receipt_status"] == "confirmed"
    assert receipt["receipt_confirmed"] is True
    assert receipt["ledger_integrity_confirmed"] is True
    assert receipt["receipt_count"] == 2
    assert receipt["receipt_items"][0]["receipt_rank"] == 1
    assert receipt["receipt_items"][0]["market"] == "CRYPTO"
    assert receipt["receipt_summary"]["execution_allowed"] is False

    diag = oracle_transfer_receipt_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["receipt_confirmed"] is True

    print("[PASS] OI-123 Oracle Transfer Receipt Engine")
    print({
        "receipt_status": receipt["receipt_status"],
        "receipt_confirmed": receipt["receipt_confirmed"],
        "summary": receipt["receipt_summary"],
        "top": receipt["receipt_items"][0],
    })


if __name__ == "__main__":
    test_oi_123_oracle_transfer_receipt_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_transfer_receipt_engine import oracle_transfer_receipt_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-123 INSTALLER")
print(" Oracle Transfer Receipt Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-123 installed")
print()
print("Run:")
print("py test_oi_123_oracle_transfer_receipt_engine.py")