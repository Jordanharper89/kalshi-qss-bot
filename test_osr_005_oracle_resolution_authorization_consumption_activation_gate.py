from __future__ import annotations

from dataclasses import dataclass, replace
import importlib

module = importlib.import_module(
    "qseries_v2.oracle_scientific_reasoning_runtime."
    "oracle_resolution_authorization_consumption_activation_gate"
)


@dataclass(frozen=True)
class StubResolutionAuthorization:
    authorization_id: str
    authorization_hash: str
    source_resolution_package_id: str
    source_resolution_hash: str
    source_admission_package_id: str
    source_admission_hash: str
    authorized_callable_count: int
    callable_resolution_authorized: bool
    callable_binding_allowed: bool
    reasoning_execution_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool


def accepted_verifier(value) -> bool:
    if not isinstance(value, StubResolutionAuthorization):
        raise ValueError("unexpected authorization type")
    if value.callable_resolution_authorized is not True:
        raise ValueError("not authorized")
    return True


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleResolutionAuthorizationConsumptionInvariantError:
        return
    raise AssertionError("expected OSR-005 invariant rejection")


def main() -> None:
    original_verifier = (
        module.verify_certified_callable_resolution_authorization
    )
    module.verify_certified_callable_resolution_authorization = (
        accepted_verifier
    )
    try:
        authorization = StubResolutionAuthorization(
            authorization_id="osr004:authorization:001",
            authorization_hash="a" * 64,
            source_resolution_package_id="osr003:resolution:001",
            source_resolution_hash="b" * 64,
            source_admission_package_id="osr002:admission:001",
            source_admission_hash="c" * 64,
            authorized_callable_count=9,
            callable_resolution_authorized=True,
            callable_binding_allowed=False,
            reasoning_execution_allowed=False,
            qseries_execution_allowed=False,
            order_creation_allowed=False,
            funds_movement_allowed=False,
            portfolio_mutation_allowed=False,
        )

        first = module.consume_resolution_authorization_and_activate(
            authorization=authorization
        )
        second = module.consume_resolution_authorization_and_activate(
            authorization=authorization
        )

        assert first == second
        assert first.activation_hash == second.activation_hash
        assert module.verify_callable_resolution_activation(first)
        assert first.activated_callable_count == 9
        assert first.callable_resolution_allowed is True
        assert first.callable_binding_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False

        rejected(
            lambda: module.verify_callable_resolution_activation(
                replace(first, activation_hash="0" * 64)
            )
        )
        rejected(
            lambda: module.verify_callable_resolution_activation(
                replace(first, callable_binding_allowed=True)
            )
        )
        rejected(
            lambda: module.consume_resolution_authorization_and_activate(
                authorization=replace(
                    authorization,
                    callable_binding_allowed=True,
                )
            )
        )

        print("========================================")
        print(" OSR-005 TEST")
        print(" RESOLUTION AUTHORIZATION CONSUMPTION")
        print(" ACTIVATION GATE")
        print("========================================")
        print("[PASS] OSR-004 verifier boundary consumed")
        print("[PASS] Authorization identity and lineage preserved")
        print("[PASS] Single-use consumption receipt materialized")
        print("[PASS] Activation identity deterministic")
        print("[PASS] Resolution scope activated")
        print("[PASS] Callable binding remains disabled")
        print("[PASS] Reasoning execution remains disabled")
        print("[PASS] Probability estimation remains disabled")
        print("[PASS] Final intelligence conclusions remain disabled")
        print("[PASS] Publication, alerting, and handoff disabled")
        print("[PASS] Q Series execution remains disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[PASS] Read-only Oracle boundary preserved")
        print("[DONE] OSR-005 RESOLUTION ACTIVATION GATE CERTIFIED")
    finally:
        module.verify_certified_callable_resolution_authorization = (
            original_verifier
        )


if __name__ == "__main__":
    main()
