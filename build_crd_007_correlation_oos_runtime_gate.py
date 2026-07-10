from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "correlation_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "correlation_oos_runtime_gate.py"
TEST = ROOT / "test_crd_007_correlation_oos_runtime_gate.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional

from .correlation_pipeline_bridge import (
    CorrelationPipelineBridgeResult,
    run_correlation_pipeline,
)


READ_ONLY = True
SCHEMA_VERSION = "CRD-007"
ENGINE_ID = "oracle.discovery.correlation.oos_runtime_gate"

_ALLOWED_RUNTIME_MODES = {
    "oos",
    "replay",
    "paper",
    "shadow",
}

_EXECUTION_CONTEXT_KEYS = {
    "execute",
    "execution",
    "trade",
    "buy",
    "sell",
    "submit",
    "submit_order",
    "place_order",
    "cancel_order",
    "replace_order",
    "sign",
    "sign_transaction",
    "broadcast",
    "broadcast_transaction",
    "transfer",
    "withdraw",
    "deposit",
}


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _deep_sort(value[key])
            for key in sorted(value.keys(), key=str)
        }
    if isinstance(value, list):
        return [_deep_sort(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_deep_sort(item) for item in value)
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = repr(_deep_sort(payload)).encode("utf-8")
    return sha256(encoded).hexdigest()


def _contains_execution_request(
    runtime_context: Mapping[str, Any],
) -> bool:
    for key, value in runtime_context.items():
        normalized_key = str(key).strip().lower()

        if (
            normalized_key in _EXECUTION_CONTEXT_KEYS
            and bool(value)
        ):
            return True

        if isinstance(value, Mapping):
            if _contains_execution_request(value):
                return True

    return False


@dataclass(frozen=True)
class CorrelationOOSRuntimeGateResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    reason: str
    pipeline_hash: str
    opportunity_count: int
    checks: Dict[str, bool] = field(default_factory=dict)
    runtime_context: Dict[str, Any] = field(default_factory=dict)
    read_only: bool = True
    oos_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class CorrelationOOSRuntimeGate:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        require_accepted_pipeline: bool = True,
        max_opportunities: int = 10000,
    ) -> None:
        if int(max_opportunities) < 0:
            raise ValueError(
                "max_opportunities must be non-negative"
            )

        self.require_accepted_pipeline = bool(
            require_accepted_pipeline
        )
        self.max_opportunities = int(
            max_opportunities
        )

    def validate(
        self,
        pipeline_result: CorrelationPipelineBridgeResult,
        runtime_context: Optional[Mapping[str, Any]] = None,
    ) -> CorrelationOOSRuntimeGateResult:
        if not isinstance(
            pipeline_result,
            CorrelationPipelineBridgeResult,
        ):
            raise TypeError(
                "pipeline_result must be a "
                "CorrelationPipelineBridgeResult"
            )

        if (
            runtime_context is not None
            and not isinstance(runtime_context, Mapping)
        ):
            raise TypeError(
                "runtime_context must be a mapping or None"
            )

        context = dict(runtime_context or {})
        clean_context = _deep_sort(context)
        runtime_mode = str(
            context.get("mode", "oos")
        ).strip().lower()

        no_execution_request = not _contains_execution_request(
            context
        )

        checks = {
            "read_only": (
                pipeline_result.read_only is True
            ),
            "pipeline_schema": (
                pipeline_result.schema_version
                == "CRD-006"
            ),
            "pipeline_engine": (
                pipeline_result.engine_id
                == (
                    "oracle.discovery.correlation."
                    "pipeline_bridge"
                )
            ),
            "pipeline_hash_present": bool(
                pipeline_result.pipeline_hash
            ),
            "pipeline_accepted": (
                pipeline_result.accepted is True
                if self.require_accepted_pipeline
                else True
            ),
            "pipeline_status_consistent": (
                (
                    pipeline_result.accepted is True
                    and pipeline_result.status
                    == "accepted"
                )
                or (
                    pipeline_result.accepted is False
                    and pipeline_result.status
                    == "rejected"
                )
            ),
            "opportunity_count_matches": (
                pipeline_result.opportunity_count
                == (
                    pipeline_result.discovery
                    .opportunity_count
                )
            ),
            "opportunity_count_within_limit": (
                0
                <= pipeline_result.opportunity_count
                <= self.max_opportunities
            ),
            "discovery_read_only": (
                pipeline_result.discovery.read_only
                is True
            ),
            "pipeline_gate_accepted": (
                pipeline_result.gate.accepted is True
            ),
            "registry_entry_accepted": (
                pipeline_result.registry_entry.accepted
                is True
            ),
            "runtime_mode_valid": (
                runtime_mode
                in _ALLOWED_RUNTIME_MODES
            ),
            "no_execution_context": (
                no_execution_request
            ),
            "audit_read_only": (
                pipeline_result.audit.get("read_only")
                is True
            ),
            "audit_execution_disabled": (
                pipeline_result.audit.get(
                    "execution_capable"
                )
                is False
            ),
            "audit_external_mutation_disabled": (
                pipeline_result.audit.get(
                    "external_mutation_allowed"
                )
                is False
            ),
        }

        accepted = all(checks.values())
        status = (
            "accepted"
            if accepted
            else "rejected"
        )

        failed_checks = [
            name
            for name, passed in checks.items()
            if not passed
        ]

        reason = (
            "all correlation OOS runtime checks passed"
            if accepted
            else "failed checks: "
            + ", ".join(failed_checks)
        )

        unsigned = CorrelationOOSRuntimeGateResult(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            accepted=accepted,
            reason=reason,
            pipeline_hash=(
                pipeline_result.pipeline_hash
            ),
            opportunity_count=(
                pipeline_result.opportunity_count
            ),
            checks=checks,
            runtime_context=clean_context,
            read_only=True,
            oos_hash="",
        )

        return CorrelationOOSRuntimeGateResult(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            accepted=unsigned.accepted,
            reason=unsigned.reason,
            pipeline_hash=unsigned.pipeline_hash,
            opportunity_count=(
                unsigned.opportunity_count
            ),
            checks=unsigned.checks,
            runtime_context=unsigned.runtime_context,
            read_only=True,
            oos_hash=_stable_hash(
                unsigned.canonical()
            ),
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "read_only": True,
            "supports": [
                "oos_runtime_validation",
                "replay_runtime_validation",
                "paper_runtime_validation",
                "shadow_runtime_validation",
                "execution_context_rejection",
                "nested_execution_context_rejection",
                "pipeline_integrity_validation",
                "deterministic_oos_hashing",
            ],
            "allowed_runtime_modes": sorted(
                _ALLOWED_RUNTIME_MODES
            ),
            "max_opportunities": (
                self.max_opportunities
            ),
            "require_accepted_pipeline": (
                self.require_accepted_pipeline
            ),
        }

    def assert_read_only(self) -> bool:
        forbidden = [
            "buy",
            "sell",
            "trade",
            "execute",
            "order",
            "sign",
            "submit",
            "broadcast",
        ]

        offenders = sorted(
            word
            for word in forbidden
            if word in set(dir(self))
        )

        if offenders:
            raise AssertionError(
                f"mutation-like methods are forbidden: "
                f"{offenders}"
            )

        return True


def validate_correlation_oos_runtime(
    pipeline_result: CorrelationPipelineBridgeResult,
    runtime_context: Optional[Mapping[str, Any]] = None,
    require_accepted_pipeline: bool = True,
    max_opportunities: int = 10000,
) -> CorrelationOOSRuntimeGateResult:
    gate = CorrelationOOSRuntimeGate(
        require_accepted_pipeline=(
            require_accepted_pipeline
        ),
        max_opportunities=max_opportunities,
    )

    return gate.validate(
        pipeline_result=pipeline_result,
        runtime_context=runtime_context,
    )


def run_correlation_oos_runtime_gate(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "correlation.generic",
    observed_at: Optional[str] = None,
    runtime_context: Optional[Mapping[str, Any]] = None,
    strong_correlation_threshold: float = 0.70,
    correlation_break_threshold: float = 0.30,
    return_divergence_threshold: float = 0.04,
    min_sample_size: int = 20,
    max_opportunities: int = 10000,
) -> CorrelationOOSRuntimeGateResult:
    pipeline = run_correlation_pipeline(
        raw_records=raw_records,
        source_name=source_name,
        observed_at=observed_at,
        strong_correlation_threshold=(
            strong_correlation_threshold
        ),
        correlation_break_threshold=(
            correlation_break_threshold
        ),
        return_divergence_threshold=(
            return_divergence_threshold
        ),
        min_sample_size=min_sample_size,
    )

    return validate_correlation_oos_runtime(
        pipeline_result=pipeline,
        runtime_context=runtime_context,
        require_accepted_pipeline=True,
        max_opportunities=max_opportunities,
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "CorrelationOOSRuntimeGate",
    "CorrelationOOSRuntimeGateResult",
    "validate_correlation_oos_runtime",
    "run_correlation_oos_runtime_gate",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_oos_runtime_gate import (
    CorrelationOOSRuntimeGate,
    run_correlation_oos_runtime_gate,
    validate_correlation_oos_runtime,
)
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_pipeline_bridge import (
    run_correlation_pipeline,
)


RAW = [
    {
        "primary_market_id": "KXTEST-A",
        "related_market_id": "KXTEST-B",
        "venue": "kalshi",
        "correlation": 0.82,
        "baseline_correlation": 0.80,
        "recent_correlation": 0.20,
        "lag": 0,
        "window": "30d",
        "sample_size": 120,
        "primary_return": 0.06,
        "related_return": -0.01,
        "observed_at": (
            "2026-07-09T00:00:00+00:00"
        ),
    },
    {
        "primary_market_id": "KXTEST-C",
        "related_market_id": "KXTEST-D",
        "venue": "kalshi",
        "correlation": -0.76,
        "baseline_correlation": -0.72,
        "recent_correlation": 0.31,
        "lag": 2,
        "window": "30d",
        "sample_size": 150,
        "primary_return": -0.03,
        "related_return": 0.04,
        "observed_at": (
            "2026-07-09T00:00:00+00:00"
        ),
    },
]


def _build_pipeline():
    return run_correlation_pipeline(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )


def test_correlation_oos_runtime_gate_accepts_valid_pipeline():
    pipeline = _build_pipeline()

    gate = CorrelationOOSRuntimeGate()
    assert gate.assert_read_only() is True

    result = gate.validate(
        pipeline,
        runtime_context={
            "mode": "oos",
            "fold": "test-fold-001",
        },
    )

    assert result.schema_version == "CRD-007"
    assert (
        result.engine_id
        == (
            "oracle.discovery.correlation."
            "oos_runtime_gate"
        )
    )
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.read_only is True
    assert (
        result.pipeline_hash
        == pipeline.pipeline_hash
    )
    assert (
        result.opportunity_count
        == pipeline.opportunity_count
    )
    assert result.checks["runtime_mode_valid"] is True
    assert (
        result.checks["no_execution_context"]
        is True
    )
    assert result.oos_hash


def test_correlation_oos_runtime_gate_rejects_execution_context():
    pipeline = _build_pipeline()

    result = validate_correlation_oos_runtime(
        pipeline,
        runtime_context={
            "mode": "oos",
            "execute": True,
        },
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert (
        result.checks["no_execution_context"]
        is False
    )
    assert result.read_only is True
    assert result.oos_hash


def test_correlation_oos_runtime_gate_rejects_nested_execution_context():
    pipeline = _build_pipeline()

    result = validate_correlation_oos_runtime(
        pipeline,
        runtime_context={
            "mode": "shadow",
            "request": {
                "submit_order": True,
            },
        },
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert (
        result.checks["no_execution_context"]
        is False
    )


def test_correlation_oos_runtime_gate_rejects_invalid_mode():
    pipeline = _build_pipeline()

    result = validate_correlation_oos_runtime(
        pipeline,
        runtime_context={
            "mode": "live_execution",
        },
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert (
        result.checks["runtime_mode_valid"]
        is False
    )


def test_correlation_oos_runtime_gate_is_replayable():
    result1 = run_correlation_oos_runtime_gate(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "mode": "replay",
            "fold": "A",
        },
    )

    result2 = run_correlation_oos_runtime_gate(
        list(reversed(RAW)),
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "fold": "A",
            "mode": "replay",
        },
    )

    assert result1.oos_hash == result2.oos_hash
    assert result1.checks == result2.checks
    assert (
        result1.pipeline_hash
        == result2.pipeline_hash
    )


def test_correlation_oos_runtime_gate_accepts_empty_pipeline():
    result = run_correlation_oos_runtime_gate(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "mode": "shadow",
        },
    )

    assert result.status == "accepted"
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert result.oos_hash


def test_correlation_oos_runtime_gate_enforces_opportunity_limit():
    pipeline = _build_pipeline()

    result = validate_correlation_oos_runtime(
        pipeline,
        runtime_context={
            "mode": "oos",
        },
        max_opportunities=0,
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert (
        result.checks[
            "opportunity_count_within_limit"
        ]
        is False
    )


def test_correlation_oos_runtime_gate_rejects_wrong_types():
    gate = CorrelationOOSRuntimeGate()

    try:
        gate.validate(
            {"status": "accepted"},
            runtime_context={"mode": "oos"},
        )
    except TypeError as exc:
        assert str(exc) == (
            "pipeline_result must be a "
            "CorrelationPipelineBridgeResult"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid pipeline type"
        )

    pipeline = _build_pipeline()

    try:
        gate.validate(
            pipeline,
            runtime_context=["oos"],
        )
    except TypeError as exc:
        assert str(exc) == (
            "runtime_context must be a mapping or None"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid context type"
        )


if __name__ == "__main__":
    test_correlation_oos_runtime_gate_accepts_valid_pipeline()
    test_correlation_oos_runtime_gate_rejects_execution_context()
    test_correlation_oos_runtime_gate_rejects_nested_execution_context()
    test_correlation_oos_runtime_gate_rejects_invalid_mode()
    test_correlation_oos_runtime_gate_is_replayable()
    test_correlation_oos_runtime_gate_accepts_empty_pipeline()
    test_correlation_oos_runtime_gate_enforces_opportunity_limit()
    test_correlation_oos_runtime_gate_rejects_wrong_types()

    result = run_correlation_oos_runtime_gate(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "mode": "oos",
        },
    )

    print(
        "[PASS] CRD-007 "
        "Correlation OOS Runtime Gate"
    )
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted": result.accepted,
            "opportunities": (
                result.opportunity_count
            ),
            "read_only": result.read_only,
        }
    )
''', encoding="utf-8")

existing = INIT.read_text(
    encoding="utf-8"
) if INIT.exists() else ""

exports = '''
from .correlation_oos_runtime_gate import (
    CorrelationOOSRuntimeGate,
    CorrelationOOSRuntimeGateResult,
    validate_correlation_oos_runtime,
    run_correlation_oos_runtime_gate,
)
'''

if "correlation_oos_runtime_gate" not in existing:
    INIT.write_text(
        existing.rstrip() + "\n" + exports.lstrip(),
        encoding="utf-8",
    )

print("========================================")
print(" CRD-007 INSTALLER")
print(" Correlation OOS Runtime Gate")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] CRD-007 installed")
print()
print("Run:")
print("py test_crd_007_correlation_oos_runtime_gate.py")