from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "integration" / "oracle_runtime_smoke_gate.py"
TEST = ROOT / "test_int_011_oracle_runtime_smoke_gate.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List

from qseries_v2.integration.oracle_intelligence_runtime import OracleIntelligenceRuntime


@dataclass(frozen=True)
class OracleRuntimeSmokeGateResult:
    status: str
    checks: Dict[str, bool]
    errors: List[str]
    generated_at: str

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleRuntimeSmokeGate:
    """
    INT-011 Oracle Runtime Smoke Gate.

    Verifies the integrated Oracle Intelligence runtime is wired correctly.
    This gate does not execute trades.
    """

    def __init__(self, runtime: OracleIntelligenceRuntime) -> None:
        self.runtime = runtime

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def run(self) -> OracleRuntimeSmokeGateResult:
        errors: List[str] = []

        health = self.runtime.health()
        pipeline = self.runtime.pipeline_status()
        engines = self.runtime.engines()

        checks = {
            "runtime_object_exists": self.runtime is not None,
            "registry_exists": getattr(self.runtime, "registry", None) is not None,
            "signal_bus_exists": getattr(self.runtime, "signal_bus", None) is not None,
            "aggregator_exists": getattr(self.runtime, "aggregator", None) is not None,
            "execution_gateway_exists": getattr(self.runtime, "execution_gateway", None) is not None,
            "orchestrator_exists": getattr(self.runtime, "orchestrator", None) is not None,
            "terminal_api_exists": getattr(self.runtime, "terminal_api", None) is not None,
            "health_returns_status": bool(getattr(health, "status", None)),
            "pipeline_status_ok": pipeline.status == "ok",
            "engines_endpoint_ok": engines.status == "ok",
        }

        for name, passed in checks.items():
            if not passed:
                errors.append(name)

        return OracleRuntimeSmokeGateResult(
            status="ok" if not errors else "error",
            checks=checks,
            errors=errors,
            generated_at=self.now_iso(),
        )


def run_oracle_runtime_smoke_gate(runtime: OracleIntelligenceRuntime) -> OracleRuntimeSmokeGateResult:
    return OracleRuntimeSmokeGate(runtime).run()


__all__ = [
    "OracleRuntimeSmokeGateResult",
    "OracleRuntimeSmokeGate",
    "run_oracle_runtime_smoke_gate",
]
'''

test_code = r'''
from qseries_v2.integration.oracle_intelligence_runtime import create_oracle_intelligence_runtime
from qseries_v2.integration.oracle_runtime_smoke_gate import (
    OracleRuntimeSmokeGate,
    run_oracle_runtime_smoke_gate,
)


def test_int_011_oracle_runtime_smoke_gate():
    runtime = create_oracle_intelligence_runtime()

    gate = OracleRuntimeSmokeGate(runtime)
    result = gate.run()

    assert result.status == "ok"
    assert result.ok is True
    assert result.errors == []
    assert all(result.checks.values())

    result2 = run_oracle_runtime_smoke_gate(runtime)
    assert result2.status == "ok"

    print("[PASS] INT-011 Oracle Runtime Smoke Gate")
    print(result.to_dict())


if __name__ == "__main__":
    test_int_011_oracle_runtime_smoke_gate()
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "integration" / "__init__.py"
existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .oracle_runtime_smoke_gate import "
    "OracleRuntimeSmokeGateResult, OracleRuntimeSmokeGate, "
    "run_oracle_runtime_smoke_gate\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" INT-011 INSTALLER")
print(" Oracle Runtime Smoke Gate")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] INT-011 installed")
print("")
print("Run:")
print("py test_int_011_oracle_runtime_smoke_gate.py")