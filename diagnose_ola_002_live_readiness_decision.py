from __future__ import annotations

import json
import os
import traceback
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent

ENV_FILE = ROOT / ".env"

RUNTIME_ROOT = (
    ROOT
    / "runtime"
    / "oracle_live_shadow"
)

DIAGNOSTIC_OUTPUT = (
    ROOT
    / "runtime"
    / "oracle_live_shadow"
    / "diagnostics"
    / "ola_002_live_readiness_decision.json"
)


def canonical(value: Any) -> Any:
    if is_dataclass(value):
        return canonical(
            asdict(value)
        )

    if isinstance(value, Mapping):
        return {
            str(key): canonical(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set, frozenset)):
        return [
            canonical(item)
            for item in value
        ]

    if isinstance(value, datetime):
        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            return value.isoformat()

        return value.astimezone(
            timezone.utc
        ).isoformat()

    if isinstance(value, Path):
        return str(value)

    if hasattr(
        value,
        "to_canonical_dict",
    ):
        try:
            return canonical(
                value.to_canonical_dict()
            )
        except TypeError:
            try:
                return canonical(
                    value.to_canonical_dict(
                        include_decision_hash=True
                    )
                )
            except Exception:
                pass

    if hasattr(
        value,
        "__dict__",
    ):
        return canonical(
            vars(value)
        )

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ) or value is None:
        return value

    return repr(value)


def load_env_file(
    path: Path,
) -> dict[str, str]:
    if not path.exists():
        raise RuntimeError(
            f"Required .env file is missing: {path}"
        )

    values: dict[str, str] = {}

    for raw_line in path.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        name, value = line.split(
            "=",
            1,
        )

        name = name.strip()
        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        values[name] = value

    return values


def load_runtime_environment() -> dict[str, str]:
    environment = dict(
        os.environ
    )

    environment.update(
        load_env_file(
            ENV_FILE
        )
    )

    database_url = (
        environment.get(
            "ORACLE_POSTGRES_URL"
        )
        or environment.get(
            "DATABASE_URL"
        )
    )

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL or ORACLE_POSTGRES_URL "
            "is missing from .env"
        )

    return environment


def print_mapping(
    title: str,
    payload: Any,
) -> None:
    print()
    print(title)
    print("-" * 72)

    print(
        json.dumps(
            canonical(payload),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
    )


def main() -> int:
    print("========================================")
    print(" OLA-002 LIVE READINESS DIAGNOSTIC")
    print(" ONE PRODUCTION READ-ONLY PROBE")
    print(" NO CONTINUOUS POLLING")
    print("========================================")

    environment = load_runtime_environment()

    print("[OK] Environment loaded")
    print(
        "[OK] PostgreSQL configuration present"
    )

    from qseries_v2.oracle_intelligence.live_acquisition.oracle_acquisition_source_control_engine import (
        OracleAcquisitionSourceControlEngine,
    )

    from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_first_real_shadow_corpus_launch_command import (
        build_real_oracle_shadow_graph,
    )

    captured: dict[str, Any] = {
        "diagnostic": (
            "ola_002_live_readiness_decision"
        ),
        "started_at": datetime.now(
            timezone.utc
        ),
        "production_module_changes": False,
        "continuous_polling_started": False,
        "execution_allowed": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }

    original_evaluate = (
        OracleAcquisitionSourceControlEngine.evaluate
    )

    def diagnostic_evaluate(
        self,
        *,
        health_observation,
        rate_observation,
        evaluated_at,
        replay_metadata,
        audit_metadata,
    ):
        captured[
            "ola_002_health_observation"
        ] = canonical(
            health_observation
        )

        captured[
            "ola_002_rate_observation"
        ] = canonical(
            rate_observation
        )

        captured[
            "ola_002_evaluated_at"
        ] = canonical(
            evaluated_at
        )

        captured[
            "ola_002_replay_metadata"
        ] = canonical(
            replay_metadata
        )

        captured[
            "ola_002_audit_metadata"
        ] = canonical(
            audit_metadata
        )

        decision = original_evaluate(
            self,
            health_observation=(
                health_observation
            ),
            rate_observation=(
                rate_observation
            ),
            evaluated_at=evaluated_at,
            replay_metadata=(
                replay_metadata
            ),
            audit_metadata=(
                audit_metadata
            ),
        )

        captured[
            "ola_002_decision"
        ] = canonical(
            decision
        )

        captured[
            "ola_002_reason_codes"
        ] = list(
            decision.reason_codes
        )

        captured[
            "ola_002_acquisition_allowed"
        ] = decision.acquisition_allowed

        return decision

    OracleAcquisitionSourceControlEngine.evaluate = (
        diagnostic_evaluate
    )

    try:
        graph = build_real_oracle_shadow_graph(
            runtime_root=RUNTIME_ROOT.resolve(
                strict=False
            ),
            environment=environment,
            sleep_callable=lambda seconds: None,
            service_tick_interval_seconds=5,
        )

        print("[OK] OLA-030 production graph assembled")

        required_graph_keys = {
            "source_control_engine",
            "live_readiness_gate",
            "readiness_provider",
            "initial_polling_state",
            "readiness_kwargs_factory",
        }

        missing = sorted(
            required_graph_keys
            - set(graph)
        )

        if missing:
            raise RuntimeError(
                "Production graph is missing: "
                + ", ".join(
                    missing
                )
            )

        print(
            "[OK] OLA-002 source-control engine resolved"
        )

        print(
            "[OK] OLA-018 live-readiness gate resolved"
        )

        polling_state = graph[
            "initial_polling_state"
        ]

        checked_at = datetime.now(
            timezone.utc
        )

        evaluated_at = datetime.now(
            timezone.utc
        )

        readiness_kwargs = graph[
            "readiness_kwargs_factory"
        ](
            1,
            polling_state,
            checked_at,
            evaluated_at,
        )

        captured[
            "readiness_kwargs"
        ] = canonical(
            readiness_kwargs
        )

        captured[
            "initial_polling_state"
        ] = canonical(
            polling_state
        )

        print(
            "[START] Running one OLA-018 "
            "production readiness evaluation"
        )

        try:
            readiness_provider = graph[
                "readiness_provider"
            ]

            class _StopAfterFirstReadinessAttempt(
                RuntimeError
            ):
                pass

            def stop_after_first_attempt(
                delay_seconds,
            ):
                raise _StopAfterFirstReadinessAttempt(
                    "First production readiness attempt "
                    "captured; retry loop intentionally "
                    "stopped by diagnostic"
                )

            original_provider_sleeper = (
                readiness_provider._sleeper
            )

            readiness_provider._sleeper = (
                stop_after_first_attempt
            )

            try:
                readiness = readiness_provider(
                    **dict(
                        readiness_kwargs
                    )
                )
            finally:
                readiness_provider._sleeper = (
                    original_provider_sleeper
                )

            captured[
                "readiness_result"
            ] = canonical(
                readiness
            )

            captured[
                "readiness_passed"
            ] = True

            print(
                "[PASS] Production readiness evaluation passed"
            )

        except Exception as exc:
            captured[
                "readiness_passed"
            ] = False

            captured[
                "readiness_exception_type"
            ] = type(
                exc
            ).__name__

            captured[
                "readiness_exception"
            ] = str(
                exc
            )

            captured[
                "readiness_traceback"
            ] = traceback.format_exc()

            print(
                "[BLOCKED] Production readiness "
                "evaluation raised:"
            )

            print(
                f"{type(exc).__name__}: {exc}"
            )

    except Exception as exc:
        captured[
            "diagnostic_setup_exception_type"
        ] = type(
            exc
        ).__name__

        captured[
            "diagnostic_setup_exception"
        ] = str(
            exc
        )

        captured[
            "diagnostic_setup_traceback"
        ] = traceback.format_exc()

        print(
            "[FAIL] Diagnostic setup failed:"
        )

        print(
            f"{type(exc).__name__}: {exc}"
        )

    finally:
        OracleAcquisitionSourceControlEngine.evaluate = (
            original_evaluate
        )

    captured[
        "completed_at"
    ] = datetime.now(
        timezone.utc
    )

    reason_codes = captured.get(
        "ola_002_reason_codes"
    )

    if reason_codes is not None:
        reason_code_set = set(
            reason_codes
        )

        captured[
            "reason_code_analysis"
        ] = {
            "source_reachable_present": (
                "source_reachable"
                in reason_code_set
            ),
            "source_unreachable_present": (
                "source_unreachable"
                in reason_code_set
            ),
            (
                "consecutive_failures_within_policy_present"
            ): (
                "consecutive_failures_within_policy"
                in reason_code_set
            ),
            (
                "consecutive_failures_exceeded_present"
            ): (
                "consecutive_failures_exceeded"
                in reason_code_set
            ),
            "latency_within_policy_present": (
                "latency_within_policy"
                in reason_code_set
            ),
            (
                "latency_policy_not_required_present"
            ): (
                "latency_policy_not_required"
                in reason_code_set
            ),
            "latency_policy_exceeded_present": (
                "latency_policy_exceeded"
                in reason_code_set
            ),
            "latency_required_but_missing_present": (
                "latency_required_but_missing"
                in reason_code_set
            ),
            "rate_window_within_policy_present": (
                "rate_window_within_policy"
                in reason_code_set
            ),
            "rate_reserve_preserved_present": (
                "rate_reserve_preserved"
                in reason_code_set
            ),
            "acquisition_allowed_present": (
                "acquisition_allowed"
                in reason_code_set
            ),
        }

    DIAGNOSTIC_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    DIAGNOSTIC_OUTPUT.write_text(
        json.dumps(
            canonical(
                captured
            ),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print_mapping(
        "OLA-016 / OLA-002 CAPTURE",
        captured,
    )

    print()
    print(
        "[OK] Diagnostic artifact written:"
    )

    print(
        DIAGNOSTIC_OUTPUT.resolve()
    )

    print()
    print(
        "[DONE] One readiness evaluation completed"
    )

    print(
        "[SAFE] Continuous polling was not started"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )