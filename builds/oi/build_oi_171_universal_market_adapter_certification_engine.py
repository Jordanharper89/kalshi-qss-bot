from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "universal_market_adapter_certification_engine.py"
TEST = ROOT / "test_oi_171_universal_market_adapter_certification_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-171 — Oracle Universal Market Adapter Certification Engine

Read-only certification engine for Universal Market Adapter diagnostics.

Purpose:
- Certify adapters after contract, validation, telemetry, health, and diagnostics.
- Confirm institutional readiness, safety, UMM compatibility, replayability,
  explainability, and read-only boundaries.
- Produce adapter certification packets for future Oracle Market OS layers.

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
class AdapterCertificationRecord:
    certification_id: str
    adapter_id: str
    domain: str
    certification_score: float
    certification_tier: str
    certification_status: str
    diagnostics_status: str
    finding_count: int
    critical_count: int
    warning_count: int
    certified: bool
    certification_note: str
    lineage_hash: str
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"


@dataclass
class OracleUniversalMarketAdapterCertificationEngine:
    name: str = "oracle_universal_market_adapter_certification_engine"
    version: str = "OI-171"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    certification_schema_version: str = "universal_market_adapter_certification_v1"

    def classify_tier(self, score: float, critical_count: int) -> str:
        if critical_count > 0:
            return "certification_blocked"
        if score >= 95:
            return "institutional_certification"
        if score >= 85:
            return "production_certification"
        if score >= 75:
            return "review_certification"
        return "limited_certification"

    def classify_status(self, score: float, critical_count: int, warning_count: int) -> str:
        if critical_count > 0:
            return "adapter_certification_blocked"
        if score >= 95 and warning_count == 0:
            return "adapter_institutionally_certified"
        if score >= 85:
            return "adapter_certified"
        if score >= 75:
            return "adapter_certified_with_review"
        return "adapter_not_certified"

    def certify_adapter(self, adapter_id: str, domain: str, findings: List[Dict[str, Any]]) -> AdapterCertificationRecord:
        critical_count = sum(1 for f in findings if _safe_dict(f).get("severity") == "critical")
        warning_count = sum(1 for f in findings if _safe_dict(f).get("severity") == "warning")
        finding_count = len(findings)

        clean_only = finding_count == 1 and _safe_dict(findings[0]).get("code") == "adapter_diagnostics_clean"
        score = 100.0

        if critical_count:
            score -= min(critical_count * 35, 80)
        if warning_count:
            score -= min(warning_count * 10, 40)
        if finding_count and not clean_only:
            score -= min(finding_count * 2, 15)

        score = round(max(0.0, min(100.0, score)), 2)
        tier = self.classify_tier(score, critical_count)
        status = self.classify_status(score, critical_count, warning_count)
        certified = status in {
            "adapter_institutionally_certified",
            "adapter_certified",
            "adapter_certified_with_review",
        }

        payload = {
            "adapter_id": adapter_id,
            "domain": domain,
            "score": score,
            "tier": tier,
            "status": status,
            "finding_count": finding_count,
            "critical_count": critical_count,
            "warning_count": warning_count,
        }
        lineage_hash = _hash(payload)

        return AdapterCertificationRecord(
            certification_id=_hash({"payload": payload, "lineage": lineage_hash}),
            adapter_id=adapter_id,
            domain=domain,
            certification_score=score,
            certification_tier=tier,
            certification_status=status,
            diagnostics_status="adapter_diagnostics_clean" if clean_only else "adapter_diagnostics_reviewed",
            finding_count=finding_count,
            critical_count=critical_count,
            warning_count=warning_count,
            certified=certified,
            certification_note=(
                f"{adapter_id} certified for {domain} with score {score}."
                if certified else
                f"{adapter_id} certification blocked or incomplete for {domain}."
            ) + " Oracle certification is read-only; Q Series owns execution.",
            lineage_hash=lineage_hash,
            read_only=True,
            execution_allowed=False,
            execution_owner=self.execution_owner,
        )

    def certify(self, diagnostics: Dict[str, Any]) -> Dict[str, Any]:
        diagnostics = _safe_dict(diagnostics)
        findings = [_safe_dict(f) for f in _safe_list(diagnostics.get("findings"))]

        grouped: Dict[str, List[Dict[str, Any]]] = {}
        domains: Dict[str, str] = {}

        for finding in findings:
            adapter_id = str(finding.get("adapter_id") or "unknown_adapter")
            domain = str(finding.get("domain") or "UNKNOWN").upper()
            grouped.setdefault(adapter_id, []).append(finding)
            domains[adapter_id] = domain

        records = [
            self.certify_adapter(adapter_id, domains.get(adapter_id, "UNKNOWN"), group)
            for adapter_id, group in grouped.items()
        ]
        records.sort(key=lambda r: (r.domain, r.adapter_id))

        certified_count = sum(1 for r in records if r.certified)
        blocked_count = sum(1 for r in records if r.certification_status == "adapter_certification_blocked")
        warning_count = sum(r.warning_count for r in records)
        critical_count = sum(r.critical_count for r in records)

        tier_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}
        domain_counts: Dict[str, int] = {}

        for record in records:
            tier_counts[record.certification_tier] = tier_counts.get(record.certification_tier, 0) + 1
            status_counts[record.certification_status] = status_counts.get(record.certification_status, 0) + 1
            domain_counts[record.domain] = domain_counts.get(record.domain, 0) + 1

        avg_score = round(sum(r.certification_score for r in records) / len(records), 2) if records else 0.0

        if not records:
            certification_status = "empty_adapter_certification"
        elif blocked_count:
            certification_status = "adapter_certification_blocked"
        elif certified_count == len(records) and avg_score >= 95 and warning_count == 0:
            certification_status = "adapter_certification_institutional"
        elif certified_count == len(records):
            certification_status = "adapter_certification_ready"
        else:
            certification_status = "adapter_certification_review_required"

        batch_id = _hash({
            "source_diagnostics_id": diagnostics.get("adapter_diagnostics_id"),
            "status": certification_status,
            "records": [r.__dict__ for r in records],
        })

        return {
            "module": self.name,
            "version": self.version,
            "certification_schema_version": self.certification_schema_version,
            "adapter_certification_batch_id": batch_id,
            "certification_status": certification_status,
            "certified_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "source_adapter_diagnostics_id": diagnostics.get("adapter_diagnostics_id"),
            "source_diagnostics_status": diagnostics.get("diagnostics_status"),
            "adapter_count": len(records),
            "certified_count": certified_count,
            "blocked_count": blocked_count,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "average_certification_score": avg_score,
            "tier_counts": tier_counts,
            "status_counts": status_counts,
            "domain_counts": domain_counts,
            "executive_summary": {
                "headline": (
                    "Universal Market adapters are institutionally certified."
                    if certification_status == "adapter_certification_institutional"
                    else f"Universal Market adapter certification status: {certification_status}."
                ),
                "adapter_certification_batch_id": batch_id,
                "adapter_count": len(records),
                "certified_count": certified_count,
                "blocked_count": blocked_count,
                "average_certification_score": avg_score,
                "operator_note": "Certification is read-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "records": [r.__dict__ for r in records],
        }

    def lookup_certification(self, certification: Dict[str, Any], adapter_id: str) -> Dict[str, Any]:
        certification = _safe_dict(certification)
        records = _safe_list(certification.get("records"))
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


oracle_universal_market_adapter_certification_engine = OracleUniversalMarketAdapterCertificationEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.universal_market_adapter_certification_engine import (
    oracle_universal_market_adapter_certification_engine,
)


def clean_diagnostics():
    return {
        "adapter_diagnostics_id": "diag-001",
        "diagnostics_status": "adapter_diagnostics_clean",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "findings": [
            {
                "finding_id": "find-001",
                "adapter_id": "adp.crypto",
                "domain": "CRYPTO",
                "severity": "info",
                "code": "adapter_diagnostics_clean",
                "message": "Adapter diagnostics are clean.",
                "recommendation": "Adapter may remain active.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            }
        ],
    }


def test_clean_certification():
    cert = oracle_universal_market_adapter_certification_engine.certify(clean_diagnostics())

    assert cert["read_only"] is True
    assert cert["execution_allowed"] is False
    assert cert["execution_owner"] == "Q Series"
    assert cert["certification_status"] == "adapter_certification_institutional"
    assert cert["adapter_count"] == 1
    assert cert["certified_count"] == 1
    assert cert["blocked_count"] == 0
    assert cert["records"][0]["certified"] is True


def test_warning_certification_ready():
    diag = clean_diagnostics()
    diag["findings"].append({
        "finding_id": "find-002",
        "adapter_id": "adp.crypto",
        "domain": "CRYPTO",
        "severity": "warning",
        "code": "warning_validation_pressure",
        "message": "Warning pressure.",
        "recommendation": "Review warnings.",
    })

    cert = oracle_universal_market_adapter_certification_engine.certify(diag)

    assert cert["certification_status"] == "adapter_certification_ready"
    assert cert["warning_count"] == 1
    assert cert["records"][0]["certified"] is True


def test_critical_certification_blocked():
    diag = clean_diagnostics()
    diag["findings"].append({
        "finding_id": "find-003",
        "adapter_id": "adp.crypto",
        "domain": "CRYPTO",
        "severity": "critical",
        "code": "execution_contract_failure",
        "message": "Execution contract failed.",
        "recommendation": "Block adapter.",
    })

    cert = oracle_universal_market_adapter_certification_engine.certify(diag)

    assert cert["certification_status"] == "adapter_certification_blocked"
    assert cert["blocked_count"] == 1
    assert cert["critical_count"] == 1
    assert cert["records"][0]["certified"] is False


def test_lookup_certification():
    cert = oracle_universal_market_adapter_certification_engine.certify(clean_diagnostics())
    result = oracle_universal_market_adapter_certification_engine.lookup_certification(cert, "adp.crypto")

    assert result["found"] is True
    assert result["record"]["adapter_id"] == "adp.crypto"
    assert result["read_only"] is True
    assert result["execution_allowed"] is False


def test_empty_certification():
    cert = oracle_universal_market_adapter_certification_engine.certify({
        "adapter_diagnostics_id": "empty",
        "diagnostics_status": "empty_adapter_diagnostics",
        "findings": [],
    })

    assert cert["certification_status"] == "empty_adapter_certification"
    assert cert["adapter_count"] == 0
    assert cert["records"] == []
    assert cert["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_clean_certification()
    test_warning_certification_ready()
    test_critical_certification_blocked()
    test_lookup_certification()
    test_empty_certification()
    print("[PASS] OI-171 Oracle Universal Market Adapter Certification Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .universal_market_adapter_certification_engine import oracle_universal_market_adapter_certification_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-171 INSTALLER")
    print(" Oracle Universal Market Adapter Certification Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-171 installed")
    print("\nRun:")
    print("py test_oi_171_universal_market_adapter_certification_engine.py")


if __name__ == "__main__":
    main()