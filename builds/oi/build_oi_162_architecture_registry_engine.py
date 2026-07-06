from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "architecture_registry_engine.py"
TEST = ROOT / "test_oi_162_architecture_registry_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-162 — Oracle Architecture Registry Engine

Read-only architecture registry for Oracle Intelligence.

Purpose:
- Register institutional Oracle modules and architecture layers.
- Preserve module ownership, read-only constraints, execution boundaries,
  lifecycle phase, and Universal Market Model readiness.
- Provide registry reports for the Architecture Manual and future terminal views.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _stable_text(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(f"{k}:{_stable_text(value[k])}" for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _hash(value: Any, size: int = 24) -> str:
    return sha256(_stable_text(value).encode("utf-8")).hexdigest()[:size]


@dataclass
class ArchitectureRegistryRecord:
    registry_record_id: str
    module_id: str
    module_name: str
    architecture_layer: str
    lifecycle_phase: str
    ownership: str
    read_only: bool
    execution_allowed: bool
    execution_owner: str
    universal_market_model_ready: bool
    adapter_ready: bool
    replayable: bool
    explainable: bool
    institutional_status: str
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    lineage_hash: str = ""


@dataclass
class OracleArchitectureRegistryEngine:
    name: str = "oracle_architecture_registry_engine"
    version: str = "OI-162"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    registry_schema_version: str = "architecture_registry_v1"

    permanent_principles: List[str] = field(default_factory=lambda: [
        "Oracle is strictly read-only.",
        "Q Series is the only execution engine.",
        "Universal Market Model for all data.",
        "Adapter-based expansion.",
        "Event-driven intelligence.",
        "Explainability by default.",
        "Replayability by default.",
        "Historical memory is permanent.",
        "Institutional telemetry.",
        "Strategy-agnostic Q Series.",
        "Single responsibility per module.",
        "Architecture Registry and Architecture Manual maintained as platform grows.",
    ])

    supported_domains: List[str] = field(default_factory=lambda: [
        "PREDICTION_MARKETS",
        "CRYPTO",
        "STOCKS",
        "ETFS",
        "FUTURES",
        "COMMODITIES",
        "FOREX",
        "MACROECONOMICS",
        "WEATHER",
        "NEWS",
        "ALTERNATIVE_DATA",
    ])

    def classify_status(self, module: Dict[str, Any]) -> str:
        module = _safe_dict(module)

        if module.get("read_only") is not True:
            return "blocked_read_only_violation"
        if module.get("execution_allowed") is not False:
            return "blocked_execution_violation"
        if module.get("execution_owner") != "Q Series":
            return "blocked_execution_owner_violation"

        if module.get("replayable") and module.get("explainable") and module.get("universal_market_model_ready"):
            return "institutional_registered"

        if module.get("explainable") and module.get("read_only"):
            return "registered_with_review"

        return "registered_limited"

    def register_module(self, module: Dict[str, Any]) -> ArchitectureRegistryRecord:
        module = _safe_dict(module)

        module_id = str(module.get("module_id") or module.get("version") or _hash(module, 12))
        module_name = str(module.get("module_name") or module.get("name") or "unknown_oracle_module")
        architecture_layer = str(module.get("architecture_layer") or "Oracle Intelligence")
        lifecycle_phase = str(module.get("lifecycle_phase") or "production")
        ownership = str(module.get("ownership") or "Oracle Intelligence")

        record_payload = {
            "module_id": module_id,
            "module_name": module_name,
            "architecture_layer": architecture_layer,
            "lifecycle_phase": lifecycle_phase,
            "ownership": ownership,
            "read_only": module.get("read_only", True),
            "execution_allowed": module.get("execution_allowed", False),
            "execution_owner": module.get("execution_owner", "Q Series"),
        }

        lineage_hash = _hash(record_payload)

        return ArchitectureRegistryRecord(
            registry_record_id=_hash({"record": record_payload, "lineage": lineage_hash}),
            module_id=module_id,
            module_name=module_name,
            architecture_layer=architecture_layer,
            lifecycle_phase=lifecycle_phase,
            ownership=ownership,
            read_only=module.get("read_only", True) is True,
            execution_allowed=module.get("execution_allowed", False) is True,
            execution_owner=str(module.get("execution_owner") or "Q Series"),
            universal_market_model_ready=module.get("universal_market_model_ready", True) is True,
            adapter_ready=module.get("adapter_ready", False) is True,
            replayable=module.get("replayable", True) is True,
            explainable=module.get("explainable", True) is True,
            institutional_status=self.classify_status(module),
            dependencies=[str(x) for x in _safe_list(module.get("dependencies"))],
            tags=[str(x) for x in _safe_list(module.get("tags"))],
            lineage_hash=lineage_hash,
        )

    def build_registry(self, modules: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        records = [self.register_module(module) for module in modules]
        records.sort(key=lambda r: r.module_id)

        layer_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}
        phase_counts: Dict[str, int] = {}

        violation_count = 0
        replayable_count = 0
        explainable_count = 0
        umm_count = 0

        for record in records:
            layer_counts[record.architecture_layer] = layer_counts.get(record.architecture_layer, 0) + 1
            status_counts[record.institutional_status] = status_counts.get(record.institutional_status, 0) + 1
            phase_counts[record.lifecycle_phase] = phase_counts.get(record.lifecycle_phase, 0) + 1

            if "blocked" in record.institutional_status:
                violation_count += 1
            if record.replayable:
                replayable_count += 1
            if record.explainable:
                explainable_count += 1
            if record.universal_market_model_ready:
                umm_count += 1

        registry_id = _hash([record.__dict__ for record in records])

        if not records:
            registry_status = "empty_architecture_registry"
        elif violation_count:
            registry_status = "architecture_registry_blocked"
        else:
            registry_status = "architecture_registry_ready"

        return {
            "module": self.name,
            "version": self.version,
            "registry_schema_version": self.registry_schema_version,
            "architecture_registry_id": registry_id,
            "registry_status": registry_status,
            "created_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "supported_domains": list(self.supported_domains),
            "permanent_principles": list(self.permanent_principles),
            "record_count": len(records),
            "violation_count": violation_count,
            "replayable_count": replayable_count,
            "explainable_count": explainable_count,
            "universal_market_model_ready_count": umm_count,
            "layer_counts": layer_counts,
            "status_counts": status_counts,
            "phase_counts": phase_counts,
            "executive_summary": {
                "headline": (
                    "Oracle architecture registry is ready."
                    if registry_status == "architecture_registry_ready"
                    else f"Oracle architecture registry status: {registry_status}."
                ),
                "architecture_registry_id": registry_id,
                "record_count": len(records),
                "violation_count": violation_count,
                "operator_note": "Oracle remains read-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "records": [record.__dict__ for record in records],
        }

    def lookup_module(self, registry: Dict[str, Any], module_id: str) -> Dict[str, Any]:
        registry = _safe_dict(registry)
        records = _safe_list(registry.get("records"))
        target = str(module_id or "").strip().lower()

        for record in records:
            record = _safe_dict(record)
            if str(record.get("module_id") or "").strip().lower() == target:
                return {
                    "module": self.name,
                    "version": self.version,
                    "found": True,
                    "module_id": module_id,
                    "record": record,
                    "read_only": True,
                    "execution_allowed": False,
                    "execution_owner": self.execution_owner,
                }

        return {
            "module": self.name,
            "version": self.version,
            "found": False,
            "module_id": module_id,
            "record": None,
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }


oracle_architecture_registry_engine = OracleArchitectureRegistryEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.architecture_registry_engine import (
    oracle_architecture_registry_engine,
)


def sample_modules():
    return [
        {
            "module_id": "OI-155",
            "module_name": "Oracle Historical Replay Engine",
            "architecture_layer": "Historical Intelligence",
            "lifecycle_phase": "production",
            "ownership": "Oracle Intelligence",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "universal_market_model_ready": True,
            "adapter_ready": False,
            "replayable": True,
            "explainable": True,
            "dependencies": ["OI-154"],
            "tags": ["historical", "replay"],
        },
        {
            "module_id": "OI-160",
            "module_name": "Oracle Alpha Integration Test Engine",
            "architecture_layer": "Institutional Validation",
            "lifecycle_phase": "production",
            "ownership": "Oracle Intelligence",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "universal_market_model_ready": True,
            "adapter_ready": False,
            "replayable": True,
            "explainable": True,
            "dependencies": ["OI-155", "OI-156", "OI-157", "OI-158", "OI-159"],
            "tags": ["alpha", "integration"],
        },
    ]


def test_registry_builds_successfully():
    registry = oracle_architecture_registry_engine.build_registry(sample_modules())

    assert registry["read_only"] is True
    assert registry["execution_allowed"] is False
    assert registry["execution_owner"] == "Q Series"
    assert registry["registry_status"] == "architecture_registry_ready"
    assert registry["record_count"] == 2
    assert registry["violation_count"] == 0
    assert registry["replayable_count"] == 2
    assert registry["explainable_count"] == 2


def test_registry_blocks_execution_violation():
    modules = sample_modules()
    modules[0]["execution_allowed"] = True

    registry = oracle_architecture_registry_engine.build_registry(modules)

    assert registry["registry_status"] == "architecture_registry_blocked"
    assert registry["violation_count"] == 1
    assert registry["records"][0]["institutional_status"] == "blocked_execution_violation"


def test_lookup_module_found():
    registry = oracle_architecture_registry_engine.build_registry(sample_modules())
    result = oracle_architecture_registry_engine.lookup_module(registry, "OI-160")

    assert result["found"] is True
    assert result["read_only"] is True
    assert result["execution_allowed"] is False
    assert result["record"]["module_id"] == "OI-160"


def test_lookup_module_missing():
    registry = oracle_architecture_registry_engine.build_registry(sample_modules())
    result = oracle_architecture_registry_engine.lookup_module(registry, "OI-999")

    assert result["found"] is False
    assert result["record"] is None
    assert result["execution_owner"] == "Q Series"


def test_empty_registry():
    registry = oracle_architecture_registry_engine.build_registry([])

    assert registry["registry_status"] == "empty_architecture_registry"
    assert registry["record_count"] == 0
    assert registry["records"] == []
    assert registry["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_registry_builds_successfully()
    test_registry_blocks_execution_violation()
    test_lookup_module_found()
    test_lookup_module_missing()
    test_empty_registry()
    print("[PASS] OI-162 Oracle Architecture Registry Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .architecture_registry_engine import oracle_architecture_registry_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-162 INSTALLER")
    print(" Oracle Architecture Registry Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-162 installed")
    print("\nRun:")
    print("py test_oi_162_architecture_registry_engine.py")


if __name__ == "__main__":
    main()