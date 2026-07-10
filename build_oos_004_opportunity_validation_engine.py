from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / "qseries_v2"
ORACLE = BASE / "oracle_intelligence"
OOS = ORACLE / "opportunity_operating_system"

MODULE_PATH = OOS / "opportunity_validation_engine.py"
INIT_PATH = OOS / "__init__.py"
TEST_PATH = ROOT / "test_oos_004_opportunity_validation_engine.py"

MODULE_CODE = r'''"""
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

from dataclasses import dataclass, field, asdict
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
    created_at: str = field(default_factory=utc_now)

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
    validated_at: str = field(default_factory=utc_now)

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
'''

TEST_CODE = r'''from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_validation_engine import (
    OOS_VALIDATION_VERSION,
    ValidationRuleConfig,
    ValidationStatus,
    build_validation_engine,
)
from qseries_v2.oracle_intelligence.universal_market_model import UniversalMarketFactory
from qseries_v2.oracle_intelligence.universal_opportunity_model import (
    OpportunityExecutionProfile,
    OpportunityTimeWindow,
    UniversalOpportunityFactory,
)


def _market():
    return UniversalMarketFactory.from_prediction_market(
        venue_id="kalshi",
        venue_name="Kalshi",
        market_id="KXBTC-YES",
        title="Will BTC close above 100k?",
        bid=0.52,
        ask=0.55,
        liquidity=30000,
    )


def _valid_opportunity():
    return UniversalOpportunityFactory.prediction_market_scalp(
        market=_market(),
        fair_value=0.67,
        market_price=0.55,
        confidence=0.84,
        explanation="Oracle fair value is above market ask.",
        liquidity_score=0.76,
        risk_score=0.31,
        time_window=OpportunityTimeWindow(urgency_score=0.5, freshness_score=1.0),
        execution=OpportunityExecutionProfile(
            required_execution_adapter="prediction_market",
            execution_difficulty=0.25,
            capital_required=100,
        ),
    )


def test_oos_004_valid_opportunity_passes():
    engine = build_validation_engine()
    report = engine.validate(_valid_opportunity())

    assert report.schema_version == OOS_VALIDATION_VERSION
    assert report.read_only is True
    assert report.status in {ValidationStatus.PASSED, ValidationStatus.WARNING}
    assert report.failed_checks == 0
    assert report.is_accepted() is True
    assert report.fingerprint is not None


def test_oos_004_non_read_only_fails():
    class BadOpportunity:
        read_only = False
        opportunity_id = "bad_1"
        market_id = "bad_market"
        market_type = "bad_type"
        venue_id = "bad_venue"
        venue_name = "Bad Venue"
        opportunity_type = "bad"
        direction = "BUY"
        expected_value = 1
        expected_edge = 0.1
        confidence = 0.5
        time_window = object()
        execution = object()
        explanation = "bad"

        def fingerprint(self):
            return "bad"

        def to_dict(self):
            return {}

    engine = build_validation_engine()
    report = engine.validate(BadOpportunity())

    assert report.status == ValidationStatus.FAILED
    assert report.failed_checks >= 1
    assert report.is_accepted() is False


def test_oos_004_missing_required_fields_fail():
    class IncompleteOpportunity:
        read_only = True

        def fingerprint(self):
            return "incomplete"

        def to_dict(self):
            return {}

    engine = build_validation_engine()
    report = engine.validate(IncompleteOpportunity())

    assert report.status == ValidationStatus.FAILED
    assert report.failed_checks > 5
    assert report.is_accepted() is False


def test_oos_004_business_rules_fail_low_confidence_and_zero_edge():
    opportunity = UniversalOpportunityFactory.prediction_market_scalp(
        market=_market(),
        fair_value=0.55,
        market_price=0.55,
        confidence=0.0,
        explanation="No edge.",
        liquidity_score=0.5,
        risk_score=0.2,
    )

    engine = build_validation_engine()
    report = engine.validate(opportunity)

    assert report.status == ValidationStatus.FAILED
    assert report.failed_checks >= 2
    assert report.is_accepted() is False


def test_oos_004_warning_for_high_risk_execution_and_flags():
    market = UniversalMarketFactory.from_solana_token_launch(
        token_mint="Mint111",
        token_symbol="MEME",
        liquidity=1200,
    )

    opportunity = UniversalOpportunityFactory.solana_token_snipe(
        market=market,
        expected_multiple=2.5,
        confidence=0.62,
        explanation="High-risk launch candidate.",
        execution=OpportunityExecutionProfile(
            required_execution_adapter="solana_wallet",
            execution_difficulty=0.95,
            capital_required=2500,
        ),
    )

    engine = build_validation_engine(
        ValidationRuleConfig(
            max_capital_required_warning=1000,
            require_evidence_warning=True,
        )
    )

    report = engine.validate(opportunity)

    assert report.failed_checks == 0
    assert report.warning_count >= 3
    assert report.status == ValidationStatus.WARNING
    assert report.is_accepted() is True


def test_oos_004_supported_type_config():
    opportunity = _valid_opportunity()
    engine = build_validation_engine(
        ValidationRuleConfig(
            supported_opportunity_types=["arbitrage_spread"]
        )
    )

    report = engine.validate(opportunity)

    assert report.status == ValidationStatus.FAILED
    assert any(check.check_id == "business.supported_opportunity_type" for check in report.checks)


def test_oos_004_validate_many_and_serialization():
    engine = build_validation_engine()
    reports = engine.validate_many([_valid_opportunity(), _valid_opportunity()])

    assert len(reports) == 2
    assert all(report.is_accepted() for report in reports)

    data = reports[0].to_dict()

    assert data["schema_version"] == OOS_VALIDATION_VERSION
    assert data["read_only"] is True
    assert "checks" in data
    assert data["opportunity_id"] != "unknown_opportunity"


def test_oos_004_report_immutability():
    report = build_validation_engine().validate(_valid_opportunity())

    try:
        report.status = ValidationStatus.FAILED
        raise AssertionError("Validation report should be immutable.")
    except FrozenInstanceError:
        pass


if __name__ == "__main__":
    test_oos_004_valid_opportunity_passes()
    test_oos_004_non_read_only_fails()
    test_oos_004_missing_required_fields_fail()
    test_oos_004_business_rules_fail_low_confidence_and_zero_edge()
    test_oos_004_warning_for_high_risk_execution_and_flags()
    test_oos_004_supported_type_config()
    test_oos_004_validate_many_and_serialization()
    test_oos_004_report_immutability()

    report = build_validation_engine().validate(_valid_opportunity())

    print("[PASS] OOS-004 Opportunity Validation Engine")
    print(
        {
            "schema_version": report.schema_version,
            "status": report.status.value,
            "passed_checks": report.passed_checks,
            "failed_checks": report.failed_checks,
            "warning_count": report.warning_count,
            "read_only": report.read_only,
        }
    )
'''

def ensure_dirs():
    OOS.mkdir(parents=True, exist_ok=True)


def update_init():
    INIT_PATH.touch(exist_ok=True)
    text = INIT_PATH.read_text(encoding="utf-8")

    import_block = '''from .opportunity_validation_engine import (
    OOS_VALIDATION_VERSION,
    ValidationSeverity,
    ValidationStatus,
    ValidationRuleConfig,
    ValidationCheck,
    OpportunityValidationReport,
    OpportunityValidationEngine,
    build_validation_engine,
)
'''

    if "from .opportunity_validation_engine import" not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        text += import_block

    if "__all__" not in text:
        text += "\n__all__ = []\n"

    for item in [
        '"OOS_VALIDATION_VERSION"',
        '"ValidationSeverity"',
        '"ValidationStatus"',
        '"ValidationRuleConfig"',
        '"ValidationCheck"',
        '"OpportunityValidationReport"',
        '"OpportunityValidationEngine"',
        '"build_validation_engine"',
    ]:
        if item not in text:
            text = text.replace("__all__ = [", f"__all__ = [\n    {item},")

    INIT_PATH.write_text(text, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OOS-004 INSTALLER")
    print(" Opportunity Validation Engine")
    print("=" * 40)

    ensure_dirs()

    MODULE_PATH.write_text(MODULE_CODE, encoding="utf-8")
    print(f"[OK] Wrote {MODULE_PATH}")

    TEST_PATH.write_text(TEST_CODE, encoding="utf-8")
    print(f"[OK] Wrote {TEST_PATH}")

    update_init()
    print(f"[OK] Updated {INIT_PATH}")

    print("\n[DONE] OOS-004 installed")
    print("\nRun:")
    print("py test_oos_004_opportunity_validation_engine.py")


if __name__ == "__main__":
    main()