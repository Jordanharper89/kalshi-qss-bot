from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "universal_market_model_schema_engine.py"
TEST = ROOT / "test_oi_165_universal_market_model_schema_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-165 — Oracle Universal Market Model Schema Engine

Read-only schema engine for Universal Market Model records.

Purpose:
- Define and validate the common schema that all market adapters must map into.
- Preserve Oracle's universal intelligence model across prediction markets, crypto,
  stocks, ETFs, futures, commodities, forex, macro, weather, news, and alternative data.
- Enforce read-only boundaries before downstream Oracle intelligence modules consume data.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _stable_text(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(f"{k}:{_stable_text(value[k])}" for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _hash(value: Any, size: int = 24) -> str:
    return sha256(_stable_text(value).encode("utf-8")).hexdigest()[:size]


@dataclass
class UMMSchemaIssue:
    field: str
    severity: str
    code: str
    message: str


@dataclass
class OracleUniversalMarketModelSchemaEngine:
    name: str = "oracle_universal_market_model_schema_engine"
    version: str = "OI-165"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    schema_version: str = "universal_market_model_schema_v1"

    supported_domains: List[str] = field(default_factory=lambda: [
        "PREDICTION_MARKETS",
        "CRYPTO",
        "STOCKS",
        "ETFS",
        "FUTURES",
        "COMMODITIES",
        "FOREX",
        "MACROECONOMICS",
        "WEATHER",
        "NEWS",
        "ALTERNATIVE_DATA",
    ])

    required_fields: List[str] = field(default_factory=lambda: [
        "domain",
        "symbol",
        "timestamp",
        "source",
        "price",
        "confidence",
        "lineage",
    ])

    optional_fields: List[str] = field(default_factory=lambda: [
        "name",
        "description",
        "exchange",
        "venue",
        "bid",
        "ask",
        "spread",
        "volume",
        "open_interest",
        "event_id",
        "contract_id",
        "forecast_value",
        "probability",
        "sentiment_score",
        "macro_series_id",
        "weather_metric",
        "news_topic",
        "alternative_signal",
        "metadata",
    ])

    def schema(self) -> Dict[str, Any]:
        return {
            "module": self.name,
            "version": self.version,
            "schema_version": self.schema_version,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "supported_domains": list(self.supported_domains),
            "required_fields": list(self.required_fields),
            "optional_fields": list(self.optional_fields),
            "field_contract": {
                "domain": "Uppercase market domain routed through Universal Market Model.",
                "symbol": "Domain-specific symbol, ticker, contract, event, pair, or series identifier.",
                "timestamp": "ISO-8601 observation timestamp.",
                "source": "Adapter or data source name.",
                "price": "Observed price, probability, quote, index value, forecast value, or normalized numeric value.",
                "confidence": "Oracle/source confidence from 0 to 100.",
                "lineage": "Traceable lineage identifier or payload hash.",
            },
            "safety_contract": {
                "oracle_read_only": True,
                "oracle_executes_trades": False,
                "oracle_manages_positions": False,
                "oracle_submits_orders": False,
                "execution_owner": self.execution_owner,
            },
        }

    def normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        record = _safe_dict(record)

        domain = str(record.get("domain") or "UNKNOWN").upper()
        symbol = str(record.get("symbol") or record.get("ticker") or record.get("contract_id") or "UNKNOWN")
        timestamp = str(record.get("timestamp") or _utc_now())
        source = str(record.get("source") or record.get("adapter") or "unknown_source")
        price = _num(record.get("price", record.get("value", record.get("probability", 0.0))))
        confidence = max(0.0, min(100.0, _num(record.get("confidence"), 0.0)))

        lineage_payload = {
            "domain": domain,
            "symbol": symbol,
            "timestamp": timestamp,
            "source": source,
            "price": price,
            "confidence": confidence,
            "raw_lineage": record.get("lineage") or record.get("lineage_hash"),
        }

        normalized = {
            "umm_record_id": _hash(lineage_payload),
            "schema_version": self.schema_version,
            "domain": domain,
            "symbol": symbol,
            "timestamp": timestamp,
            "source": source,
            "price": price,
            "confidence": confidence,
            "lineage": str(record.get("lineage") or record.get("lineage_hash") or _hash(lineage_payload)),
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }

        for field_name in self.optional_fields:
            if field_name in record and field_name not in normalized:
                normalized[field_name] = record[field_name]

        normalized["metadata"] = _safe_dict(record.get("metadata")) if isinstance(record.get("metadata"), dict) else record.get("metadata", {})
        return normalized

    def validate_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self.normalize_record(record)
        issues: List[UMMSchemaIssue] = []

        for field_name in self.required_fields:
            value = normalized.get(field_name)
            if value in (None, ""):
                issues.append(UMMSchemaIssue(
                    field=field_name,
                    severity="critical",
                    code="missing_required_field",
                    message=f"Universal Market Model record missing required field: {field_name}",
                ))

        if normalized.get("domain") not in self.supported_domains:
            issues.append(UMMSchemaIssue(
                field="domain",
                severity="warning",
                code="unsupported_domain",
                message=f"Domain {normalized.get('domain')} is not currently registered as a supported domain.",
            ))

        if normalized.get("read_only") is not True:
            issues.append(UMMSchemaIssue(
                field="read_only",
                severity="critical",
                code="read_only_violation",
                message="UMM record must be read_only=True.",
            ))

        if normalized.get("execution_allowed") is not False:
            issues.append(UMMSchemaIssue(
                field="execution_allowed",
                severity="critical",
                code="execution_violation",
                message="UMM record must not allow execution.",
            ))

        if normalized.get("execution_owner") != "Q Series":
            issues.append(UMMSchemaIssue(
                field="execution_owner",
                severity="critical",
                code="execution_owner_violation",
                message="UMM execution_owner must be Q Series.",
            ))

        confidence = _num(normalized.get("confidence"))
        if confidence < 0 or confidence > 100:
            issues.append(UMMSchemaIssue(
                field="confidence",
                severity="critical",
                code="confidence_out_of_bounds",
                message="Confidence must be between 0 and 100.",
            ))

        critical_count = sum(1 for issue in issues if issue.severity == "critical")
        warning_count = sum(1 for issue in issues if issue.severity == "warning")

        if critical_count:
            validation_status = "umm_record_invalid"
        elif warning_count:
            validation_status = "umm_record_valid_with_warnings"
        else:
            validation_status = "umm_record_valid"

        validation_id = _hash({
            "record": normalized,
            "issues": [issue.__dict__ for issue in issues],
            "status": validation_status,
        })

        return {
            "module": self.name,
            "version": self.version,
            "schema_version": self.schema_version,
            "validation_id": validation_id,
            "validated_at": _utc_now(),
            "validation_status": validation_status,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "issue_count": len(issues),
            "normalized_record": normalized,
            "issues": [issue.__dict__ for issue in issues],
        }

    def validate_batch(self, records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        reports = [self.validate_record(record) for record in records]

        invalid_count = sum(1 for report in reports if report["validation_status"] == "umm_record_invalid")
        warning_count = sum(1 for report in reports if report["validation_status"] == "umm_record_valid_with_warnings")
        valid_count = sum(1 for report in reports if report["validation_status"] == "umm_record_valid")

        if invalid_count:
            batch_status = "umm_batch_invalid"
        elif warning_count:
            batch_status = "umm_batch_valid_with_warnings"
        else:
            batch_status = "umm_batch_valid"

        batch_id = _hash({
            "reports": reports,
            "batch_status": batch_status,
        })

        return {
            "module": self.name,
            "version": self.version,
            "schema_version": self.schema_version,
            "umm_batch_id": batch_id,
            "batch_status": batch_status,
            "validated_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "record_count": len(reports),
            "valid_count": valid_count,
            "warning_count": warning_count,
            "invalid_count": invalid_count,
            "reports": reports,
        }


oracle_universal_market_model_schema_engine = OracleUniversalMarketModelSchemaEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.universal_market_model_schema_engine import (
    oracle_universal_market_model_schema_engine,
)


def test_schema_contract_is_read_only():
    schema = oracle_universal_market_model_schema_engine.schema()

    assert schema["read_only"] is True
    assert schema["execution_allowed"] is False
    assert schema["execution_owner"] == "Q Series"
    assert "domain" in schema["required_fields"]
    assert "CRYPTO" in schema["supported_domains"]


def test_normalize_record():
    record = oracle_universal_market_model_schema_engine.normalize_record({
        "domain": "crypto",
        "ticker": "SOL-USD",
        "source": "crypto_adapter",
        "value": 144.25,
        "confidence": 88,
        "lineage_hash": "abc123",
    })

    assert record["domain"] == "CRYPTO"
    assert record["symbol"] == "SOL-USD"
    assert record["price"] == 144.25
    assert record["confidence"] == 88.0
    assert record["read_only"] is True
    assert record["execution_allowed"] is False


def test_valid_record_passes():
    report = oracle_universal_market_model_schema_engine.validate_record({
        "domain": "STOCKS",
        "symbol": "AAPL",
        "timestamp": "2026-07-02T00:00:00+00:00",
        "source": "stocks_adapter",
        "price": 200.0,
        "confidence": 91.0,
        "lineage": "lineage-001",
    })

    assert report["validation_status"] == "umm_record_valid"
    assert report["issue_count"] == 0
    assert report["normalized_record"]["execution_owner"] == "Q Series"


def test_unsupported_domain_warns():
    report = oracle_universal_market_model_schema_engine.validate_record({
        "domain": "UNKNOWN_DOMAIN",
        "symbol": "X",
        "timestamp": "2026-07-02T00:00:00+00:00",
        "source": "adapter",
        "price": 1,
        "confidence": 70,
        "lineage": "lineage-002",
    })

    assert report["validation_status"] == "umm_record_valid_with_warnings"
    assert report["warning_count"] == 1
    assert any(issue["code"] == "unsupported_domain" for issue in report["issues"])


def test_batch_validation():
    batch = oracle_universal_market_model_schema_engine.validate_batch([
        {
            "domain": "CRYPTO",
            "symbol": "BTC-USD",
            "source": "crypto_adapter",
            "price": 100,
            "confidence": 90,
            "lineage": "a",
        },
        {
            "domain": "FOREX",
            "symbol": "EURUSD",
            "source": "forex_adapter",
            "price": 1.1,
            "confidence": 84,
            "lineage": "b",
        },
    ])

    assert batch["batch_status"] == "umm_batch_valid"
    assert batch["record_count"] == 2
    assert batch["valid_count"] == 2
    assert batch["invalid_count"] == 0


if __name__ == "__main__":
    test_schema_contract_is_read_only()
    test_normalize_record()
    test_valid_record_passes()
    test_unsupported_domain_warns()
    test_batch_validation()
    print("[PASS] OI-165 Oracle Universal Market Model Schema Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .universal_market_model_schema_engine import oracle_universal_market_model_schema_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-165 INSTALLER")
    print(" Oracle Universal Market Model Schema Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-165 installed")
    print("\nRun:")
    print("py test_oi_165_universal_market_model_schema_engine.py")


if __name__ == "__main__":
    main()