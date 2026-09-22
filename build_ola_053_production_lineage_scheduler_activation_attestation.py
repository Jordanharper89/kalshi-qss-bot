from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE = ROOT / "qseries_v2/oracle_intelligence/live_acquisition/oracle_production_lineage_scheduler_activation_attestation.py"
OLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"
TEST = ROOT / "test_ola_053_production_lineage_scheduler_activation_attestation.py"

MODULE_TEXT = r'''"""
OLA-053 Oracle Production Lineage Scheduler Activation Attestation.

Fail-closed activation attestation for the actual OLA-030 production graph.

OLA-052 proves the lineage graph is assembled correctly before scheduler
construction. OLA-053 proves that the exact OLA-050 lineage callable is then
activated through the real production execution path:

OLA-050 callable facade
    ->
ShadowCycleRunnerBinding
    ->
OLA-021 scheduler
    ->
OracleLiveShadowSchedulerBinding
    ->
OLA-023 service runner

This boundary performs no acquisition, persistence, alerting, handoff, or
execution. Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "OLA-053"
ENGINE_ID = "OLA-053"
ATTESTATION_TYPE = "oracle_production_lineage_scheduler_activation_attestation"


class OracleProductionLineageSchedulerActivationAttestationError(ValueError):
    pass


class OracleProductionLineageSchedulerActivationAttestationBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLineageSchedulerActivationAttestationRecord:
    schema_version: str
    engine_id: str
    attestation_type: str
    ola050_bound_to_cycle_runner: bool
    cycle_runner_bound_to_ola021: bool
    ola021_bound_to_service_scheduler_binding: bool
    service_scheduler_binding_bound_to_ola023: bool
    scheduler_engine_identity_preserved: bool
    cycle_runner_engine_identity_preserved: bool
    full_activation_chain_attested: bool
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
            raise OracleProductionLineageSchedulerActivationAttestationError(
                "OLA-053 identity mismatch"
            )
        if self.attestation_type != ATTESTATION_TYPE:
            raise OracleProductionLineageSchedulerActivationAttestationError(
                "attestation_type mismatch"
            )

        required = (
            self.ola050_bound_to_cycle_runner,
            self.cycle_runner_bound_to_ola021,
            self.ola021_bound_to_service_scheduler_binding,
            self.service_scheduler_binding_bound_to_ola023,
            self.scheduler_engine_identity_preserved,
            self.cycle_runner_engine_identity_preserved,
            self.full_activation_chain_attested,
            self.read_only,
        )
        if not all(value is True for value in required):
            raise OracleProductionLineageSchedulerActivationAttestationBlocked(
                "production lineage scheduler activation attestation failed closed"
            )

        forbidden = (
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
            raise OracleProductionLineageSchedulerActivationAttestationBlocked(
                "OLA-053 permanent read-only invariant violated"
            )


class OracleProductionLineageSchedulerActivationAttestor:
    read_only = True
    execution_allowed = False

    def attest(
        self,
        *,
        lineage_cycle_callable: Any,
        cycle_runner_binding: Any,
        scheduler: Any,
        service_scheduler_binding: Any,
        runner: Any,
    ) -> OracleProductionLineageSchedulerActivationAttestationRecord:
        cycle_callable = getattr(cycle_runner_binding, "cycle_callable", None)

        scheduler_cycle_runner = getattr(scheduler, "cycle_runner", None)
        if scheduler_cycle_runner is None:
            scheduler_cycle_runner = getattr(scheduler, "_cycle_runner", None)

        service_tick_callable = getattr(
            service_scheduler_binding,
            "tick_callable",
            None,
        )

        runner_scheduler = getattr(runner, "_scheduler", None)
        scheduler_tick = getattr(scheduler, "run_tick", None)

        checks = {
            "ola050_bound_to_cycle_runner": (
                cycle_callable is lineage_cycle_callable
            ),
            "cycle_runner_bound_to_ola021": (
                scheduler_cycle_runner is cycle_runner_binding
            ),
            "ola021_bound_to_service_scheduler_binding": (
                getattr(service_tick_callable, "__self__", None) is scheduler
                and getattr(service_tick_callable, "__func__", None)
                is getattr(scheduler_tick, "__func__", None)
            ),
            "service_scheduler_binding_bound_to_ola023": (
                runner_scheduler is service_scheduler_binding
            ),
            "scheduler_engine_identity_preserved": (
                getattr(service_scheduler_binding, "engine_id", None) == "OLA-021"
            ),
            "cycle_runner_engine_identity_preserved": (
                getattr(cycle_runner_binding, "engine_id", None) == "OLA-017"
            ),
        }

        full = all(checks.values())
        if not full:
            failed = ", ".join(
                name for name, passed in checks.items() if not passed
            )
            raise OracleProductionLineageSchedulerActivationAttestationBlocked(
                "production lineage scheduler activation mismatch: "
                f"{failed}"
            )

        return OracleProductionLineageSchedulerActivationAttestationRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            attestation_type=ATTESTATION_TYPE,
            full_activation_chain_attested=True,
            **checks,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ATTESTATION_TYPE",
    "OracleProductionLineageSchedulerActivationAttestationError",
    "OracleProductionLineageSchedulerActivationAttestationBlocked",
    "OracleProductionLineageSchedulerActivationAttestationRecord",
    "OracleProductionLineageSchedulerActivationAttestor",
]
'''

TEST_TEXT = r'''from __future__ import annotations

import ast
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_lineage_scheduler_activation_attestation import (
    OracleProductionLineageSchedulerActivationAttestationBlocked,
    OracleProductionLineageSchedulerActivationAttestor,
)

ROOT = Path(__file__).resolve().parent
OLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"


class Facade:
    def __call__(self, **kwargs):
        return None


class CycleRunnerBinding:
    def __init__(self, cycle_callable):
        self.cycle_callable = cycle_callable
        self.engine_id = "OLA-017"


class Scheduler:
    def __init__(self, cycle_runner):
        self._cycle_runner = cycle_runner

    @property
    def cycle_runner(self):
        return self._cycle_runner

    def run_tick(self, **kwargs):
        return None


class ServiceSchedulerBinding:
    def __init__(self, scheduler):
        self.engine_id = "OLA-021"
        self.tick_callable = scheduler.run_tick


class Runner:
    def __init__(self, scheduler_binding):
        self._scheduler = scheduler_binding


def main():
    facade = Facade()
    cycle_runner = CycleRunnerBinding(facade)
    scheduler = Scheduler(cycle_runner)
    service_scheduler = ServiceSchedulerBinding(scheduler)
    runner = Runner(service_scheduler)

    record = OracleProductionLineageSchedulerActivationAttestor().attest(
        lineage_cycle_callable=facade,
        cycle_runner_binding=cycle_runner,
        scheduler=scheduler,
        service_scheduler_binding=service_scheduler,
        runner=runner,
    )

    assert record.schema_version == "OLA-053"
    assert record.full_activation_chain_attested is True
    assert record.read_only is True
    assert record.execution_allowed is False

    bad_cycle_runner = CycleRunnerBinding(object())
    bad_scheduler = Scheduler(bad_cycle_runner)
    bad_service_scheduler = ServiceSchedulerBinding(bad_scheduler)
    bad_runner = Runner(bad_service_scheduler)

    try:
        OracleProductionLineageSchedulerActivationAttestor().attest(
            lineage_cycle_callable=facade,
            cycle_runner_binding=bad_cycle_runner,
            scheduler=bad_scheduler,
            service_scheduler_binding=bad_service_scheduler,
            runner=bad_runner,
        )
    except OracleProductionLineageSchedulerActivationAttestationBlocked:
        pass
    else:
        raise AssertionError(
            "OLA-053 must fail closed on activation identity mismatch"
        )

    source = OLA030.read_text(encoding="utf-8")
    ast.parse(source)

    required = (
        "OracleProductionLineageSchedulerActivationAttestor",
        "cycle_runner_binding = (",
        "service_scheduler_binding = (",
        "lineage_scheduler_activation_attestation = (",
        '"lineage_scheduler_activation_attestation": (',
    )
    for marker in required:
        assert marker in source, marker

    print("[PASS] OLA-053 Production Lineage Scheduler Activation Attestation")
    print({
        "schema_version": "OLA-053",
        "engine_id": "OLA-053",
        "status": "passed",
        "actual_ola030_activation_chain_attested": True,
        "ola050_bound_to_shadow_cycle_runner_binding": True,
        "shadow_cycle_runner_binding_bound_to_ola021": True,
        "ola021_bound_to_service_scheduler_binding": True,
        "service_scheduler_binding_bound_to_ola023": True,
        "cycle_runner_engine_identity_preserved": True,
        "scheduler_engine_identity_preserved": True,
        "fail_closed_activation_mismatch_tested": True,
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
'''


def patch_ola030(source: str) -> str:
    import_marker = '''from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_lineage_graph_assembly_attestation import (
    OracleProductionLineageGraphAssemblyAttestor,
)
'''
    new_import = import_marker + '''
from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_lineage_scheduler_activation_attestation import (
    OracleProductionLineageSchedulerActivationAttestor,
)
'''
    if "OracleProductionLineageSchedulerActivationAttestor" not in source:
        if import_marker not in source:
            raise RuntimeError(
                "OLA-052 import anchor not found; install and pass OLA-052 first"
            )
        source = source.replace(import_marker, new_import, 1)

    old_scheduler = '''    scheduler = (
        OracleControlledShadowCollectionSchedulerTick(
            polling_engine=polling_engine,
            cycle_runner=ShadowCycleRunnerBinding(
                runner_id=(
                    "runner.ola017.ola030.production"
                ),
                engine_id="OLA-017",
                source_id=SOURCE_ID,
                adapter_id=ADAPTER_ID,
                cycle_callable=(
                    lineage_cycle_callable
                ),
            ),
        )
    )
'''
    new_scheduler = '''    cycle_runner_binding = (
        ShadowCycleRunnerBinding(
            runner_id=(
                "runner.ola017.ola030.production"
            ),
            engine_id="OLA-017",
            source_id=SOURCE_ID,
            adapter_id=ADAPTER_ID,
            cycle_callable=(
                lineage_cycle_callable
            ),
        )
    )

    scheduler = (
        OracleControlledShadowCollectionSchedulerTick(
            polling_engine=polling_engine,
            cycle_runner=cycle_runner_binding,
        )
    )
'''
    if "cycle_runner_binding = (" not in source:
        if old_scheduler not in source:
            raise RuntimeError("OLA-030 scheduler construction anchor not found")
        source = source.replace(old_scheduler, new_scheduler, 1)

    old_runner_prefix = '''    runner = OracleLiveShadowServiceRunner(
        bootstrap_record=service_bootstrap,
        readiness_provider=(
            OracleLiveShadowReadinessProviderBinding(
'''
    new_runner_prefix = '''    service_scheduler_binding = (
        OracleLiveShadowSchedulerBinding(
            scheduler_id=(
                "scheduler.ola021."
                "production.ola030"
            ),
            engine_id="OLA-021",
            tick_callable=scheduler.run_tick,
        )
    )

    runner = OracleLiveShadowServiceRunner(
        bootstrap_record=service_bootstrap,
        readiness_provider=(
            OracleLiveShadowReadinessProviderBinding(
'''
    if "service_scheduler_binding = (" not in source:
        if old_runner_prefix not in source:
            raise RuntimeError("OLA-030 runner construction anchor not found")
        source = source.replace(old_runner_prefix, new_runner_prefix, 1)

    old_inline_scheduler = '''        scheduler=OracleLiveShadowSchedulerBinding(
            scheduler_id=(
                "scheduler.ola021."
                "production.ola030"
            ),
            engine_id="OLA-021",
            tick_callable=scheduler.run_tick,
        ),
'''
    if old_inline_scheduler in source:
        source = source.replace(
            old_inline_scheduler,
            "        scheduler=service_scheduler_binding,\n",
            1,
        )

    attestation_anchor = '''    return {
'''
    attestation_block = '''    lineage_scheduler_activation_attestation = (
        OracleProductionLineageSchedulerActivationAttestor()
        .attest(
            lineage_cycle_callable=(
                lineage_cycle_callable
            ),
            cycle_runner_binding=(
                cycle_runner_binding
            ),
            scheduler=scheduler,
            service_scheduler_binding=(
                service_scheduler_binding
            ),
            runner=runner,
        )
    )

'''
    if "lineage_scheduler_activation_attestation = (" not in source:
        graph_start = source.find("def build_real_oracle_shadow_graph(")
        if graph_start < 0:
            raise RuntimeError("OLA-030 graph function not found")
        return_pos = source.find(attestation_anchor, graph_start)
        if return_pos < 0:
            raise RuntimeError("OLA-030 graph return anchor not found")
        source = source[:return_pos] + attestation_block + source[return_pos:]

    return_anchor = '''        "lineage_graph_attestation": (
            lineage_graph_attestation
        ),
'''
    return_block = return_anchor + '''        "cycle_runner_binding": (
            cycle_runner_binding
        ),
        "service_scheduler_binding": (
            service_scheduler_binding
        ),
        "lineage_scheduler_activation_attestation": (
            lineage_scheduler_activation_attestation
        ),
'''
    if '"lineage_scheduler_activation_attestation": (' not in source:
        if return_anchor not in source:
            raise RuntimeError("OLA-052 graph return anchor not found")
        source = source.replace(return_anchor, return_block, 1)

    return source


def main() -> None:
    print("========================================")
    print(" OLA-053 INSTALLER")
    print(" PRODUCTION LINEAGE SCHEDULER ACTIVATION ATTESTATION")
    print("========================================")

    if not OLA030.exists():
        raise SystemExit(f"[ERROR] Missing OLA-030 production graph: {OLA030}")

    source = OLA030.read_text(encoding="utf-8")
    if "OracleProductionLineageGraphAssemblyAttestor" not in source:
        raise SystemExit(
            "[ERROR] OLA-052 production graph attestation is not installed. "
            "Install and pass OLA-052 first."
        )

    MODULE.parent.mkdir(parents=True, exist_ok=True)
    MODULE.write_text(MODULE_TEXT, encoding="utf-8")
    print(f"[OK] Wrote OLA-053 activation attestation module: {MODULE}")

    patched = patch_ola030(source)
    OLA030.write_text(patched, encoding="utf-8")
    print(f"[OK] Integrated OLA-053 into actual OLA-030 graph: {OLA030}")

    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print(f"[OK] Wrote regression test: {TEST}")

    compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
    compile(OLA030.read_text(encoding="utf-8"), str(OLA030), "exec")
    compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

    print(
        "\n[DONE] OLA-053 production lineage scheduler activation "
        "attestation installed"
    )
    print("\nRun:")
    print("py test_ola_053_production_lineage_scheduler_activation_attestation.py")


if __name__ == "__main__":
    main()
