from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "architecture_manual_engine.py"
TEST = ROOT / "test_oi_163_architecture_manual_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-163 — Oracle Architecture Manual Engine

Read-only architecture manual generator for Oracle Intelligence.

Purpose:
- Convert architecture registry output into an institutional architecture manual.
- Preserve permanent principles, module registry records, ownership boundaries,
  Universal Market Model readiness, replayability, explainability, and safety notes.
- Support future Oracle Terminal documentation views.

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


def _stable_text(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(f"{k}:{_stable_text(value[k])}" for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _hash(value: Any, size: int = 24) -> str:
    return sha256(_stable_text(value).encode("utf-8")).hexdigest()[:size]


@dataclass
class ArchitectureManualSection:
    section_id: str
    title: str
    section_type: str
    content: Dict[str, Any]
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"


@dataclass
class OracleArchitectureManualEngine:
    name: str = "oracle_architecture_manual_engine"
    version: str = "OI-163"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    manual_schema_version: str = "architecture_manual_v1"

    def _section(self, title: str, section_type: str, content: Dict[str, Any]) -> ArchitectureManualSection:
        payload = {
            "title": title,
            "section_type": section_type,
            "content": content,
        }
        return ArchitectureManualSection(
            section_id=_hash(payload),
            title=title,
            section_type=section_type,
            content=content,
            read_only=True,
            execution_allowed=False,
            execution_owner=self.execution_owner,
        )

    def generate_manual(self, registry: Dict[str, Any]) -> Dict[str, Any]:
        registry = _safe_dict(registry)
        records = _safe_list(registry.get("records"))
        principles = _safe_list(registry.get("permanent_principles"))
        supported_domains = _safe_list(registry.get("supported_domains"))

        layer_map: Dict[str, List[Dict[str, Any]]] = {}
        for record in records:
            record = _safe_dict(record)
            layer = str(record.get("architecture_layer") or "Unknown Layer")
            layer_map.setdefault(layer, []).append(record)

        layer_sections = []
        for layer, layer_records in sorted(layer_map.items()):
            layer_sections.append({
                "layer": layer,
                "module_count": len(layer_records),
                "modules": [
                    {
                        "module_id": r.get("module_id"),
                        "module_name": r.get("module_name"),
                        "institutional_status": r.get("institutional_status"),
                        "read_only": r.get("read_only"),
                        "execution_allowed": r.get("execution_allowed"),
                        "execution_owner": r.get("execution_owner"),
                        "replayable": r.get("replayable"),
                        "explainable": r.get("explainable"),
                        "universal_market_model_ready": r.get("universal_market_model_ready"),
                    }
                    for r in layer_records
                ],
            })

        sections = [
            self._section(
                "Oracle Operating Doctrine",
                "doctrine",
                {
                    "principles": principles,
                    "execution_boundary": "Oracle is read-only. Q Series owns execution.",
                    "read_only": True,
                    "execution_allowed": False,
                    "execution_owner": self.execution_owner,
                },
            ),
            self._section(
                "Supported Market Domains",
                "universal_market_model",
                {
                    "supported_domains": supported_domains,
                    "expansion_model": "All future data integrations use adapters into the Universal Market Model.",
                    "single_oracle_instance": True,
                },
            ),
            self._section(
                "Architecture Layer Map",
                "layer_map",
                {
                    "layer_count": len(layer_sections),
                    "layers": layer_sections,
                },
            ),
            self._section(
                "Safety Contract",
                "safety",
                {
                    "oracle_read_only": True,
                    "oracle_executes_trades": False,
                    "oracle_manages_positions": False,
                    "oracle_submits_orders": False,
                    "execution_owner": self.execution_owner,
                },
            ),
            self._section(
                "Institutional Capabilities",
                "capabilities",
                {
                    "replayability_by_default": True,
                    "explainability_by_default": True,
                    "historical_memory_permanent": True,
                    "institutional_telemetry": True,
                    "strategy_agnostic_q_series": True,
                    "adapter_based_expansion": True,
                },
            ),
        ]

        violation_count = int(registry.get("violation_count") or 0)
        manual_id = _hash({
            "registry_id": registry.get("architecture_registry_id"),
            "section_ids": [s.section_id for s in sections],
            "record_count": len(records),
            "violation_count": violation_count,
        })

        if not records:
            manual_status = "empty_architecture_manual"
        elif violation_count:
            manual_status = "architecture_manual_blocked"
        else:
            manual_status = "architecture_manual_ready"

        return {
            "module": self.name,
            "version": self.version,
            "manual_schema_version": self.manual_schema_version,
            "architecture_manual_id": manual_id,
            "manual_status": manual_status,
            "created_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "source_architecture_registry_id": registry.get("architecture_registry_id"),
            "source_registry_status": registry.get("registry_status"),
            "record_count": len(records),
            "section_count": len(sections),
            "violation_count": violation_count,
            "executive_summary": {
                "headline": (
                    "Oracle architecture manual is ready."
                    if manual_status == "architecture_manual_ready"
                    else f"Oracle architecture manual status: {manual_status}."
                ),
                "architecture_manual_id": manual_id,
                "source_architecture_registry_id": registry.get("architecture_registry_id"),
                "record_count": len(records),
                "section_count": len(sections),
                "operator_note": "Oracle remains intelligence-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "sections": [section.__dict__ for section in sections],
        }

    def get_section(self, manual: Dict[str, Any], section_type: str) -> Dict[str, Any]:
        manual = _safe_dict(manual)
        sections = _safe_list(manual.get("sections"))
        target = str(section_type or "").strip().lower()

        for section in sections:
            section = _safe_dict(section)
            if str(section.get("section_type") or "").strip().lower() == target:
                return {
                    "module": self.name,
                    "version": self.version,
                    "found": True,
                    "section_type": section_type,
                    "section": section,
                    "read_only": True,
                    "execution_allowed": False,
                    "execution_owner": self.execution_owner,
                }

        return {
            "module": self.name,
            "version": self.version,
            "found": False,
            "section_type": section_type,
            "section": None,
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }


oracle_architecture_manual_engine = OracleArchitectureManualEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.architecture_manual_engine import (
    oracle_architecture_manual_engine,
)


def sample_registry():
    return {
        "architecture_registry_id": "reg-001",
        "registry_status": "architecture_registry_ready",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "violation_count": 0,
        "supported_domains": ["CRYPTO", "STOCKS", "FOREX"],
        "permanent_principles": [
            "Oracle is strictly read-only.",
            "Q Series is the only execution engine.",
            "Universal Market Model for all data.",
        ],
        "records": [
            {
                "module_id": "OI-155",
                "module_name": "Oracle Historical Replay Engine",
                "architecture_layer": "Historical Intelligence",
                "institutional_status": "institutional_registered",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "replayable": True,
                "explainable": True,
                "universal_market_model_ready": True,
            },
            {
                "module_id": "OI-160",
                "module_name": "Oracle Alpha Integration Test Engine",
                "architecture_layer": "Institutional Validation",
                "institutional_status": "institutional_registered",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "replayable": True,
                "explainable": True,
                "universal_market_model_ready": True,
            },
        ],
    }


def test_manual_generates_successfully():
    manual = oracle_architecture_manual_engine.generate_manual(sample_registry())

    assert manual["read_only"] is True
    assert manual["execution_allowed"] is False
    assert manual["execution_owner"] == "Q Series"
    assert manual["manual_status"] == "architecture_manual_ready"
    assert manual["record_count"] == 2
    assert manual["section_count"] == 5


def test_manual_contains_safety_contract():
    manual = oracle_architecture_manual_engine.generate_manual(sample_registry())
    section = oracle_architecture_manual_engine.get_section(manual, "safety")

    assert section["found"] is True
    assert section["read_only"] is True
    assert section["execution_allowed"] is False
    assert section["section"]["content"]["oracle_executes_trades"] is False
    assert section["section"]["content"]["execution_owner"] == "Q Series"


def test_manual_contains_layer_map():
    manual = oracle_architecture_manual_engine.generate_manual(sample_registry())
    section = oracle_architecture_manual_engine.get_section(manual, "layer_map")

    assert section["found"] is True
    assert section["section"]["content"]["layer_count"] == 2


def test_blocked_registry_blocks_manual():
    registry = sample_registry()
    registry["violation_count"] = 1

    manual = oracle_architecture_manual_engine.generate_manual(registry)

    assert manual["manual_status"] == "architecture_manual_blocked"
    assert manual["violation_count"] == 1


def test_empty_manual():
    registry = sample_registry()
    registry["records"] = []

    manual = oracle_architecture_manual_engine.generate_manual(registry)

    assert manual["manual_status"] == "empty_architecture_manual"
    assert manual["record_count"] == 0
    assert manual["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_manual_generates_successfully()
    test_manual_contains_safety_contract()
    test_manual_contains_layer_map()
    test_blocked_registry_blocks_manual()
    test_empty_manual()
    print("[PASS] OI-163 Oracle Architecture Manual Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .architecture_manual_engine import oracle_architecture_manual_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-163 INSTALLER")
    print(" Oracle Architecture Manual Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-163 installed")
    print("\nRun:")
    print("py test_oi_163_architecture_manual_engine.py")


if __name__ == "__main__":
    main()