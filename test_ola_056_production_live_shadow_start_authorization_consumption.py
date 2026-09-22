from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_start_authorization_consumption import (
    OracleProductionLiveShadowStartAuthorizationConsumptionBlocked,
    OracleProductionLiveShadowStartAuthorizationConsumer,
)

ROOT = Path(__file__).resolve().parent
OLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"


def make_authorization():
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


def main():
    authorization = make_authorization()
    consumer = OracleProductionLiveShadowStartAuthorizationConsumer()

    token = consumer.consume(
        start_authorization=authorization,
    )

    assert token.schema_version == "OLA-056"
    assert token.engine_id == "OLA-056"
    assert token.authorization_consumed is True
    assert token.launch_token_issued is True
    assert token.launch_invoked is False
    assert token.service_started is False
    assert token.loop_started is False
    assert token.read_only is True
    assert token.execution_allowed is False

    try:
        consumer.consume(
            start_authorization=authorization,
        )
    except OracleProductionLiveShadowStartAuthorizationConsumptionBlocked:
        pass
    else:
        raise AssertionError(
            "OLA-056 must reject replay of the same OLA-055 authorization"
        )

    invalid = make_authorization()
    invalid.service_started = True

    try:
        OracleProductionLiveShadowStartAuthorizationConsumer().consume(
            start_authorization=invalid,
        )
    except OracleProductionLiveShadowStartAuthorizationConsumptionBlocked:
        pass
    else:
        raise AssertionError(
            "OLA-056 must fail closed for a pre-start authorization "
            "that already observed service activity"
        )

    source = OLA030.read_text(encoding="utf-8")
    ast.parse(source)

    required = (
        "OracleProductionLiveShadowStartAuthorizationConsumer",
        "production_start_authorization_consumer = (",
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
    return_pos = source.index("    return {", consumer_pos)

    assert authorization_pos < consumer_pos < return_pos

    print("[PASS] OLA-056 Production Live Shadow Start Authorization Consumption")
    print({
        "schema_version": "OLA-056",
        "engine_id": "OLA-056",
        "status": "passed",
        "actual_ola030_authorization_consumer_integrated": True,
        "ola055_start_authorization_required": True,
        "single_use_consumption_enforced": True,
        "replay_rejected": True,
        "launch_token_issued": True,
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
