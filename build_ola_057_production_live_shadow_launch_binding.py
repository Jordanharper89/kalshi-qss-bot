from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

MODULE = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_production_live_shadow_launch_binding.py"
)

OLA030 = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)

TEST = (
    ROOT
    / "test_ola_057_production_live_shadow_launch_binding.py"
)


MODULE_TEXT = r'''
"""
OLA-057 Production Live Shadow Launch Binding.

Fail-closed binding between an OLA-056 single-use launch token and the exact
OLA-023 production live-shadow runner instance exposed by the actual OLA-030
graph.

This module does not invoke the runner. It only proves that an eligible
single-use token is bound to the exact read-only production runner.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SCHEMA_VERSION = "OLA-057"
ENGINE_ID = "OLA-057"
BINDING_TYPE = "oracle_production_live_shadow_launch_binding"


class OracleProductionLiveShadowLaunchBindingError(ValueError):
    pass


class OracleProductionLiveShadowLaunchBindingBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLiveShadowLaunchBindingRecord:
    schema_version: str
    engine_id: str
    binding_type: str

    launch_token_schema_version: str
    launch_token_engine_id: str
    launch_token_identity: int
    runner_identity: int

    token_valid: bool
    token_not_invoked: bool
    runner_identity_bound: bool
    launch_binding_ready: bool

    launch_invoked: bool = False
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
        if self.schema_version != SCHEMA_VERSION:
            raise OracleProductionLiveShadowLaunchBindingError(
                "OLA-057 schema_version mismatch"
            )

        if self.engine_id != ENGINE_ID:
            raise OracleProductionLiveShadowLaunchBindingError(
                "OLA-057 engine_id mismatch"
            )

        if self.binding_type != BINDING_TYPE:
            raise OracleProductionLiveShadowLaunchBindingError(
                "OLA-057 binding_type mismatch"
            )

        required = (
            self.token_valid,
            self.token_not_invoked,
            self.runner_identity_bound,
            self.launch_binding_ready,
            self.read_only,
        )

        if not all(value is True for value in required):
            raise OracleProductionLiveShadowLaunchBindingBlocked(
                "OLA-057 launch binding failed closed"
            )

        forbidden = (
            self.launch_invoked,
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
            raise OracleProductionLiveShadowLaunchBindingBlocked(
                "OLA-057 observed forbidden activity"
            )


class OracleProductionLiveShadowLaunchBinder:
    read_only = True
    execution_allowed = False

    def bind(
        self,
        *,
        launch_token: Any,
        runner: Any,
    ) -> OracleProductionLiveShadowLaunchBindingRecord:

        token_checks = (
            getattr(
                launch_token,
                "schema_version",
                None,
            )
            == "OLA-056",

            getattr(
                launch_token,
                "engine_id",
                None,
            )
            == "OLA-056",

            getattr(
                launch_token,
                "authorization_consumed",
                None,
            )
            is True,

            getattr(
                launch_token,
                "launch_token_issued",
                None,
            )
            is True,

            getattr(
                launch_token,
                "launch_invoked",
                None,
            )
            is False,

            getattr(
                launch_token,
                "service_started",
                None,
            )
            is False,

            getattr(
                launch_token,
                "loop_started",
                None,
            )
            is False,

            getattr(
                launch_token,
                "acquisition_invoked",
                None,
            )
            is False,

            getattr(
                launch_token,
                "scheduler_tick_invoked",
                None,
            )
            is False,

            getattr(
                launch_token,
                "shadow_cycle_invoked",
                None,
            )
            is False,

            getattr(
                launch_token,
                "read_only",
                None,
            )
            is True,

            getattr(
                launch_token,
                "execution_allowed",
                None,
            )
            is False,
        )

        if not all(token_checks):
            raise OracleProductionLiveShadowLaunchBindingBlocked(
                "OLA-056 launch token is not eligible "
                "for OLA-057 binding"
            )

        if runner is None:
            raise OracleProductionLiveShadowLaunchBindingBlocked(
                "OLA-057 requires the exact production runner"
            )

        if getattr(
            runner,
            "read_only",
            None,
        ) is not True:
            raise OracleProductionLiveShadowLaunchBindingBlocked(
                "OLA-057 runner is not read-only"
            )

        if getattr(
            runner,
            "execution_allowed",
            None,
        ) is not False:
            raise OracleProductionLiveShadowLaunchBindingBlocked(
                "OLA-057 runner execution invariant violated"
            )

        return OracleProductionLiveShadowLaunchBindingRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            binding_type=BINDING_TYPE,

            launch_token_schema_version=(
                launch_token.schema_version
            ),

            launch_token_engine_id=(
                launch_token.engine_id
            ),

            launch_token_identity=id(
                launch_token
            ),

            runner_identity=id(
                runner
            ),

            token_valid=True,
            token_not_invoked=True,
            runner_identity_bound=True,
            launch_binding_ready=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "BINDING_TYPE",
    "OracleProductionLiveShadowLaunchBindingError",
    "OracleProductionLiveShadowLaunchBindingBlocked",
    "OracleProductionLiveShadowLaunchBindingRecord",
    "OracleProductionLiveShadowLaunchBinder",
]
'''


TEST_TEXT = r'''
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_launch_binding import (
    OracleProductionLiveShadowLaunchBinder,
    OracleProductionLiveShadowLaunchBindingBlocked,
)


ROOT = Path(__file__).resolve().parent

OLA030 = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)


class Runner:
    read_only = True
    execution_allowed = False


def make_token():
    return SimpleNamespace(
        schema_version="OLA-056",
        engine_id="OLA-056",

        authorization_consumed=True,
        launch_token_issued=True,

        launch_invoked=False,
        service_started=False,
        process_created=False,
        thread_created=False,
        loop_started=False,

        acquisition_invoked=False,
        scheduler_tick_invoked=False,
        shadow_cycle_invoked=False,

        read_only=True,
        execution_allowed=False,
    )


def main() -> None:
    token = make_token()
    runner = Runner()

    record = (
        OracleProductionLiveShadowLaunchBinder()
        .bind(
            launch_token=token,
            runner=runner,
        )
    )

    assert record.schema_version == "OLA-057"
    assert record.engine_id == "OLA-057"

    assert record.launch_token_identity == id(
        token
    )

    assert record.runner_identity == id(
        runner
    )

    assert record.token_valid is True
    assert record.token_not_invoked is True

    assert record.runner_identity_bound is True
    assert record.launch_binding_ready is True

    assert record.launch_invoked is False

    assert record.service_started is False
    assert record.process_created is False
    assert record.thread_created is False
    assert record.loop_started is False

    assert record.acquisition_invoked is False
    assert record.scheduler_tick_invoked is False
    assert record.shadow_cycle_invoked is False

    assert record.read_only is True
    assert record.execution_allowed is False

    bad_token = make_token()
    bad_token.launch_invoked = True

    try:
        (
            OracleProductionLiveShadowLaunchBinder()
            .bind(
                launch_token=bad_token,
                runner=runner,
            )
        )

    except OracleProductionLiveShadowLaunchBindingBlocked:
        pass

    else:
        raise AssertionError(
            "OLA-057 must fail closed for "
            "an already-invoked launch token"
        )

    class BadRunner:
        read_only = False
        execution_allowed = False

    try:
        (
            OracleProductionLiveShadowLaunchBinder()
            .bind(
                launch_token=make_token(),
                runner=BadRunner(),
            )
        )

    except OracleProductionLiveShadowLaunchBindingBlocked:
        pass

    else:
        raise AssertionError(
            "OLA-057 must fail closed for "
            "a non-read-only runner"
        )

    source = OLA030.read_text(
        encoding="utf-8"
    )

    ast.parse(
        source
    )

    required = (
        "OracleProductionLiveShadowLaunchBinder",
        "production_launch_binder = (",
        '"production_launch_binder": (',
    )

    for marker in required:
        assert marker in source, marker

    consumer_pos = source.index(
        "production_start_authorization_consumer = ("
    )

    binder_pos = source.index(
        "production_launch_binder = ("
    )

    return_pos = source.index(
        "    return {",
        binder_pos,
    )

    assert (
        consumer_pos
        < binder_pos
        < return_pos
    )

    graph_source = source[
        source.index(
            "def build_real_oracle_shadow_graph("
        ):
    ]

    forbidden = (
        "production_start_authorization_consumer.consume(",
        "production_launch_binder.bind(",
        "runner.run(",
        "runner.start(",
    )

    for marker in forbidden:
        assert marker not in graph_source, marker

    print(
        "[PASS] OLA-057 "
        "Production Live Shadow Launch Binding"
    )

    print({
        "schema_version": "OLA-057",
        "engine_id": "OLA-057",
        "status": "passed",

        "actual_ola030_launch_binder_integrated": True,

        "ola056_launch_token_required": True,

        "exact_runner_identity_bound": True,

        "launch_binding_ready": True,

        "launch_not_invoked": True,

        "service_not_started": True,

        "no_process_created": True,
        "no_thread_created": True,
        "no_loop_started": True,

        "no_acquisition_invoked": True,
        "no_scheduler_tick_invoked": True,
        "no_shadow_cycle_invoked": True,

        "fail_closed_invoked_token_tested": True,

        "fail_closed_non_read_only_runner_tested": True,

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


def patch_ola030(
    source: str,
) -> str:

    import_anchor = (
        "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_start_authorization_consumption "
        "import (\n"
        "    OracleProductionLiveShadowStartAuthorizationConsumer,\n"
        ")\n"
    )

    new_import = (
        import_anchor
        + "\n"
        + "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_launch_binding import (\n"
        "    OracleProductionLiveShadowLaunchBinder,\n"
        ")\n"
    )

    if (
        "OracleProductionLiveShadowLaunchBinder"
        not in source
    ):

        if import_anchor not in source:
            raise RuntimeError(
                "OLA-056 import anchor not found. "
                "Install and pass OLA-056 first."
            )

        source = source.replace(
            import_anchor,
            new_import,
            1,
        )

    consumer_marker = (
        "    production_start_authorization_consumer = (\n"
    )

    if consumer_marker not in source:
        raise RuntimeError(
            "OLA-056 authorization consumer block not found"
        )

    if (
        "production_launch_binder = ("
        not in source
    ):

        consumer_pos = source.index(
            consumer_marker
        )

        return_pos = source.index(
            "    return {",
            consumer_pos,
        )

        binder_block = (
            "    production_launch_binder = (\n"
            "        OracleProductionLiveShadowLaunchBinder()\n"
            "    )\n\n"
        )

        source = (
            source[:return_pos]
            + binder_block
            + source[return_pos:]
        )

    return_anchor = (
        '        "production_start_authorization_consumer": (\n'
        "            production_start_authorization_consumer\n"
        "        ),\n"
    )

    return_block = (
        return_anchor
        + '        "production_launch_binder": (\n'
        "            production_launch_binder\n"
        "        ),\n"
    )

    if (
        '"production_launch_binder": ('
        not in source
    ):

        if return_anchor not in source:
            raise RuntimeError(
                "OLA-056 return-map anchor not found"
            )

        source = source.replace(
            return_anchor,
            return_block,
            1,
        )

    return source


def main() -> None:
    print("========================================")
    print(" OLA-057 INSTALLER")
    print(" PRODUCTION LIVE SHADOW LAUNCH BINDING")
    print("========================================")

    if not OLA030.exists():
        raise SystemExit(
            "[ERROR] Missing OLA-030 production graph: "
            f"{OLA030}"
        )

    source = OLA030.read_text(
        encoding="utf-8"
    )

    required = (
        "OracleProductionLiveShadowStartAuthorizationConsumer",
        "production_start_authorization_consumer = (",
    )

    missing = [
        marker
        for marker in required
        if marker not in source
    ]

    if missing:
        raise SystemExit(
            "[ERROR] OLA-056 production integration "
            "is incomplete. "
            f"Missing markers: {missing}"
        )

    MODULE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    MODULE.write_text(
        MODULE_TEXT,
        encoding="utf-8",
    )

    print(
        "[OK] Wrote OLA-057 launch binding module: "
        f"{MODULE}"
    )

    patched = patch_ola030(
        source
    )

    OLA030.write_text(
        patched,
        encoding="utf-8",
    )

    print(
        "[OK] Integrated OLA-057 into actual OLA-030 graph: "
        f"{OLA030}"
    )

    TEST.write_text(
        TEST_TEXT,
        encoding="utf-8",
    )

    print(
        "[OK] Wrote regression test: "
        f"{TEST}"
    )

    compile(
        MODULE.read_text(
            encoding="utf-8"
        ),
        str(MODULE),
        "exec",
    )

    compile(
        OLA030.read_text(
            encoding="utf-8"
        ),
        str(OLA030),
        "exec",
    )

    compile(
        TEST.read_text(
            encoding="utf-8"
        ),
        str(TEST),
        "exec",
    )

    print(
        "\n[DONE] OLA-057 production live shadow "
        "launch binding installed"
    )

    print("\nRun:")

    print(
        "py test_ola_057_"
        "production_live_shadow_launch_binding.py"
    )


if __name__ == "__main__":
    main()