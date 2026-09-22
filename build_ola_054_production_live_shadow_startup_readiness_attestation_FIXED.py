from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE = ROOT / "qseries_v2/oracle_intelligence/live_acquisition/oracle_production_live_shadow_startup_readiness_attestation.py"
OLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"
TEST = ROOT / "test_ola_054_production_live_shadow_startup_readiness_attestation.py"

MODULE_TEXT = r'''
"""
OLA-054 Production Live Shadow Startup Readiness Attestation.

Fail-closed startup authorization boundary for the actual OLA-030 production
graph. This record does not start the service. It only proves that the
already-attested production lineage graph, scheduler activation chain,
OLA-022 bootstrap record, and OLA-023 runner agree on a permanently read-only
live-shadow startup boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "OLA-054"
ENGINE_ID = "OLA-054"
ATTESTATION_TYPE = "oracle_production_live_shadow_startup_readiness_attestation"


class OracleProductionLiveShadowStartupReadinessAttestationError(ValueError):
    pass


class OracleProductionLiveShadowStartupReadinessAttestationBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLiveShadowStartupReadinessAttestationRecord:
    schema_version: str
    engine_id: str
    attestation_type: str
    graph_assembly_attested: bool
    scheduler_activation_attested: bool
    bootstrap_ready: bool
    bootstrap_service_start_allowed: bool
    bootstrap_not_started: bool
    runner_bootstrap_identity_preserved: bool
    runner_read_only: bool
    startup_ready: bool
    service_started: bool = False
    process_created: bool = False
    thread_created: bool = False
    loop_started: bool = False
    acquisition_invoked: bool = False
    scheduler_tick_invoked: bool = False
    shadow_cycle_invoked: bool = False
    read_only: bool = True
    execution_allowed: bool = False
    alerts_allowed: bool = False
    qseries_handoff_allowed: bool = False
    execution_adapter_resolved: bool = False
    execution_adapter_invoked: bool = False
    trade_authorization_allowed: bool = False
    order_placement_allowed: bool = False
    funds_moved: bool = False
    portfolio_mutated: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION or self.engine_id != ENGINE_ID:
            raise OracleProductionLiveShadowStartupReadinessAttestationError(
                "OLA-054 identity mismatch"
            )
        if self.attestation_type != ATTESTATION_TYPE:
            raise OracleProductionLiveShadowStartupReadinessAttestationError(
                "attestation_type mismatch"
            )

        required = (
            self.graph_assembly_attested,
            self.scheduler_activation_attested,
            self.bootstrap_ready,
            self.bootstrap_service_start_allowed,
            self.bootstrap_not_started,
            self.runner_bootstrap_identity_preserved,
            self.runner_read_only,
            self.startup_ready,
            self.read_only,
        )
        if not all(value is True for value in required):
            raise OracleProductionLiveShadowStartupReadinessAttestationBlocked(
                "production live-shadow startup readiness failed closed"
            )

        forbidden = (
            self.service_started,
            self.process_created,
            self.thread_created,
            self.loop_started,
            self.acquisition_invoked,
            self.scheduler_tick_invoked,
            self.shadow_cycle_invoked,
            self.execution_allowed,
            self.alerts_allowed,
            self.qseries_handoff_allowed,
            self.execution_adapter_resolved,
            self.execution_adapter_invoked,
            self.trade_authorization_allowed,
            self.order_placement_allowed,
            self.funds_moved,
            self.portfolio_mutated,
        )
        if any(value is True for value in forbidden):
            raise OracleProductionLiveShadowStartupReadinessAttestationBlocked(
                "OLA-054 startup attestation observed forbidden activity"
            )


class OracleProductionLiveShadowStartupReadinessAttestor:
    read_only = True
    execution_allowed = False

    def attest(
        self,
        *,
        lineage_graph_attestation: Any,
        lineage_scheduler_activation_attestation: Any,
        service_bootstrap: Any,
        runner: Any,
    ) -> OracleProductionLiveShadowStartupReadinessAttestationRecord:
        runner_bootstrap = getattr(runner, "_bootstrap_record", None)

        checks = {
            "graph_assembly_attested": (
                getattr(
                    lineage_graph_attestation,
                    "full_graph_attested",
                    getattr(
                        lineage_graph_attestation,
                        "actual_ola030_graph_attested",
                        False,
                    ),
                )
                is True
            ),
            "scheduler_activation_attested": (
                getattr(
                    lineage_scheduler_activation_attestation,
                    "full_activation_chain_attested",
                    False,
                )
                is True
            ),
            "bootstrap_ready": (
                getattr(service_bootstrap, "bootstrap_status", None) == "ready"
            ),
            "bootstrap_service_start_allowed": (
                getattr(service_bootstrap, "service_start_allowed", None) is True
            ),
            "bootstrap_not_started": all(
                getattr(service_bootstrap, field, None) is False
                for field in (
                    "service_started",
                    "process_created",
                    "thread_created",
                    "loop_started",
                    "acquisition_invoked",
                    "scheduler_tick_invoked",
                    "shadow_cycle_invoked",
                )
            ),
            "runner_bootstrap_identity_preserved": (
                runner_bootstrap is service_bootstrap
            ),
            "runner_read_only": (
                getattr(runner, "read_only", None) is True
                and getattr(runner, "execution_allowed", None) is False
            ),
        }

        if not all(checks.values()):
            failed = ", ".join(
                name for name, passed in checks.items() if not passed
            )
            raise OracleProductionLiveShadowStartupReadinessAttestationBlocked(
                "production live-shadow startup readiness mismatch: "
                f"{failed}"
            )

        return OracleProductionLiveShadowStartupReadinessAttestationRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            attestation_type=ATTESTATION_TYPE,
            startup_ready=True,
            **checks,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ATTESTATION_TYPE",
    "OracleProductionLiveShadowStartupReadinessAttestationError",
    "OracleProductionLiveShadowStartupReadinessAttestationBlocked",
    "OracleProductionLiveShadowStartupReadinessAttestationRecord",
    "OracleProductionLiveShadowStartupReadinessAttestor",
]
'''

TEST_TEXT = r"""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_startup_readiness_attestation import (
    OracleProductionLiveShadowStartupReadinessAttestationBlocked,
    OracleProductionLiveShadowStartupReadinessAttestor,
)

ROOT = Path(__file__).resolve().parent
OLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"


class Runner:
    read_only = True
    execution_allowed = False

    def __init__(self, bootstrap):
        self._bootstrap_record = bootstrap


def bootstrap_record():
    return SimpleNamespace(
        bootstrap_status="ready",
        service_start_allowed=True,
        service_started=False,
        process_created=False,
        thread_created=False,
        loop_started=False,
        acquisition_invoked=False,
        scheduler_tick_invoked=False,
        shadow_cycle_invoked=False,
    )


def main():
    graph_attestation = SimpleNamespace(full_graph_attested=True)
    activation_attestation = SimpleNamespace(
        full_activation_chain_attested=True
    )
    bootstrap = bootstrap_record()
    runner = Runner(bootstrap)

    record = OracleProductionLiveShadowStartupReadinessAttestor().attest(
        lineage_graph_attestation=graph_attestation,
        lineage_scheduler_activation_attestation=activation_attestation,
        service_bootstrap=bootstrap,
        runner=runner,
    )

    assert record.schema_version == "OLA-054"
    assert record.startup_ready is True
    assert record.service_started is False
    assert record.loop_started is False
    assert record.read_only is True
    assert record.execution_allowed is False

    bad_bootstrap = bootstrap_record()
    bad_bootstrap.loop_started = True

    try:
        OracleProductionLiveShadowStartupReadinessAttestor().attest(
            lineage_graph_attestation=graph_attestation,
            lineage_scheduler_activation_attestation=activation_attestation,
            service_bootstrap=bad_bootstrap,
            runner=Runner(bad_bootstrap),
        )
    except OracleProductionLiveShadowStartupReadinessAttestationBlocked:
        pass
    else:
        raise AssertionError(
            "OLA-054 must fail closed if startup activity already occurred"
        )

    source = OLA030.read_text(encoding="utf-8")
    ast.parse(source)

    required = (
        "OracleProductionLiveShadowStartupReadinessAttestor",
        "production_startup_readiness_attestation = (",
        "lineage_graph_attestation=(",
        "lineage_scheduler_activation_attestation=(",
        "service_bootstrap=service_bootstrap",
        "runner=runner",
        '"production_startup_readiness_attestation": (',
    )
    for marker in required:
        assert marker in source, marker

    activation_pos = source.index(
        "lineage_scheduler_activation_attestation = ("
    )
    startup_pos = source.index(
        "production_startup_readiness_attestation = ("
    )
    return_pos = source.index("    return {", startup_pos)

    assert activation_pos < startup_pos < return_pos

    print("[PASS] OLA-054 Production Live Shadow Startup Readiness Attestation")
    print({
        "schema_version": "OLA-054",
        "engine_id": "OLA-054",
        "status": "passed",
        "actual_ola030_startup_boundary_attested": True,
        "ola052_graph_assembly_required": True,
        "ola053_scheduler_activation_required": True,
        "ola022_bootstrap_ready_required": True,
        "ola023_runner_bootstrap_identity_preserved": True,
        "startup_authorized_but_not_started": True,
        "fail_closed_prestarted_runtime_tested": True,
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "execution_adapter_resolved": False,
        "execution_adapter_invoked": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    })


if __name__ == "__main__":
    main()
"""


def patch_ola030(source: str) -> str:
    import_anchor = (
        "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_lineage_scheduler_activation_attestation import (\n"
        "    OracleProductionLineageSchedulerActivationAttestor,\n"
        ")\n"
    )
    new_import = import_anchor + (
        "\nfrom qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_startup_readiness_attestation import (\n"
        "    OracleProductionLiveShadowStartupReadinessAttestor,\n"
        ")\n"
    )

    if "OracleProductionLiveShadowStartupReadinessAttestor" not in source:
        if import_anchor not in source:
            raise RuntimeError(
                "OLA-053 import anchor not found; install and pass OLA-053 first"
            )
        source = source.replace(import_anchor, new_import, 1)

    activation_marker = (
        "    lineage_scheduler_activation_attestation = (\n"
    )
    if activation_marker not in source:
        raise RuntimeError(
            "OLA-053 activation attestation block not found"
        )

    if "production_startup_readiness_attestation = (" not in source:
        activation_pos = source.index(activation_marker)
        return_pos = source.index("    return {", activation_pos)

        startup_block = (
            "    production_startup_readiness_attestation = (\n"
            "        OracleProductionLiveShadowStartupReadinessAttestor()\n"
            "        .attest(\n"
            "            lineage_graph_attestation=(\n"
            "                lineage_graph_attestation\n"
            "            ),\n"
            "            lineage_scheduler_activation_attestation=(\n"
            "                lineage_scheduler_activation_attestation\n"
            "            ),\n"
            "            service_bootstrap=service_bootstrap,\n"
            "            runner=runner,\n"
            "        )\n"
            "    )\n\n"
        )
        source = source[:return_pos] + startup_block + source[return_pos:]

    return_anchor = (
        '        "lineage_scheduler_activation_attestation": (\n'
        "            lineage_scheduler_activation_attestation\n"
        "        ),\n"
    )
    return_block = return_anchor + (
        '        "production_startup_readiness_attestation": (\n'
        "            production_startup_readiness_attestation\n"
        "        ),\n"
    )

    if '"production_startup_readiness_attestation": (' not in source:
        if return_anchor not in source:
            raise RuntimeError(
                "OLA-053 return-map anchor not found"
            )
        source = source.replace(return_anchor, return_block, 1)

    return source


def main() -> None:
    print("========================================")
    print(" OLA-054 INSTALLER")
    print(" PRODUCTION LIVE SHADOW STARTUP READINESS ATTESTATION")
    print("========================================")

    if not OLA030.exists():
        raise SystemExit(f"[ERROR] Missing OLA-030 production graph: {OLA030}")

    source = OLA030.read_text(encoding="utf-8")
    required = (
        "OracleProductionLineageGraphAssemblyAttestor",
        "OracleProductionLineageSchedulerActivationAttestor",
        "lineage_graph_attestation = (",
        "lineage_scheduler_activation_attestation = (",
    )
    missing = [marker for marker in required if marker not in source]
    if missing:
        raise SystemExit(
            "[ERROR] OLA-052/OLA-053 production integration is incomplete. "
            f"Missing markers: {missing}"
        )

    MODULE.parent.mkdir(parents=True, exist_ok=True)
    MODULE.write_text(MODULE_TEXT, encoding="utf-8")
    print(f"[OK] Wrote OLA-054 startup readiness attestation module: {MODULE}")

    patched = patch_ola030(source)
    OLA030.write_text(patched, encoding="utf-8")
    print(f"[OK] Integrated OLA-054 into actual OLA-030 graph: {OLA030}")

    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print(f"[OK] Wrote regression test: {TEST}")

    compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
    compile(OLA030.read_text(encoding="utf-8"), str(OLA030), "exec")
    compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

    print(
        "\n[DONE] OLA-054 production live shadow startup readiness "
        "attestation installed"
    )
    print("\nRun:")
    print(
        "py test_ola_054_production_live_shadow_"
        "startup_readiness_attestation.py"
    )


if __name__ == "__main__":
    main()
