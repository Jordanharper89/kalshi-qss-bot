from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "universal_market_adapter_health_engine.py"
TEST = ROOT / "test_oi_169_universal_market_adapter_health_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-169 — Oracle Universal Market Adapter Health Engine

Read-only health engine for Universal Market Adapter telemetry.

Purpose:
- Convert adapter telemetry into institutional adapter health reports.
- Track adapter health scores, domain health, critical/warning pressure,
  degraded adapters, institutional readiness, and safety adherence.
- Keep Oracle universal, read-only, replayable, and explainable.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List


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
class AdapterHealthRecord:
    adapter_health_id: str
    adapter_id: str
    domain: str
    health_score: float
    health_status: str
    validation_status: str
    issue_count: int
    critical_count: int
    warning_count: int
    institutional_ready: bool
    safety_status: str
    lineage_hash: str
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"


@dataclass
class OracleUniversalMarketAdapterHealthEngine:
    name: str = "oracle_universal_market_adapter_health_engine"
    version: str = "OI-169"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    health_schema_version: str = "universal_market_adapter_health_v1"

    def classify_health(self, score: float, critical_count: int = 0) -> str:
        if critical_count > 0:
            return "adapter_health_critical"
        if score >= 95:
            return "institutional_adapter_ready"
        if score >= 85:
            return "adapter_healthy"
        if score >= 70:
            return "adapter_watch"
        if score >= 50:
            return "adapter_degraded"
        return "adapter_unhealthy"

    def classify_safety(self, record: Dict[str, Any]) -> str:
        record = _safe_dict(record)
        if record.get("read_only") is not True:
            return "safety_failed_read_only"
        if record.get("execution_allowed") is not False:
            return "safety_failed_execution_allowed"
        if record.get("execution_owner") != "Q Series":
            return "safety_failed_execution_owner"
        return "safety_confirmed"

    def build_health_record(self, telemetry_record: Dict[str, Any]) -> AdapterHealthRecord:
        record = _safe_dict(telemetry_record)

        adapter_id = str(record.get("adapter_id") or "unknown_adapter")
        domain = str(record.get("domain") or "UNKNOWN").upper()
        health_score = round(_num(record.get("health_score")), 2)
        critical_count = int(_num(record.get("critical_count"), 0))
        warning_count = int(_num(record.get("warning_count"), 0))
        issue_count = int(_num(record.get("issue_count"), critical_count + warning_count))
        validation_status = str(record.get("validation_status") or "unknown_validation_status")
        safety_status = self.classify_safety({
            "read_only": record.get("read_only", True),
            "execution_allowed": record.get("execution_allowed", False),
            "execution_owner": record.get("execution_owner", "Q Series"),
        })
        health_status = self.classify_health(health_score, critical_count)
        institutional_ready = (
            health_status == "institutional_adapter_ready"
            and safety_status == "safety_confirmed"
            and validation_status == "adapter_packet_valid"
        )

        payload = {
            "adapter_id": adapter_id,
            "domain": domain,
            "health_score": health_score,
            "validation_status": validation_status,
            "issue_count": issue_count,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "safety_status": safety_status,
            "source_lineage": record.get("lineage_hash") or record.get("telemetry_record_id"),
        }

        lineage_hash = _hash(payload)

        return AdapterHealthRecord(
            adapter_health_id=_hash({"payload": payload, "lineage": lineage_hash}),
            adapter_id=adapter_id,
            domain=domain,
            health_score=health_score,
            health_status=health_status,
            validation_status=validation_status,
            issue_count=issue_count,
            critical_count=critical_count,
            warning_count=warning_count,
            institutional_ready=institutional_ready,
            safety_status=safety_status,
            lineage_hash=lineage_hash,
            read_only=True,
            execution_allowed=False,
            execution_owner=self.execution_owner,
        )

    def evaluate(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        telemetry = _safe_dict(telemetry)
        telemetry_records = _safe_list(telemetry.get("records"))

        health_records = [self.build_health_record(record) for record in telemetry_records]
        health_records.sort(key=lambda r: (r.domain, r.adapter_id))

        adapter_counts: Dict[str, int] = {}
        domain_counts: Dict[str, int] = {}
        health_status_counts: Dict[str, int] = {}
        safety_status_counts: Dict[str, int] = {}

        total_score = 0.0
        total_issues = 0
        total_critical = 0
        total_warnings = 0
        institutional_ready_count = 0

        for record in health_records:
            adapter_counts[record.adapter_id] = adapter_counts.get(record.adapter_id, 0) + 1
            domain_counts[record.domain] = domain_counts.get(record.domain, 0) + 1
            health_status_counts[record.health_status] = health_status_counts.get(record.health_status, 0) + 1
            safety_status_counts[record.safety_status] = safety_status_counts.get(record.safety_status, 0) + 1
            total_score += record.health_score
            total_issues += record.issue_count
            total_critical += record.critical_count
            total_warnings += record.warning_count
            if record.institutional_ready:
                institutional_ready_count += 1

        average_health_score = round(total_score / len(health_records), 2) if health_records else 0.0

        if not health_records:
            health_report_status = "empty_adapter_health_report"
        elif total_critical > 0:
            health_report_status = "adapter_health_critical"
        elif institutional_ready_count == len(health_records) and average_health_score >= 95:
            health_report_status = "adapter_health_institutional"
        elif total_warnings > 0:
            health_report_status = "adapter_health_ready_with_warnings"
        elif average_health_score >= 85:
            health_report_status = "adapter_health_ready"
        else:
            health_report_status = "adapter_health_review_required"

        health_report_id = _hash({
            "source_telemetry_id": telemetry.get("adapter_telemetry_id"),
            "average_health_score": average_health_score,
            "health_report_status": health_report_status,
            "records": [record.__dict__ for record in health_records],
        })

        return {
            "module": self.name,
            "version": self.version,
            "health_schema_version": self.health_schema_version,
            "adapter_health_report_id": health_report_id,
            "health_report_status": health_report_status,
            "evaluated_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "source_adapter_telemetry_id": telemetry.get("adapter_telemetry_id"),
            "source_telemetry_status": telemetry.get("telemetry_status"),
            "adapter_count": len(adapter_counts),
            "domain_count": len(domain_counts),
            "health_record_count": len(health_records),
            "institutional_ready_count": institutional_ready_count,
            "total_issue_count": total_issues,
            "total_critical_count": total_critical,
            "total_warning_count": total_warnings,
            "average_health_score": average_health_score,
            "adapter_counts": adapter_counts,
            "domain_counts": domain_counts,
            "health_status_counts": health_status_counts,
            "safety_status_counts": safety_status_counts,
            "executive_summary": {
                "headline": (
                    "Universal Market adapter health is institutional."
                    if health_report_status == "adapter_health_institutional"
                    else f"Universal Market adapter health status: {health_report_status}."
                ),
                "adapter_health_report_id": health_report_id,
                "adapter_count": len(adapter_counts),
                "domain_count": len(domain_counts),
                "average_health_score": average_health_score,
                "institutional_ready_count": institutional_ready_count,
                "operator_note": "Adapter health is intelligence-only. Oracle remains read-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "records": [record.__dict__ for record in health_records],
        }

    def lookup_adapter(self, health_report: Dict[str, Any], adapter_id: str) -> Dict[str, Any]:
        health_report = _safe_dict(health_report)
        records = _safe_list(health_report.get("records"))
        target = str(adapter_id or "").strip().lower()

        matches = [
            _safe_dict(record)
            for record in records
            if str(_safe_dict(record).get("adapter_id") or "").strip().lower() == target
        ]

        if not matches:
            return {
                "module": self.name,
                "version": self.version,
                "found": False,
                "adapter_id": adapter_id,
                "records": [],
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            }

        avg = round(sum(_num(record.get("health_score")) for record in matches) / len(matches), 2)

        return {
            "module": self.name,
            "version": self.version,
            "found": True,
            "adapter_id": adapter_id,
            "average_health_score": avg,
            "health_status": self.classify_health(
                avg,
                sum(int(_num(record.get("critical_count"), 0)) for record in matches),
            ),
            "records": matches,
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }


oracle_universal_market_adapter_health_engine = OracleUniversalMarketAdapterHealthEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.universal_market_adapter_health_engine import (
    oracle_universal_market_adapter_health_engine,
)


def telemetry():
    return {
        "adapter_telemetry_id": "tel-001",
        "telemetry_status": "adapter_telemetry_institutional",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "records": [
            {
                "telemetry_record_id": "tel-rec-001",
                "adapter_id": "adp.crypto",
                "domain": "CRYPTO",
                "validation_status": "adapter_packet_valid",
                "record_count": 3,
                "issue_count": 0,
                "critical_count": 0,
                "warning_count": 0,
                "health_score": 100.0,
                "health_status": "institutional_adapter_health",
                "lineage_hash": "abc123",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            }
        ],
    }


def test_health_report_institutional():
    report = oracle_universal_market_adapter_health_engine.evaluate(telemetry())

    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["health_report_status"] == "adapter_health_institutional"
    assert report["adapter_count"] == 1
    assert report["domain_count"] == 1
    assert report["institutional_ready_count"] == 1
    assert report["average_health_score"] == 100.0


def test_warning_health_report():
    data = telemetry()
    data["records"][0]["warning_count"] = 2
    data["records"][0]["issue_count"] = 2
    data["records"][0]["health_score"] = 88.0

    report = oracle_universal_market_adapter_health_engine.evaluate(data)

    assert report["health_report_status"] == "adapter_health_ready_with_warnings"
    assert report["total_warning_count"] == 2
    assert report["total_critical_count"] == 0


def test_critical_health_report():
    data = telemetry()
    data["records"][0]["critical_count"] = 1
    data["records"][0]["issue_count"] = 1
    data["records"][0]["health_score"] = 55.0
    data["records"][0]["validation_status"] = "adapter_packet_invalid"

    report = oracle_universal_market_adapter_health_engine.evaluate(data)

    assert report["health_report_status"] == "adapter_health_critical"
    assert report["total_critical_count"] == 1
    assert report["records"][0]["health_status"] == "adapter_health_critical"


def test_lookup_adapter():
    report = oracle_universal_market_adapter_health_engine.evaluate(telemetry())
    lookup = oracle_universal_market_adapter_health_engine.lookup_adapter(report, "adp.crypto")

    assert lookup["found"] is True
    assert lookup["adapter_id"] == "adp.crypto"
    assert lookup["average_health_score"] == 100.0
    assert lookup["read_only"] is True
    assert lookup["execution_allowed"] is False


def test_empty_health_report():
    report = oracle_universal_market_adapter_health_engine.evaluate({
        "adapter_telemetry_id": "empty",
        "records": [],
    })

    assert report["health_report_status"] == "empty_adapter_health_report"
    assert report["health_record_count"] == 0
    assert report["records"] == []
    assert report["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_health_report_institutional()
    test_warning_health_report()
    test_critical_health_report()
    test_lookup_adapter()
    test_empty_health_report()
    print("[PASS] OI-169 Oracle Universal Market Adapter Health Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .universal_market_adapter_health_engine import oracle_universal_market_adapter_health_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-169 INSTALLER")
    print(" Oracle Universal Market Adapter Health Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-169 installed")
    print("\nRun:")
    print("py test_oi_169_universal_market_adapter_health_engine.py")


if __name__ == "__main__":
    main()