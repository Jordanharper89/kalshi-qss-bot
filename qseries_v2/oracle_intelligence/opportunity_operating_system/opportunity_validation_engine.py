"""
OOS-004 Opportunity Validation Engine

Validates UniversalOpportunity objects before OOS intake/ranking.

Responsibilities:
- Contract validation
- Business rule validation
- Risk guardrail warnings
- Immutable validation reports
- Read-only enforcement

Oracle validates and explains.
Decision Layer selects later.
Q Series executes later.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


OOS_VALIDATION_VERSION = "OOS-004"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ValidationSeverity(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    INFO = "info"


class ValidationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass(frozen=True)
class ValidationRuleConfig:
    min_confidence: float = 0.01
    min_abs_edge: float = 0.000001
    min_liquidity_score: float = 0.0
    max_risk_score_warning: float = 0.85
    max_execution_difficulty_warning: float = 0.85
    max_capital_required_warning: Optional[float] = None
    require_execution_adapter: bool = True
    require_explanation: bool = True
    require_evidence_warning: bool = False
    supported_opportunity_types: Optional[List[str]] = None
    schema_version: str = OOS_VALIDATION_VERSION
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationCheck:
    check_id: str
    severity: ValidationSeverity
    passed: bool
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None
    created_at: str = dc_field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        return data


@dataclass(frozen=True)
class OpportunityValidationReport:
    opportunity_id: str
    fingerprint: Optional[str]
    status: ValidationStatus
    passed_checks: int
    failed_checks: int
    warning_count: int
    info_count: int
    checks: List[ValidationCheck]
    schema_version: str = OOS_VALIDATION_VERSION
    read_only: bool = True
    validated_at: str = dc_field(default_factory=utc_now)

    def is_accepted(self) -> bool:
        return self.failed_checks == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "fingerprint": self.fingerprint,
            "status": self.status.value,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "checks": [check.to_dict() for check in self.checks],
            "schema_version": self.schema_version,
            "read_only": self.read_only,
            "validated_at": self.validated_at,
        }


class OpportunityValidationEngine:
    schema_version = OOS_VALIDATION_VERSION
    read_only = True

    def __init__(self, config: Optional[ValidationRuleConfig] = None):
        self.config = config or ValidationRuleConfig()

    def validate(self, opportunity: Any) -> OpportunityValidationReport:
        checks: List[ValidationCheck] = []
        opportunity_id = str(getattr(opportunity, "opportunity_id", "unknown_opportunity"))
        fingerprint = self._safe_fingerprint(opportunity)

        checks.extend(self._contract_checks(opportunity))
        checks.extend(self._business_rule_checks(opportunity))
        checks.extend(self._risk_guardrail_checks(opportunity))
        checks.extend(self._informational_checks(opportunity))

        failed = sum(1 for check in checks if check.severity == ValidationSeverity.FAIL and not check.passed)
        warnings = sum(1 for check in checks if check.severity == ValidationSeverity.WARNING)
        infos = sum(1 for check in checks if check.severity == ValidationSeverity.INFO)
        passed = sum(1 for check in checks if check.passed)

        if failed > 0:
            status = ValidationStatus.FAILED
        elif warnings > 0:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.PASSED

        return OpportunityValidationReport(
            opportunity_id=opportunity_id,
            fingerprint=fingerprint,
            status=status,
            passed_checks=passed,
            failed_checks=failed,
            warning_count=warnings,
            info_count=infos,
            checks=checks,
        )

    def validate_many(self, opportunities: List[Any]) -> List[OpportunityValidationReport]:
        return [self.validate(opportunity) for opportunity in opportunities]

    def accepted(self, opportunity: Any) -> bool:
        return self.validate(opportunity).is_accepted()

    def _contract_checks(self, opportunity: Any) -> List[ValidationCheck]:
        checks: List[ValidationCheck] = []

        checks.append(self._required_bool(opportunity, "read_only", True))
        checks.append(self._required_attr(opportunity, "opportunity_id"))
        checks.append(self._required_attr(opportunity, "market_id"))
        checks.append(self._required_attr(opportunity, "market_type"))
        checks.append(self._required_attr(opportunity, "venue_id"))
        checks.append(self._required_attr(opportunity, "venue_name"))
        checks.append(self._required_attr(opportunity, "opportunity_type"))
        checks.append(self._required_attr(opportunity, "direction"))
        checks.append(self._required_attr(opportunity, "expected_value"))
        checks.append(self._required_attr(opportunity, "expected_edge"))
        checks.append(self._required_attr(opportunity, "confidence"))
        checks.append(self._required_attr(opportunity, "time_window"))
        checks.append(self._required_attr(opportunity, "execution"))

        checks.append(
            ValidationCheck(
                check_id="contract.fingerprint_callable",
                severity=ValidationSeverity.FAIL,
                passed=callable(getattr(opportunity, "fingerprint", None)),
                field="fingerprint",
                message="Opportunity must expose fingerprint().",
            )
        )

        checks.append(
            ValidationCheck(
                check_id="contract.to_dict_callable",
                severity=ValidationSeverity.FAIL,
                passed=callable(getattr(opportunity, "to_dict", None)),
                field="to_dict",
                message="Opportunity must expose to_dict().",
            )
        )

        return checks

    def _business_rule_checks(self, opportunity: Any) -> List[ValidationCheck]:
        checks: List[ValidationCheck] = []

        confidence = self._float(getattr(opportunity, "confidence", None))
        checks.append(
            ValidationCheck(
                check_id="business.confidence_range",
                severity=ValidationSeverity.FAIL,
                passed=confidence is not None and 0.0 <= confidence <= 1.0,
                field="confidence",
                value=confidence,
                message="Confidence must be between 0 and 1.",
            )
        )

        checks.append(
            ValidationCheck(
                check_id="business.confidence_minimum",
                severity=ValidationSeverity.FAIL,
                passed=confidence is not None and confidence >= self.config.min_confidence,
                field="confidence",
                value=confidence,
                message=f"Confidence must be >= {self.config.min_confidence}.",
            )
        )

        edge = self._float(getattr(opportunity, "expected_edge", None))
        checks.append(
            ValidationCheck(
                check_id="business.edge_minimum",
                severity=ValidationSeverity.FAIL,
                passed=edge is not None and abs(edge) >= self.config.min_abs_edge,
                field="expected_edge",
                value=edge,
                message=f"Absolute expected edge must be >= {self.config.min_abs_edge}.",
            )
        )

        liquidity = self._float(getattr(opportunity, "liquidity_score", None))
        checks.append(
            ValidationCheck(
                check_id="business.liquidity_minimum",
                severity=ValidationSeverity.FAIL,
                passed=liquidity is not None and liquidity >= self.config.min_liquidity_score,
                field="liquidity_score",
                value=liquidity,
                message=f"Liquidity score must be >= {self.config.min_liquidity_score}.",
            )
        )

        if self.config.require_explanation:
            explanation = getattr(opportunity, "explanation", None)
            checks.append(
                ValidationCheck(
                    check_id="business.explanation_required",
                    severity=ValidationSeverity.FAIL,
                    passed=isinstance(explanation, str) and len(explanation.strip()) > 0,
                    field="explanation",
                    value=explanation,
                    message="Explanation is required.",
                )
            )

        if self.config.require_execution_adapter:
            execution = getattr(opportunity, "execution", None)
            adapter = getattr(execution, "required_execution_adapter", None)
            checks.append(
                ValidationCheck(
                    check_id="business.execution_adapter_required",
                    severity=ValidationSeverity.FAIL,
                    passed=isinstance(adapter, str) and len(adapter.strip()) > 0,
                    field="execution.required_execution_adapter",
                    value=adapter,
                    message="Required execution adapter must be present.",
                )
            )

        supported = self.config.supported_opportunity_types
        if supported is not None:
            opportunity_type = self._enum_value(getattr(opportunity, "opportunity_type", None))
            checks.append(
                ValidationCheck(
                    check_id="business.supported_opportunity_type",
                    severity=ValidationSeverity.FAIL,
                    passed=opportunity_type in supported,
                    field="opportunity_type",
                    value=opportunity_type,
                    message="Opportunity type must be supported by validation config.",
                )
            )

        return checks

    def _risk_guardrail_checks(self, opportunity: Any) -> List[ValidationCheck]:
        checks: List[ValidationCheck] = []

        risk = self._float(getattr(opportunity, "risk_score", None))
        if risk is not None and risk >= self.config.max_risk_score_warning:
            checks.append(
                ValidationCheck(
                    check_id="risk.high_risk_score",
                    severity=ValidationSeverity.WARNING,
                    passed=True,
                    field="risk_score",
                    value=risk,
                    message="Risk score is above warning threshold.",
                )
            )

        execution = getattr(opportunity, "execution", None)
        difficulty = self._float(getattr(execution, "execution_difficulty", None))
        if difficulty is not None and difficulty >= self.config.max_execution_difficulty_warning:
            checks.append(
                ValidationCheck(
                    check_id="risk.high_execution_difficulty",
                    severity=ValidationSeverity.WARNING,
                    passed=True,
                    field="execution.execution_difficulty",
                    value=difficulty,
                    message="Execution difficulty is above warning threshold.",
                )
            )

        capital_required = self._float(getattr(execution, "capital_required", None))
        if (
            self.config.max_capital_required_warning is not None
            and capital_required is not None
            and capital_required > self.config.max_capital_required_warning
        ):
            checks.append(
                ValidationCheck(
                    check_id="risk.capital_required_warning",
                    severity=ValidationSeverity.WARNING,
                    passed=True,
                    field="execution.capital_required",
                    value=capital_required,
                    message="Capital required exceeds warning threshold.",
                )
            )

        evidence_refs = getattr(opportunity, "evidence_refs", [])
        if self.config.require_evidence_warning and not evidence_refs:
            checks.append(
                ValidationCheck(
                    check_id="risk.missing_evidence_warning",
                    severity=ValidationSeverity.WARNING,
                    passed=True,
                    field="evidence_refs",
                    value=0,
                    message="Opportunity has no evidence references.",
                )
            )

        risk_flags = getattr(opportunity, "risk_flags", [])
        if risk_flags:
            checks.append(
                ValidationCheck(
                    check_id="risk.flags_present",
                    severity=ValidationSeverity.WARNING,
                    passed=True,
                    field="risk_flags",
                    value=list(risk_flags),
                    message="Opportunity contains risk flags.",
                )
            )

        return checks

    def _informational_checks(self, opportunity: Any) -> List[ValidationCheck]:
        checks: List[ValidationCheck] = []

        checks.append(
            ValidationCheck(
                check_id="info.schema_version",
                severity=ValidationSeverity.INFO,
                passed=True,
                field="schema_version",
                value=getattr(opportunity, "schema_version", None),
                message="Opportunity schema version recorded.",
            )
        )

        quality = getattr(opportunity, "quality_score", None)
        if callable(quality):
            try:
                value = quality()
            except Exception:
                value = None

            checks.append(
                ValidationCheck(
                    check_id="info.quality_score",
                    severity=ValidationSeverity.INFO,
                    passed=True,
                    field="quality_score",
                    value=value,
                    message="Opportunity quality score recorded.",
                )
            )

        return checks

    def _required_attr(self, opportunity: Any, field_name: str) -> ValidationCheck:
        value = getattr(opportunity, field_name, None)
        return ValidationCheck(
            check_id=f"contract.{field_name}",
            severity=ValidationSeverity.FAIL,
            passed=value is not None,
            field=field_name,
            value=value,
            message=f"Opportunity requires field: {field_name}.",
        )

    def _required_bool(self, opportunity: Any, field_name: str, expected: bool) -> ValidationCheck:
        value = getattr(opportunity, field_name, None)
        return ValidationCheck(
            check_id=f"contract.{field_name}",
            severity=ValidationSeverity.FAIL,
            passed=value is expected,
            field=field_name,
            value=value,
            message=f"Opportunity field {field_name} must be {expected}.",
        )

    def _safe_fingerprint(self, opportunity: Any) -> Optional[str]:
        fn = getattr(opportunity, "fingerprint", None)
        if callable(fn):
            try:
                return str(fn())
            except Exception:
                return None
        return None

    def _float(self, value: Any) -> Optional[float]:
        try:
            if value is None:
                return None
            return float(value)
        except Exception:
            return None

    def _enum_value(self, value: Any) -> str:
        return value.value if hasattr(value, "value") else str(value)


def build_validation_engine(config: Optional[ValidationRuleConfig] = None) -> OpportunityValidationEngine:
    return OpportunityValidationEngine(config=config)


__all__ = [
    "OOS_VALIDATION_VERSION",
    "ValidationSeverity",
    "ValidationStatus",
    "ValidationRuleConfig",
    "ValidationCheck",
    "OpportunityValidationReport",
    "OpportunityValidationEngine",
    "build_validation_engine",
]
