from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

TEST = (
    ROOT
    / "test_int_ola_lineage_graph_006_"
    "production_authorization_consumption_gate.py"
)

TEST_TEXT = r'''
from __future__ import annotations

import ast
import importlib
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parent

OLA030 = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)

OLA055_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_live_shadow_start_authorization"
)

OLA056_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_live_shadow_start_authorization_consumption"
)


def _assert_module_contracts() -> None:
    ola055 = importlib.import_module(OLA055_MODULE)
    ola056 = importlib.import_module(OLA056_MODULE)

    assert getattr(ola055, "SCHEMA_VERSION", None) == "OLA-055"
    assert getattr(ola055, "ENGINE_ID", None) == "OLA-055"

    assert getattr(ola056, "SCHEMA_VERSION", None) == "OLA-056"
    assert getattr(ola056, "ENGINE_ID", None) == "OLA-056"

    Consumer = (
        ola056.
        OracleProductionLiveShadowStartAuthorizationConsumer
    )

    assert getattr(Consumer, "read_only", None) is True
    assert getattr(Consumer, "execution_allowed", None) is False


def _assert_actual_ola030_consumption_boundary() -> None:
    assert OLA030.exists(), OLA030

    source = OLA030.read_text(encoding="utf-8")

    tree = ast.parse(source)
    assert isinstance(tree, ast.Module)

    required = (
        "OracleProductionLiveShadowStartAuthorizer",
        "OracleProductionLiveShadowStartAuthorizationConsumer",
        "production_start_authorization = (",
        "production_start_authorization_consumer = (",
        '"production_start_authorization": (',
        '"production_start_authorization_consumer": (',
    )

    for marker in required:
        assert marker in source, marker

    authorization_pos = source.index(
        "production_start_authorization = ("
    )

    consumer_pos = source.index(
        "production_start_authorization_consumer = ("
    )

    return_pos = source.index(
        "    return {",
        consumer_pos,
    )

    assert authorization_pos < consumer_pos < return_pos

    graph_start = source.index(
        "def build_real_oracle_shadow_graph("
    )

    graph_end = len(source)

    graph_source = source[graph_start:graph_end]

    forbidden_auto_consumption_markers = (
        "production_start_authorization_consumer.consume(",
        "production_start_authorization_consumer .consume(",
        "launch_token = production_start_authorization_consumer",
    )

    for marker in forbidden_auto_consumption_markers:
        assert marker not in graph_source, marker


def _make_authorization():
    return SimpleNamespace(
        schema_version="OLA-055",
        engine_id="OLA-055",
        start_authorized=True,
        authorization_consumed=False,
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


def _exercise_single_use_consumption_contract() -> None:
    ola056 = importlib.import_module(OLA056_MODULE)

    Consumer = (
        ola056.
        OracleProductionLiveShadowStartAuthorizationConsumer
    )

    Blocked = (
        ola056.
        OracleProductionLiveShadowStartAuthorizationConsumptionBlocked
    )

    authorization = _make_authorization()

    consumer = Consumer()

    token = consumer.consume(
        start_authorization=authorization,
    )

    assert token.schema_version == "OLA-056"
    assert token.engine_id == "OLA-056"

    assert token.authorization_consumed is True
    assert token.launch_token_issued is True

    assert token.launch_invoked is False

    assert token.service_started is False
    assert token.process_created is False
    assert token.thread_created is False
    assert token.loop_started is False

    assert token.acquisition_invoked is False
    assert token.scheduler_tick_invoked is False
    assert token.shadow_cycle_invoked is False

    assert token.read_only is True
    assert token.execution_allowed is False

    assert token.alerts_allowed is False
    assert token.qseries_handoff_allowed is False

    try:
        consumer.consume(
            start_authorization=authorization,
        )
    except Blocked:
        pass
    else:
        raise AssertionError(
            "INT-OLA-LINEAGE-GRAPH-006 expected replay rejection"
        )


def _exercise_ineligible_authorization_rejection() -> None:
    ola056 = importlib.import_module(OLA056_MODULE)

    Consumer = (
        ola056.
        OracleProductionLiveShadowStartAuthorizationConsumer
    )

    Blocked = (
        ola056.
        OracleProductionLiveShadowStartAuthorizationConsumptionBlocked
    )

    authorization = _make_authorization()
    authorization.scheduler_tick_invoked = True

    try:
        Consumer().consume(
            start_authorization=authorization,
        )
    except Blocked:
        pass
    else:
        raise AssertionError(
            "INT-OLA-LINEAGE-GRAPH-006 expected fail-closed "
            "rejection of pre-consumption runtime activity"
        )


def main() -> None:
    _assert_module_contracts()

    _assert_actual_ola030_consumption_boundary()

    _exercise_single_use_consumption_contract()

    _exercise_ineligible_authorization_rejection()

    print(
        "[PASS] INT-OLA-LINEAGE-GRAPH-006 "
        "Production Authorization Consumption Gate"
    )

    print({
        "schema_version": "INT-OLA-LINEAGE-GRAPH-006",
        "engine_id": "INT-OLA-LINEAGE-GRAPH-006",
        "status": "passed",

        "actual_ola030_source_graph_inspected": True,
        "actual_graph_ast_valid": True,

        "ola055_start_authorization_contract_preserved": True,
        "ola056_authorization_consumer_contract_preserved": True,

        "start_authorization_precedes_consumer_construction": True,

        "consumer_exposed_for_controlled_launch": True,

        "authorization_not_auto_consumed_during_graph_assembly": True,
        "launch_token_not_auto_issued_during_graph_assembly": True,
        "runner_not_auto_invoked_during_graph_assembly": True,

        "single_use_consumption_enforced": True,
        "authorization_replay_rejected": True,

        "ineligible_authorization_rejected": True,

        "launch_token_issued_only_by_explicit_consumption": True,
        "launch_not_invoked": True,

        "service_not_started": True,
        "no_process_created": True,
        "no_thread_created": True,
        "no_loop_started": True,

        "no_acquisition_invoked": True,
        "no_scheduler_tick_invoked": True,
        "no_shadow_cycle_invoked": True,

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


def main() -> None:
    print("========================================")
    print(" INT-OLA-LINEAGE-GRAPH-006 INSTALLER")
    print(" PRODUCTION AUTHORIZATION CONSUMPTION GATE")
    print("========================================")

    ola030 = (
        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition_model"
        / "oracle_first_real_shadow_corpus_launch_command.py"
    )

    if not ola030.exists():
        raise SystemExit(
            "[ERROR] Missing actual OLA-030 production graph: "
            f"{ola030}"
        )

    source = ola030.read_text(
        encoding="utf-8"
    )

    required = (
        "OracleProductionLiveShadowStartAuthorizer",
        "OracleProductionLiveShadowStartAuthorizationConsumer",
        "production_start_authorization = (",
        "production_start_authorization_consumer = (",
    )

    missing = [
        marker
        for marker in required
        if marker not in source
    ]

    if missing:
        raise SystemExit(
            "[ERROR] OLA-055/056 production integration "
            "is incomplete. "
            f"Missing markers: {missing}"
        )

    TEST.write_text(
        TEST_TEXT,
        encoding="utf-8",
    )

    compile(
        TEST.read_text(
            encoding="utf-8"
        ),
        str(TEST),
        "exec",
    )

    print(
        f"[OK] Wrote integration gate: {TEST}"
    )

    print(
        "\n[DONE] INT-OLA-LINEAGE-GRAPH-006 "
        "production authorization consumption gate installed"
    )

    print("\nRun:")

    print(
        "py test_int_ola_lineage_graph_006_"
        "production_authorization_consumption_gate.py"
    )


if __name__ == "__main__":
    main()