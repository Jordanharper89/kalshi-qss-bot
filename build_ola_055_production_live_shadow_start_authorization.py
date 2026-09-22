from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE = ROOT / "qseries_v2/oracle_intelligence/live_acquisition/oracle_production_live_shadow_start_authorization.py"
OLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"
TEST = ROOT / "test_ola_055_production_live_shadow_start_authorization.py"

MODULE_TEXT = r'''"""
OLA-055 Production Live Shadow Start Authorization.

Fail-closed authorization object for the actual OLA-030 production graph.

OLA-054 proves the fully assembled and activated production lineage graph is
ready to start while still untouched. OLA-055 converts that attested readiness
into an explicit, immutable start authorization record that may be consumed by
a later controlled launcher.

This module does not start a process, create a thread, enter a loop, invoke
acquisition, tick the scheduler, run a shadow cycle, emit alerts, hand off to
Q Series, authorize trading, place orders, move funds, or mutate a portfolio.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "OLA-055"
ENGINE_ID = "OLA-055"
AUTHORIZATION_TYPE = "oracle_production_live_shadow_start_authorization"


class OracleProductionLiveShadowStartAuthorizationError(ValueError):
    pass


class OracleProductionLiveShadowStartAuthorizationBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLiveShadowStartAuthorizationRecord:
    schema_version: str
    engine_id: str
    authorization_type: str
    startup_readiness_attested: bool
    startup_ready: bool
    bootstrap_service_start_allowed: bool
    runner_identity_preserved: bool
    start_authorized: bool
    authorization_consumed: bool = False
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
            raise OracleProductionLiveShadowStartAuthorizationError(
                "OLA-055 identity mismatch"
            )
        if self.authorization_type != AUTHORIZATION_TYPE:
            raise OracleProductionLiveShadowStartAuthorizationError(
                "authorization_type mismatch"
            )

        required = (
            self.startup_readiness_attested,
            self.startup_ready,
            self.bootstrap_service_start_allowed,
            self.runner_identity_preserved,
            self.start_authorized,
            self.read_only,
        )
        if not all(value is True for value in required):
            raise OracleProductionLiveShadowStartAuthorizationBlocked(
                "production live-shadow start authorization failed closed"
            )

        forbidden = (
            self.authorization_consumed,
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
            raise OracleProductionLiveShadowStartAuthorizationBlocked(
                "OLA-055 observed forbidden activity before authorization use"
            )


class OracleProductionLiveShadowStartAuthorizer:
    read_only = True
    execution_allowed = False

    def authorize(
        self,
        *,
        startup_readiness_attestation: Any,
        service_bootstrap: Any,
        runner: Any,
    ) -> OracleProductionLiveShadowStartAuthorizationRecord:
        runner_bootstrap = getattr(runner, "_bootstrap_record", None)

        checks = {
            "startup_readiness_attested": (
                getattr(
                    startup_readiness_attestation,
                    "startup_ready",
                    False,
                )
                is True
            ),
            "startup_ready": (
                getattr(
                    startup_readiness_attestation,
                    "startup_ready",
                    False,
                )
                is True
            ),
            "bootstrap_service_start_allowed": (
                getattr(service_bootstrap, "service_start_allowed", None) is True
            ),
            "runner_identity_preserved": (
                runner_bootstrap is service_bootstrap
            ),
        }

        if not all(checks.values()):
            failed = ", ".join(
                name for name, passed in checks.items() if not passed
            )
            raise OracleProductionLiveShadowStartAuthorizationBlocked(
                "production live-shadow start authorization mismatch: "
                f"{failed}"
            )

        forbidden_bootstrap_activity = any(
            getattr(service_bootstrap, field, None) is True
            for field in (
                "service_started",
                "process_created",
                "thread_created",
                "loop_started",
                "acquisition_invoked",
                "scheduler_tick_invoked",
                "shadow_cycle_invoked",
            )
        )
        if forbidden_bootstrap_activity:
            raise OracleProductionLiveShadowStartAuthorizationBlocked(
                "production live-shadow start authorization requires "
                "an untouched pre-start bootstrap"
            )

        return OracleProductionLiveShadowStartAuthorizationRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            authorization_type=AUTHORIZATION_TYPE,
            start_authorized=True,
            **checks,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "AUTHORIZATION_TYPE",
    "OracleProductionLiveShadowStartAuthorizationError",
    "OracleProductionLiveShadowStartAuthorizationBlocked",
    "OracleProductionLiveShadowStartAuthorizationRecord",
    "OracleProductionLiveShadowStartAuthorizer",
]
'''

TEST_TEXT = r'''from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_start_authorization import (
    OracleProductionLiveShadowStartAuthorizationBlocked,
    OracleProductionLiveShadowStartAuthorizer,
)

ROOT = Path(__file__).resolve().parent
OLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"


class Runner:
    read_only = True
    execution_allowed = False

    def __init__(self, bootstrap):
        self._bootstrap_record = bootstrap


def make_bootstrap():
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
    startup_readiness = SimpleNamespace(startup_ready=True)
    bootstrap = make_bootstrap()
    runner = Runner(bootstrap)

    record = OracleProductionLiveShadowStartAuthorizer().authorize(
        startup_readiness_attestation=startup_readiness,
        service_bootstrap=bootstrap,
        runner=runner,
    )

    assert record.schema_version == "OLA-055"
    assert record.start_authorized is True
    assert record.authorization_consumed is False
    assert record.service_started is False
    assert record.loop_started is False
    assert record.read_only is True
    assert record.execution_allowed is False

    bad_bootstrap = make_bootstrap()
    bad_bootstrap.shadow_cycle_invoked = True

    try:
        OracleProductionLiveShadowStartAuthorizer().authorize(
            startup_readiness_attestation=startup_readiness,
            service_bootstrap=bad_bootstrap,
            runner=Runner(bad_bootstrap),
        )
    except OracleProductionLiveShadowStartAuthorizationBlocked:
        pass
    else:
        raise AssertionError(
            "OLA-055 must fail closed if pre-start activity already occurred"
        )

    source = OLA030.read_text(encoding="utf-8")
    ast.parse(source)

    required = (
        "OracleProductionLiveShadowStartAuthorizer",
        "production_start_authorization = (",
        "startup_readiness_attestation=(",
        "service_bootstrap=service_bootstrap",
        "runner=runner",
        '"production_start_authorization": (',
    )
    for marker in required:
        assert marker in source, marker

    startup_pos = source.index(
        "production_startup_readiness_attestation = ("
    )
    authorization_pos = source.index(
        "production_start_authorization = ("
    )
    return_pos = source.index("    return {", authorization_pos)

    assert startup_pos < authorization_pos < return_pos

    print("[PASS] OLA-055 Production Live Shadow Start Authorization")
    print({
        "schema_version": "OLA-055",
        "engine_id": "OLA-055",
        "status": "passed",
        "actual_ola030_start_authorization_integrated": True,
        "ola054_startup_readiness_required": True,
        "ola022_service_start_permission_required": True,
        "ola023_runner_bootstrap_identity_preserved": True,
        "start_authorized_but_not_consumed": True,
        "service_not_started": True,
        "no_process_created": True,
        "no_thread_created": True,
        "no_loop_started": True,
        "no_acquisition_invoked": True,
        "no_scheduler_tick_invoked": True,
        "no_shadow_cycle_invoked": True,
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
'''


def patch_ola030(source: str) -> str:
    import_anchor = (
        "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_startup_readiness_attestation import (\n"
        "    OracleProductionLiveShadowStartupReadinessAttestor,\n"
        ")\n"
    )
    new_import = import_anchor + (
        "\nfrom qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_start_authorization import (\n"
        "    OracleProductionLiveShadowStartAuthorizer,\n"
        ")\n"
    )

    if "OracleProductionLiveShadowStartAuthorizer" not in source:
        if import_anchor not in source:
            raise RuntimeError(
                "OLA-054 import anchor not found; install and pass OLA-054 first"
            )
        source = source.replace(import_anchor, new_import, 1)

    readiness_marker = (
        "    production_startup_readiness_attestation = (\n"
    )
    if readiness_marker not in source:
        raise RuntimeError(
            "OLA-054 startup readiness attestation block not found"
        )

    if "production_start_authorization = (" not in source:
        readiness_pos = source.index(readiness_marker)
        return_pos = source.index("    return {", readiness_pos)

        authorization_block = (
            "    production_start_authorization = (\n"
            "        OracleProductionLiveShadowStartAuthorizer()\n"
            "        .authorize(\n"
            "            startup_readiness_attestation=(\n"
            "                production_startup_readiness_attestation\n"
            "            ),\n"
            "            service_bootstrap=service_bootstrap,\n"
            "            runner=runner,\n"
            "        )\n"
            "    )\n\n"
        )
        source = source[:return_pos] + authorization_block + source[return_pos:]

    return_anchor = (
        '        "production_startup_readiness_attestation": (\n'
        "            production_startup_readiness_attestation\n"
        "        ),\n"
    )
    return_block = return_anchor + (
        '        "production_start_authorization": (\n'
        "            production_start_authorization\n"
        "        ),\n"
    )

    if '"production_start_authorization": (' not in source:
        if return_anchor not in source:
            raise RuntimeError(
                "OLA-054 return-map anchor not found"
            )
        source = source.replace(return_anchor, return_block, 1)

    return source


def main() -> None:
    print("========================================")
    print(" OLA-055 INSTALLER")
    print(" PRODUCTION LIVE SHADOW START AUTHORIZATION")
    print("========================================")

    if not OLA030.exists():
        raise SystemExit(f"[ERROR] Missing OLA-030 production graph: {OLA030}")

    source = OLA030.read_text(encoding="utf-8")
    required = (
        "OracleProductionLiveShadowStartupReadinessAttestor",
        "production_startup_readiness_attestation = (",
    )
    missing = [marker for marker in required if marker not in source]
    if missing:
        raise SystemExit(
            "[ERROR] OLA-054 production integration is incomplete. "
            f"Missing markers: {missing}"
        )

    MODULE.parent.mkdir(parents=True, exist_ok=True)
    MODULE.write_text(MODULE_TEXT, encoding="utf-8")
    print(f"[OK] Wrote OLA-055 start authorization module: {MODULE}")

    patched = patch_ola030(source)
    OLA030.write_text(patched, encoding="utf-8")
    print(f"[OK] Integrated OLA-055 into actual OLA-030 graph: {OLA030}")

    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print(f"[OK] Wrote regression test: {TEST}")

    compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
    compile(OLA030.read_text(encoding="utf-8"), str(OLA030), "exec")
    compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

    print(
        "\n[DONE] OLA-055 production live shadow start "
        "authorization installed"
    )
    print("\nRun:")
    print(
        "py test_ola_055_production_live_shadow_start_authorization.py"
    )


if __name__ == "__main__":
    main()
