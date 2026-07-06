from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "universal_market_adapter_lifecycle_engine.py"
TEST = ROOT / "test_oi_172_universal_market_adapter_lifecycle_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-172 — Oracle Universal Market Adapter Lifecycle Engine

Read-only lifecycle engine for certified Universal Market Adapters.

Purpose:
- Convert adapter certification packets into lifecycle states.
- Track adapter promotion, review, blocked, retired, and active-read-only states.
- Preserve institutional safety boundaries.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _stable_text(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(f"{k}:{_stable_text(value[k])}" for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _hash(value: Any, size: int = 24) -> str:
    return sha256(_stable_text(value).encode("utf-8")).hexdigest()[:size]


@dataclass
class AdapterLifecycleRecord:
    lifecycle_record_id: str
    adapter_id: str
    domain: str
    certification_status: str
    certification_score: float
    lifecycle_state: str
    lifecycle_status: str
    promoted: bool
    blocked: bool
    note: str
    lineage_hash: str
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"


@dataclass
class OracleUniversalMarketAdapterLifecycleEngine:
    name: str = "oracle_universal_market_adapter_lifecycle_engine"
    version: str = "OI-172"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    lifecycle_schema_version: str = "universal_market_adapter_lifecycle_v1"

    def lifecycle_state(self, record: Dict[str, Any]) -> str:
        record = _safe_dict(record)
        status = str(record.get("certification_status") or "")
        score = _num(record.get("certification_score"), 0)
        critical = int(_num(record.get("critical_count"), 0))
        certified = record.get("certified") is True

        if critical > 0 or status == "adapter_certification_blocked":
            return "blocked"
        if status == "adapter_institutionally_certified" and score >= 95 and certified:
            return "active_institutional_read_only"
        if status == "adapter_certified" and certified:
            return "active_read_only"
        if status == "adapter_certified_with_review" and certified:
            return "active_review_read_only"
        return "review_required"

    def lifecycle_status(self, state: str) -> str:
        if state == "active_institutional_read_only":
            return "lifecycle_institutional"
        if state == "active_read_only":
            return "lifecycle_active"
        if state == "active_review_read_only":
            return "lifecycle_active_with_review"
        if state == "blocked":
            return "lifecycle_blocked"
        return "lifecycle_review_required"

    def build_record(self, certification_record: Dict[str, Any]) -> AdapterLifecycleRecord:
        record = _safe_dict(certification_record)
        adapter_id = str(record.get("adapter_id") or "unknown_adapter")
        domain = str(record.get("domain") or "UNKNOWN").upper()
        certification_status = str(record.get("certification_status") or "unknown_certification")
        score = round(_num(record.get("certification_score"), 0), 2)
        state = self.lifecycle_state(record)
        status = self.lifecycle_status(state)

        payload = {
            "adapter_id": adapter_id,
            "domain": domain,
            "certification_status": certification_status,
            "score": score,
            "state": state,
            "source_certification_id": record.get("certification_id"),
        }
        lineage_hash = _hash(payload)

        return AdapterLifecycleRecord(
            lifecycle_record_id=_hash({"payload": payload, "lineage": lineage_hash}),
            adapter_id=adapter_id,
            domain=domain,
            certification_status=certification_status,
            certification_score=score,
            lifecycle_state=state,
            lifecycle_status=status,
            promoted=state in {"active_institutional_read_only", "active_read_only", "active_review_read_only"},
            blocked=state == "blocked",
            note=(
                f"{adapter_id} lifecycle state is {state}. "
                "Adapter lifecycle is read-only; Q Series owns execution."
            ),
            lineage_hash=lineage_hash,
            read_only=True,
            execution_allowed=False,
            execution_owner=self.execution_owner,
        )

    def evaluate(self, certification: Dict[str, Any]) -> Dict[str, Any]:
        certification = _safe_dict(certification)
        cert_records = _safe_list(certification.get("records"))

        records = [self.build_record(record) for record in cert_records]
        records.sort(key=lambda r: (r.domain, r.adapter_id))

        state_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}
        domain_counts: Dict[str, int] = {}

        promoted_count = 0
        blocked_count = 0

        for record in records:
            state_counts[record.lifecycle_state] = state_counts.get(record.lifecycle_state, 0) + 1
            status_counts[record.lifecycle_status] = status_counts.get(record.lifecycle_status, 0) + 1
            domain_counts[record.domain] = domain_counts.get(record.domain, 0) + 1
            if record.promoted:
                promoted_count += 1
            if record.blocked:
                blocked_count += 1

        if not records:
            lifecycle_status = "empty_adapter_lifecycle"
        elif blocked_count:
            lifecycle_status = "adapter_lifecycle_blocked"
        elif promoted_count == len(records) and state_counts.get("active_institutional_read_only", 0) == len(records):
            lifecycle_status = "adapter_lifecycle_institutional"
        elif promoted_count == len(records):
            lifecycle_status = "adapter_lifecycle_active"
        else:
            lifecycle_status = "adapter_lifecycle_review_required"

        lifecycle_id = _hash({
            "source_certification_batch_id": certification.get("adapter_certification_batch_id"),
            "status": lifecycle_status,
            "records": [record.__dict__ for record in records],
        })

        return {
            "module": self.name,
            "version": self.version,
            "lifecycle_schema_version": self.lifecycle_schema_version,
            "adapter_lifecycle_batch_id": lifecycle_id,
            "lifecycle_status": lifecycle_status,
            "evaluated_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "source_adapter_certification_batch_id": certification.get("adapter_certification_batch_id"),
            "source_certification_status": certification.get("certification_status"),
            "adapter_count": len(records),
            "promoted_count": promoted_count,
            "blocked_count": blocked_count,
            "state_counts": state_counts,
            "status_counts": status_counts,
            "domain_counts": domain_counts,
            "executive_summary": {
                "headline": (
                    "Universal Market adapter lifecycle is institutional."
                    if lifecycle_status == "adapter_lifecycle_institutional"
                    else f"Universal Market adapter lifecycle status: {lifecycle_status}."
                ),
                "adapter_lifecycle_batch_id": lifecycle_id,
                "adapter_count": len(records),
                "promoted_count": promoted_count,
                "blocked_count": blocked_count,
                "operator_note": "Lifecycle state is intelligence-only. Oracle remains read-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "records": [record.__dict__ for record in records],
        }

    def lookup_adapter(self, lifecycle: Dict[str, Any], adapter_id: str) -> Dict[str, Any]:
        lifecycle = _safe_dict(lifecycle)
        records = _safe_list(lifecycle.get("records"))
        target = str(adapter_id or "").strip().lower()

        for record in records:
            record = _safe_dict(record)
            if str(record.get("adapter_id") or "").strip().lower() == target:
                return {
                    "module": self.name,
                    "version": self.version,
                    "found": True,
                    "adapter_id": adapter_id,
                    "record": record,
                    "read_only": True,
                    "execution_allowed": False,
                    "execution_owner": self.execution_owner,
                }

        return {
            "module": self.name,
            "version": self.version,
            "found": False,
            "adapter_id": adapter_id,
            "record": None,
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }


oracle_universal_market_adapter_lifecycle_engine = OracleUniversalMarketAdapterLifecycleEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.universal_market_adapter_lifecycle_engine import (
    oracle_universal_market_adapter_lifecycle_engine,
)


def institutional_certification():
    return {
        "adapter_certification_batch_id": "cert-batch-001",
        "certification_status": "adapter_certification_institutional",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "records": [
            {
                "certification_id": "cert-001",
                "adapter_id": "adp.crypto",
                "domain": "CRYPTO",
                "certification_score": 100.0,
                "certification_tier": "institutional_certification",
                "certification_status": "adapter_institutionally_certified",
                "critical_count": 0,
                "warning_count": 0,
                "certified": True,
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            }
        ],
    }


def test_institutional_lifecycle():
    report = oracle_universal_market_adapter_lifecycle_engine.evaluate(institutional_certification())

    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["lifecycle_status"] == "adapter_lifecycle_institutional"
    assert report["adapter_count"] == 1
    assert report["promoted_count"] == 1
    assert report["blocked_count"] == 0
    assert report["records"][0]["lifecycle_state"] == "active_institutional_read_only"


def test_active_review_lifecycle():
    cert = institutional_certification()
    cert["records"][0]["certification_score"] = 80.0
    cert["records"][0]["certification_status"] = "adapter_certified_with_review"
    cert["records"][0]["warning_count"] = 2

    report = oracle_universal_market_adapter_lifecycle_engine.evaluate(cert)

    assert report["lifecycle_status"] == "adapter_lifecycle_active"
    assert report["records"][0]["lifecycle_state"] == "active_review_read_only"
    assert report["promoted_count"] == 1


def test_blocked_lifecycle():
    cert = institutional_certification()
    cert["records"][0]["certification_status"] = "adapter_certification_blocked"
    cert["records"][0]["critical_count"] = 1
    cert["records"][0]["certified"] = False

    report = oracle_universal_market_adapter_lifecycle_engine.evaluate(cert)

    assert report["lifecycle_status"] == "adapter_lifecycle_blocked"
    assert report["blocked_count"] == 1
    assert report["records"][0]["lifecycle_state"] == "blocked"


def test_lookup_adapter():
    report = oracle_universal_market_adapter_lifecycle_engine.evaluate(institutional_certification())
    result = oracle_universal_market_adapter_lifecycle_engine.lookup_adapter(report, "adp.crypto")

    assert result["found"] is True
    assert result["record"]["adapter_id"] == "adp.crypto"
    assert result["read_only"] is True
    assert result["execution_allowed"] is False


def test_empty_lifecycle():
    report = oracle_universal_market_adapter_lifecycle_engine.evaluate({
        "adapter_certification_batch_id": "empty",
        "records": [],
    })

    assert report["lifecycle_status"] == "empty_adapter_lifecycle"
    assert report["adapter_count"] == 0
    assert report["records"] == []
    assert report["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_institutional_lifecycle()
    test_active_review_lifecycle()
    test_blocked_lifecycle()
    test_lookup_adapter()
    test_empty_lifecycle()
    print("[PASS] OI-172 Oracle Universal Market Adapter Lifecycle Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .universal_market_adapter_lifecycle_engine import oracle_universal_market_adapter_lifecycle_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-172 INSTALLER")
    print(" Oracle Universal Market Adapter Lifecycle Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-172 installed")
    print("\nRun:")
    print("py test_oi_172_universal_market_adapter_lifecycle_engine.py")


if __name__ == "__main__":
    main()