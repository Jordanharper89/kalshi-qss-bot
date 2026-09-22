from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE = ROOT / "qseries_v2/oracle_intelligence/live_acquisition/oracle_production_live_shadow_start_authorization_consumption.py"
OLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"
TEST = ROOT / "test_ola_056_production_live_shadow_start_authorization_consumption.py"

MODULE_TEXT = r'''"""
OLA-056 Production Live Shadow Start Authorization Consumption.

Consumes the immutable OLA-055 pre-start authorization exactly once and emits
an auditable launch token. This boundary still does not invoke the OLA-023
runner or start any process, thread, loop, acquisition, scheduler tick, or
shadow cycle.

The token is intentionally separate from execution. A later controlled launch
module may require this token before invoking the already-bound read-only
live-shadow runner.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any

SCHEMA_VERSION = "OLA-056"
ENGINE_ID = "OLA-056"
TOKEN_TYPE = "oracle_production_live_shadow_single_use_launch_token"


class OracleProductionLiveShadowStartAuthorizationConsumptionError(ValueError):
    pass


class OracleProductionLiveShadowStartAuthorizationConsumptionBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLiveShadowSingleUseLaunchToken:
    schema_version: str
    engine_id: str
    token_type: str
    source_authorization_schema_version: str
    source_authorization_engine_id: str
    source_authorization_identity: int
    authorization_consumed: bool
    launch_token_issued: bool
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
        if self.schema_version != SCHEMA_VERSION or self.engine_id != ENGINE_ID:
            raise OracleProductionLiveShadowStartAuthorizationConsumptionError(
                "OLA-056 identity mismatch"
            )
        if self.token_type != TOKEN_TYPE:
            raise OracleProductionLiveShadowStartAuthorizationConsumptionError(
                "token_type mismatch"
            )
        if self.authorization_consumed is not True:
            raise OracleProductionLiveShadowStartAuthorizationConsumptionBlocked(
                "OLA-056 token requires consumed authorization"
            )
        if self.launch_token_issued is not True:
            raise OracleProductionLiveShadowStartAuthorizationConsumptionBlocked(
                "OLA-056 token issuance failed closed"
            )
        if self.read_only is not True:
            raise OracleProductionLiveShadowStartAuthorizationConsumptionBlocked(
                "OLA-056 read-only invariant violated"
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
            raise OracleProductionLiveShadowStartAuthorizationConsumptionBlocked(
                "OLA-056 observed forbidden activity during authorization consumption"
            )


class OracleProductionLiveShadowStartAuthorizationConsumer:
    read_only = True
    execution_allowed = False

    def __init__(self) -> None:
        self._lock = Lock()
        self._consumed_authorization_identities: set[int] = set()

    def consume(
        self,
        *,
        start_authorization: Any,
    ) -> OracleProductionLiveShadowSingleUseLaunchToken:
        with self._lock:
            authorization_identity = id(start_authorization)

            if authorization_identity in self._consumed_authorization_identities:
                raise OracleProductionLiveShadowStartAuthorizationConsumptionBlocked(
                    "OLA-055 start authorization already consumed"
                )

            checks = (
                getattr(start_authorization, "schema_version", None) == "OLA-055",
                getattr(start_authorization, "engine_id", None) == "OLA-055",
                getattr(start_authorization, "start_authorized", None) is True,
                getattr(start_authorization, "authorization_consumed", None) is False,
                getattr(start_authorization, "service_started", None) is False,
                getattr(start_authorization, "loop_started", None) is False,
                getattr(start_authorization, "acquisition_invoked", None) is False,
                getattr(start_authorization, "scheduler_tick_invoked", None) is False,
                getattr(start_authorization, "shadow_cycle_invoked", None) is False,
                getattr(start_authorization, "read_only", None) is True,
                getattr(start_authorization, "execution_allowed", None) is False,
            )
            if not all(checks):
                raise OracleProductionLiveShadowStartAuthorizationConsumptionBlocked(
                    "OLA-055 start authorization is not eligible for consumption"
                )

            self._consumed_authorization_identities.add(
                authorization_identity
            )

            return OracleProductionLiveShadowSingleUseLaunchToken(
                schema_version=SCHEMA_VERSION,
                engine_id=ENGINE_ID,
                token_type=TOKEN_TYPE,
                source_authorization_schema_version=(
                    start_authorization.schema_version
                ),
                source_authorization_engine_id=(
                    start_authorization.engine_id
                ),
                source_authorization_identity=authorization_identity,
                authorization_consumed=True,
                launch_token_issued=True,
            )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "TOKEN_TYPE",
    "OracleProductionLiveShadowStartAuthorizationConsumptionError",
    "OracleProductionLiveShadowStartAuthorizationConsumptionBlocked",
    "OracleProductionLiveShadowSingleUseLaunchToken",
    "OracleProductionLiveShadowStartAuthorizationConsumer",
]
'''

TEST_TEXT = r'''from __future__ import annotations

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
'''


def patch_ola030(source: str) -> str:
    import_anchor = (
        "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_start_authorization import (\n"
        "    OracleProductionLiveShadowStartAuthorizer,\n"
        ")\n"
    )
    new_import = import_anchor + (
        "\nfrom qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_start_authorization_consumption import (\n"
        "    OracleProductionLiveShadowStartAuthorizationConsumer,\n"
        ")\n"
    )

    if "OracleProductionLiveShadowStartAuthorizationConsumer" not in source:
        if import_anchor not in source:
            raise RuntimeError(
                "OLA-055 import anchor not found; install and pass OLA-055 first"
            )
        source = source.replace(import_anchor, new_import, 1)

    authorization_marker = (
        "    production_start_authorization = (\n"
    )
    if authorization_marker not in source:
        raise RuntimeError(
            "OLA-055 start authorization block not found"
        )

    if "production_start_authorization_consumer = (" not in source:
        authorization_pos = source.index(authorization_marker)
        return_pos = source.index("    return {", authorization_pos)

        consumer_block = (
            "    production_start_authorization_consumer = (\n"
            "        OracleProductionLiveShadowStartAuthorizationConsumer()\n"
            "    )\n\n"
        )
        source = source[:return_pos] + consumer_block + source[return_pos:]

    return_anchor = (
        '        "production_start_authorization": (\n'
        "            production_start_authorization\n"
        "        ),\n"
    )
    return_block = return_anchor + (
        '        "production_start_authorization_consumer": (\n'
        "            production_start_authorization_consumer\n"
        "        ),\n"
    )

    if '"production_start_authorization_consumer": (' not in source:
        if return_anchor not in source:
            raise RuntimeError(
                "OLA-055 return-map anchor not found"
            )
        source = source.replace(return_anchor, return_block, 1)

    return source


def main() -> None:
    print("========================================")
    print(" OLA-056 INSTALLER")
    print(" PRODUCTION LIVE SHADOW START AUTHORIZATION CONSUMPTION")
    print("========================================")

    if not OLA030.exists():
        raise SystemExit(f"[ERROR] Missing OLA-030 production graph: {OLA030}")

    source = OLA030.read_text(encoding="utf-8")
    required = (
        "OracleProductionLiveShadowStartAuthorizer",
        "production_start_authorization = (",
    )
    missing = [marker for marker in required if marker not in source]
    if missing:
        raise SystemExit(
            "[ERROR] OLA-055 production integration is incomplete. "
            f"Missing markers: {missing}"
        )

    MODULE.parent.mkdir(parents=True, exist_ok=True)
    MODULE.write_text(MODULE_TEXT, encoding="utf-8")
    print(f"[OK] Wrote OLA-056 authorization consumption module: {MODULE}")

    patched = patch_ola030(source)
    OLA030.write_text(patched, encoding="utf-8")
    print(f"[OK] Integrated OLA-056 into actual OLA-030 graph: {OLA030}")

    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print(f"[OK] Wrote regression test: {TEST}")

    compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
    compile(OLA030.read_text(encoding="utf-8"), str(OLA030), "exec")
    compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

    print(
        "\n[DONE] OLA-056 production live shadow start "
        "authorization consumption installed"
    )
    print("\nRun:")
    print(
        "py test_ola_056_production_live_shadow_"
        "start_authorization_consumption.py"
    )


if __name__ == "__main__":
    main()
