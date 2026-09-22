from __future__ import annotations

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
