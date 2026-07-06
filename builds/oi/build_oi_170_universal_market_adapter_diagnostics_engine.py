from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "universal_market_adapter_diagnostics_engine.py"
TEST = ROOT / "test_oi_170_universal_market_adapter_diagnostics_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-170 — Oracle Universal Market Adapter Diagnostics Engine

Read-only diagnostics engine for Universal Market Adapter health reports.

Purpose:
- Diagnose adapter health records into actionable institutional diagnostics.
- Identify critical adapters, warning pressure, degraded domains, safety failures,
  validation problems, and adapter readiness gaps.
- Preserve Oracle as a read-only intelligence system while Q Series owns execution.

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
class AdapterDiagnosticFinding:
    finding_id: str
    adapter_id: str
    domain: str
    severity: str
    code: str
    message: str
    recommendation: str
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"


@dataclass
class OracleUniversalMarketAdapterDiagnosticsEngine:
    name: str = "oracle_universal_market_adapter_diagnostics_engine"
    version: str = "OI-170"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    diagnostics_schema_version: str = "universal_market_adapter_diagnostics_v1"

    def diagnose_record(self, record: Dict[str, Any]) -> List[AdapterDiagnosticFinding]:
        record = _safe_dict(record)
        adapter_id = str(record.get("adapter_id") or "unknown_adapter")
        domain = str(record.get("domain") or "UNKNOWN").upper()
        health_score = _num(record.get("health_score"), 0.0)
        critical_count = int(_num(record.get("critical_count"), 0))
        warning_count = int(_num(record.get("warning_count"), 0))
        issue_count = int(_num(record.get("issue_count"), critical_count + warning_count))
        health_status = str(record.get("health_status") or "")
        validation_status = str(record.get("validation_status") or "")
        safety_status = str(record.get("safety_status") or "safety_confirmed")
        institutional_ready = record.get("institutional_ready") is True

        findings: List[AdapterDiagnosticFinding] = []

        def add(severity: str, code: str, message: str, recommendation: str) -> None:
            payload = {
                "adapter_id": adapter_id,
                "domain": domain,
                "severity": severity,
                "code": code,
                "message": message,
                "recommendation": recommendation,
            }
            findings.append(AdapterDiagnosticFinding(
                finding_id=_hash(payload),
                adapter_id=adapter_id,
                domain=domain,
                severity=severity,
                code=code,
                message=message,
                recommendation=recommendation,
                read_only=True,
                execution_allowed=False,
                execution_owner=self.execution_owner,
            ))

        if record.get("read_only") is not True:
            add(
                "critical",
                "read_only_contract_failure",
                "Adapter health record is not marked read_only=True.",
                "Block adapter promotion until read-only contract is restored.",
            )

        if record.get("execution_allowed") is not False:
            add(
                "critical",
                "execution_contract_failure",
                "Adapter health record allows execution.",
                "Block adapter promotion; Oracle adapters must never execute.",
            )

        if record.get("execution_owner") != "Q Series":
            add(
                "critical",
                "execution_owner_failure",
                "Adapter health record execution owner is not Q Series.",
                "Correct execution ownership metadata before institutional use.",
            )

        if safety_status != "safety_confirmed":
            add(
                "critical",
                "safety_status_failure",
                f"Adapter safety status is {safety_status}.",
                "Inspect adapter contract, validation packet, and health lineage.",
            )

        if critical_count > 0:
            add(
                "critical",
                "critical_validation_pressure",
                f"Adapter has {critical_count} critical validation issue(s).",
                "Repair adapter output mapping before downstream Oracle ingestion.",
            )

        if validation_status == "adapter_packet_invalid":
            add(
                "critical",
                "invalid_adapter_packet",
                "Adapter validation status is invalid.",
                "Rerun adapter contract and validation checks after correcting packet output.",
            )

        if warning_count > 0:
            add(
                "warning",
                "warning_validation_pressure",
                f"Adapter has {warning_count} warning issue(s).",
                "Review optional telemetry, supported domain status, and schema completeness.",
            )

        if health_score < 70:
            add(
                "warning",
                "adapter_health_below_threshold",
                f"Adapter health score is {health_score}.",
                "Keep adapter in review until health score improves above 70.",
            )

        if health_status in {"adapter_degraded", "adapter_unhealthy", "adapter_health_critical"}:
            add(
                "warning" if health_status != "adapter_health_critical" else "critical",
                "degraded_health_status",
                f"Adapter health status is {health_status}.",
                "Investigate adapter data quality, missing capabilities, and validation failures.",
            )

        if not institutional_ready and not findings:
            add(
                "info",
                "adapter_not_institutional_ready",
                "Adapter is healthy but not marked institutional ready.",
                "Confirm validation status, health score, and safety status before promotion.",
            )

        if not findings:
            add(
                "info",
                "adapter_diagnostics_clean",
                "Adapter diagnostics are clean.",
                "Adapter may remain active in read-only Oracle intelligence flow.",
            )

        return findings

    def diagnose(self, health_report: Dict[str, Any]) -> Dict[str, Any]:
        health_report = _safe_dict(health_report)
        records = _safe_list(health_report.get("records"))

        findings: List[AdapterDiagnosticFinding] = []
        for record in records:
            findings.extend(self.diagnose_record(_safe_dict(record)))

        severity_counts: Dict[str, int] = {}
        domain_counts: Dict[str, int] = {}
        adapter_counts: Dict[str, int] = {}
        code_counts: Dict[str, int] = {}

        for finding in findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
            domain_counts[finding.domain] = domain_counts.get(finding.domain, 0) + 1
            adapter_counts[finding.adapter_id] = adapter_counts.get(finding.adapter_id, 0) + 1
            code_counts[finding.code] = code_counts.get(finding.code, 0) + 1

        critical_count = severity_counts.get("critical", 0)
        warning_count = severity_counts.get("warning", 0)
        info_count = severity_counts.get("info", 0)

        if not records:
            diagnostics_status = "empty_adapter_diagnostics"
        elif critical_count:
            diagnostics_status = "adapter_diagnostics_critical"
        elif warning_count:
            diagnostics_status = "adapter_diagnostics_warnings"
        else:
            diagnostics_status = "adapter_diagnostics_clean"

        diagnostics_id = _hash({
            "source_adapter_health_report_id": health_report.get("adapter_health_report_id"),
            "diagnostics_status": diagnostics_status,
            "findings": [finding.__dict__ for finding in findings],
        })

        return {
            "module": self.name,
            "version": self.version,
            "diagnostics_schema_version": self.diagnostics_schema_version,
            "adapter_diagnostics_id": diagnostics_id,
            "diagnostics_status": diagnostics_status,
            "diagnosed_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "source_adapter_health_report_id": health_report.get("adapter_health_report_id"),
            "source_health_report_status": health_report.get("health_report_status"),
            "adapter_count": len(adapter_counts),
            "domain_count": len(domain_counts),
            "finding_count": len(findings),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "severity_counts": severity_counts,
            "domain_counts": domain_counts,
            "adapter_counts": adapter_counts,
            "code_counts": code_counts,
            "executive_summary": {
                "headline": (
                    "Universal Market adapter diagnostics are clean."
                    if diagnostics_status == "adapter_diagnostics_clean"
                    else f"Universal Market adapter diagnostics status: {diagnostics_status}."
                ),
                "adapter_diagnostics_id": diagnostics_id,
                "finding_count": len(findings),
                "critical_count": critical_count,
                "warning_count": warning_count,
                "operator_note": "Diagnostics are read-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "findings": [finding.__dict__ for finding in findings],
        }

    def lookup_adapter_findings(self, diagnostics: Dict[str, Any], adapter_id: str) -> Dict[str, Any]:
        diagnostics = _safe_dict(diagnostics)
        findings = _safe_list(diagnostics.get("findings"))
        target = str(adapter_id or "").strip().lower()

        matches = [
            _safe_dict(finding)
            for finding in findings
            if str(_safe_dict(finding).get("adapter_id") or "").strip().lower() == target
        ]

        return {
            "module": self.name,
            "version": self.version,
            "found": bool(matches),
            "adapter_id": adapter_id,
            "finding_count": len(matches),
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
            "findings": matches,
        }


oracle_universal_market_adapter_diagnostics_engine = OracleUniversalMarketAdapterDiagnosticsEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.universal_market_adapter_diagnostics_engine import (
    oracle_universal_market_adapter_diagnostics_engine,
)


def clean_health_report():
    return {
        "adapter_health_report_id": "health-001",
        "health_report_status": "adapter_health_institutional",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "records": [
            {
                "adapter_health_id": "adapter-health-001",
                "adapter_id": "adp.crypto",
                "domain": "CRYPTO",
                "health_score": 100.0,
                "health_status": "institutional_adapter_ready",
                "validation_status": "adapter_packet_valid",
                "issue_count": 0,
                "critical_count": 0,
                "warning_count": 0,
                "institutional_ready": True,
                "safety_status": "safety_confirmed",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            }
        ],
    }


def test_clean_diagnostics():
    diagnostics = oracle_universal_market_adapter_diagnostics_engine.diagnose(clean_health_report())

    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False
    assert diagnostics["execution_owner"] == "Q Series"
    assert diagnostics["diagnostics_status"] == "adapter_diagnostics_clean"
    assert diagnostics["critical_count"] == 0
    assert diagnostics["warning_count"] == 0
    assert diagnostics["info_count"] == 1
    assert diagnostics["findings"][0]["code"] == "adapter_diagnostics_clean"


def test_critical_diagnostics():
    report = clean_health_report()
    record = report["records"][0]
    record["critical_count"] = 1
    record["issue_count"] = 1
    record["health_score"] = 55.0
    record["health_status"] = "adapter_health_critical"
    record["validation_status"] = "adapter_packet_invalid"
    record["institutional_ready"] = False

    diagnostics = oracle_universal_market_adapter_diagnostics_engine.diagnose(report)

    assert diagnostics["diagnostics_status"] == "adapter_diagnostics_critical"
    assert diagnostics["critical_count"] >= 1
    assert any(finding["code"] == "critical_validation_pressure" for finding in diagnostics["findings"])
    assert any(finding["code"] == "invalid_adapter_packet" for finding in diagnostics["findings"])


def test_warning_diagnostics():
    report = clean_health_report()
    record = report["records"][0]
    record["warning_count"] = 2
    record["issue_count"] = 2
    record["health_score"] = 82.0
    record["health_status"] = "adapter_watch"
    record["institutional_ready"] = False

    diagnostics = oracle_universal_market_adapter_diagnostics_engine.diagnose(report)

    assert diagnostics["diagnostics_status"] == "adapter_diagnostics_warnings"
    assert diagnostics["warning_count"] >= 1
    assert any(finding["code"] == "warning_validation_pressure" for finding in diagnostics["findings"])


def test_safety_failure_diagnostics():
    report = clean_health_report()
    record = report["records"][0]
    record["execution_allowed"] = True
    record["safety_status"] = "safety_failed_execution_allowed"

    diagnostics = oracle_universal_market_adapter_diagnostics_engine.diagnose(report)

    assert diagnostics["diagnostics_status"] == "adapter_diagnostics_critical"
    assert any(finding["code"] == "execution_contract_failure" for finding in diagnostics["findings"])
    assert any(finding["code"] == "safety_status_failure" for finding in diagnostics["findings"])


def test_lookup_adapter_findings():
    diagnostics = oracle_universal_market_adapter_diagnostics_engine.diagnose(clean_health_report())
    lookup = oracle_universal_market_adapter_diagnostics_engine.lookup_adapter_findings(diagnostics, "adp.crypto")

    assert lookup["found"] is True
    assert lookup["finding_count"] == 1
    assert lookup["findings"][0]["adapter_id"] == "adp.crypto"
    assert lookup["read_only"] is True


if __name__ == "__main__":
    test_clean_diagnostics()
    test_critical_diagnostics()
    test_warning_diagnostics()
    test_safety_failure_diagnostics()
    test_lookup_adapter_findings()
    print("[PASS] OI-170 Oracle Universal Market Adapter Diagnostics Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .universal_market_adapter_diagnostics_engine import oracle_universal_market_adapter_diagnostics_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-170 INSTALLER")
    print(" Oracle Universal Market Adapter Diagnostics Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-170 installed")
    print("\nRun:")
    print("py test_oi_170_universal_market_adapter_diagnostics_engine.py")


if __name__ == "__main__":
    main()