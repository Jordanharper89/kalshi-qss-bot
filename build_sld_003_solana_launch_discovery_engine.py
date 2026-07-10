from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "solana_launch_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

ENGINE_FILE = MODULE_DIR / "solana_launch_discovery_engine.py"
TEST_FILE = ROOT / "test_sld_003_solana_launch_discovery_engine.py"
INIT_FILE = MODULE_DIR / "__init__.py"

ENGINE_CODE = r'''"""
SLD-003 Solana Launch Discovery Engine

Read-only Oracle discovery engine for Solana token launch opportunities.

Consumes SLD-002 SolanaLaunchSnapshot records and emits immutable
UniversalOpportunity-shaped Solana launch opportunities.

No signing, fund movement, swaps, sniping, routing, buying, selling, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .solana_launch_discovery_contract import (
    SCHEMA_VERSION as CONTRACT_SCHEMA_VERSION,
    SolanaLaunchDiscoveryCapability,
    SolanaLaunchDiscoveryEngineContract,
    SolanaLaunchDiscoveryFamily,
    SolanaLaunchDiscoveryHealth,
    SolanaLaunchDiscoveryRequest,
    SolanaLaunchDiscoveryResult,
    SolanaLaunchDiscoveryTelemetry,
)
from .solana_launch_source_adapter import SolanaLaunchSnapshot, SolanaLaunchSourceAdapter


SCHEMA_VERSION = "SLD-003"
ENGINE_ID = "oracle.discovery.solana_launch"
ENGINE_NAME = "Solana Launch Discovery Engine"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return "{" + ",".join(
            f"{str(k)}:{_stable_text(v)}"
            for k, v in sorted(value.items(), key=lambda x: str(x[0]))
        ) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = sha256(_stable_text(payload).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}.{digest}"


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class SolanaLaunchOpportunity:
    opportunity_id: str
    schema_version: str
    mint: str
    symbol: str
    opportunity_type: str
    source_engine_id: str
    launch_score: float
    safety_score: float
    liquidity_score: float
    momentum_score: float
    confidence: float
    liquidity_usd: float
    age_seconds: float
    universal_market: Mapping[str, Any]
    status: str
    explanation: Mapping[str, Any]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "schema_version": self.schema_version,
            "mint": self.mint,
            "symbol": self.symbol,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "launch_score": self.launch_score,
            "safety_score": self.safety_score,
            "liquidity_score": self.liquidity_score,
            "momentum_score": self.momentum_score,
            "confidence": self.confidence,
            "liquidity_usd": self.liquidity_usd,
            "age_seconds": self.age_seconds,
            "universal_market": dict(self.universal_market),
            "status": self.status,
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class SolanaLaunchDiscoveryEngine(SolanaLaunchDiscoveryEngineContract):
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    engine_name = ENGINE_NAME
    read_only = True

    def __init__(
        self,
        source_snapshots: Optional[Sequence[SolanaLaunchSnapshot]] = None,
        min_liquidity_usd: float = 1000.0,
        max_age_seconds: float = 600.0,
        min_launch_score: float = 0.55,
    ) -> None:
        self.source_snapshots = tuple(source_snapshots or ())
        self.min_liquidity_usd = float(min_liquidity_usd)
        self.max_age_seconds = float(max_age_seconds)
        self.min_launch_score = float(min_launch_score)

    def capabilities(self) -> SolanaLaunchDiscoveryCapability:
        return SolanaLaunchDiscoveryCapability(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=SolanaLaunchDiscoveryFamily.NEW_TOKEN_LAUNCH,
            source_name="solana_launch_snapshot",
            supports_replay=True,
            deterministic=True,
            telemetry=True,
            read_only=True,
            metadata={
                "engine_schema_version": self.schema_version,
                "engine_name": self.engine_name,
                "produces": "UniversalOpportunity-shaped Solana launch opportunities",
                "execution": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
                "snipe_allowed": False,
            },
        )

    def health(self) -> SolanaLaunchDiscoveryHealth:
        return SolanaLaunchDiscoveryHealth(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={
                "engine_schema_version": self.schema_version,
                "read_only": True,
                "execution": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
            },
        )

    def discover(self, request: SolanaLaunchDiscoveryRequest | None = None) -> SolanaLaunchDiscoveryResult:
        started_at = _utc_now_iso()
        snapshots = self._resolve_snapshots(request)

        opportunities = []
        rejected = 0

        for snapshot in snapshots:
            opportunity = self._build_opportunity(snapshot)
            if opportunity is None:
                rejected += 1
                continue
            opportunities.append(opportunity)

        opportunities = tuple(
            sorted(
                opportunities,
                key=lambda o: (-o.launch_score, -o.confidence, o.age_seconds, o.symbol, o.mint),
            )
        )

        request_id = request.request_id if request is not None else "solana.launch.discovery.default"

        telemetry = SolanaLaunchDiscoveryTelemetry(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=len(snapshots),
            launches_seen=len({s.mint for s in snapshots}),
            opportunities_emitted=len(opportunities),
            rejected_records=rejected,
            metadata={
                "engine_schema_version": self.schema_version,
                "min_liquidity_usd": self.min_liquidity_usd,
                "max_age_seconds": self.max_age_seconds,
                "min_launch_score": self.min_launch_score,
                "deterministic_sort": True,
                "read_only": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
                "snipe_allowed": False,
            },
            read_only=True,
        )

        return SolanaLaunchDiscoveryResult(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request_id,
            status="passed" if opportunities else "empty",
            opportunities=opportunities,
            telemetry=telemetry,
            health=self.health(),
            read_only=True,
        )

    def _resolve_snapshots(
        self,
        request: SolanaLaunchDiscoveryRequest | None,
    ) -> Tuple[SolanaLaunchSnapshot, ...]:
        if request is None:
            return tuple(self.source_snapshots)

        metadata = request.metadata or {}
        records = None
        for key in ("snapshots", "launch_snapshots", "solana_launches", "records", "raw_records"):
            if key in metadata:
                records = metadata[key]
                break

        if records is None:
            return tuple(self.source_snapshots)

        record_tuple = tuple(records)
        if all(isinstance(record, SolanaLaunchSnapshot) for record in record_tuple):
            return record_tuple

        adapter = SolanaLaunchSourceAdapter(source_name=request.source_name)
        return adapter.normalize_batch(record_tuple).snapshots

    def _to_universal_market(self, snapshot: SolanaLaunchSnapshot) -> Mapping[str, Any]:
        payload = {
            "schema_family": "UMM",
            "market_type": "solana_launch",
            "chain": "solana",
            "mint": snapshot.mint,
            "symbol": snapshot.symbol,
            "name": snapshot.name,
            "pool_address": snapshot.pool_address,
            "dex": snapshot.dex,
            "quote_asset": snapshot.quote_asset,
            "liquidity_usd": snapshot.liquidity_usd,
            "market_cap_usd": snapshot.market_cap_usd,
            "volume_5m_usd": snapshot.volume_5m_usd,
            "holder_count": snapshot.holder_count,
            "age_seconds": snapshot.age_seconds,
            "mint_authority_disabled": snapshot.mint_authority_disabled,
            "freeze_authority_disabled": snapshot.freeze_authority_disabled,
            "lp_burned": snapshot.lp_burned,
            "pool_status": snapshot.pool_status,
            "read_only": True,
            "execution_allowed": False,
            "signing_allowed": False,
            "fund_movement_allowed": False,
            "swap_allowed": False,
            "snipe_allowed": False,
        }
        return _freeze(payload)

    def _score_safety(self, snapshot: SolanaLaunchSnapshot) -> float:
        score = 0.0
        if snapshot.mint_authority_disabled:
            score += 0.35
        if snapshot.freeze_authority_disabled:
            score += 0.25
        if snapshot.lp_burned:
            score += 0.25
        if snapshot.pool_status in {"active", "open", "trading"}:
            score += 0.15
        return round(min(1.0, score), 6)

    def _score_liquidity(self, snapshot: SolanaLaunchSnapshot) -> float:
        return round(min(snapshot.liquidity_usd, 100_000.0) / 100_000.0, 6)

    def _score_momentum(self, snapshot: SolanaLaunchSnapshot) -> float:
        volume_score = min(snapshot.volume_5m_usd, 50_000.0) / 50_000.0
        holder_score = min(snapshot.holder_count, 500) / 500.0
        age_score = max(0.0, 1.0 - min(snapshot.age_seconds, self.max_age_seconds) / self.max_age_seconds)
        return round(volume_score * 0.45 + holder_score * 0.25 + age_score * 0.30, 6)

    def _build_opportunity(self, snapshot: SolanaLaunchSnapshot) -> Optional[SolanaLaunchOpportunity]:
        if not snapshot.mint or not snapshot.pool_address:
            return None

        if snapshot.pool_status not in {"active", "open", "trading"}:
            return None

        if snapshot.liquidity_usd < self.min_liquidity_usd:
            return None

        if snapshot.age_seconds > self.max_age_seconds:
            return None

        safety_score = self._score_safety(snapshot)
        liquidity_score = self._score_liquidity(snapshot)
        momentum_score = self._score_momentum(snapshot)
        launch_score = round(safety_score * 0.45 + liquidity_score * 0.25 + momentum_score * 0.30, 6)

        if launch_score < self.min_launch_score:
            return None

        confidence = round(min(1.0, launch_score * 0.75 + safety_score * 0.25), 6)

        identity_payload = {
            "mint": snapshot.mint,
            "pool_address": snapshot.pool_address,
            "symbol": snapshot.symbol,
            "dex": snapshot.dex,
            "launch_score": launch_score,
        }

        explanation = MappingProxyType(
            {
                "summary": "Solana launch passed read-only safety, liquidity, and freshness guardrails.",
                "mint": snapshot.mint,
                "symbol": snapshot.symbol,
                "pool_address": snapshot.pool_address,
                "dex": snapshot.dex,
                "launch_score": launch_score,
                "safety_score": safety_score,
                "liquidity_score": liquidity_score,
                "momentum_score": momentum_score,
                "liquidity_usd": snapshot.liquidity_usd,
                "age_seconds": snapshot.age_seconds,
                "rules": [
                    "read_only_scan",
                    "minimum_liquidity_guardrail",
                    "maximum_age_guardrail",
                    "mint_authority_safety_signal",
                    "freeze_authority_safety_signal",
                    "lp_burn_safety_signal",
                    "deterministic_opportunity_id",
                    "no_signing_authority",
                    "no_fund_movement_authority",
                    "no_swap_authority",
                    "no_execution_authority",
                ],
            }
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "source_engine_id": self.engine_id,
                "mint": snapshot.mint,
                "symbol": snapshot.symbol,
                "pool_address": snapshot.pool_address,
                "created_at": _utc_now_iso(),
                "read_only": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
                "snipe_allowed": False,
            }
        )

        return SolanaLaunchOpportunity(
            opportunity_id=_stable_id("uop.solana_launch", identity_payload),
            schema_version="UOM-compatible/SLD-003",
            mint=snapshot.mint,
            symbol=snapshot.symbol,
            opportunity_type="solana_launch_signal",
            source_engine_id=self.engine_id,
            launch_score=launch_score,
            safety_score=safety_score,
            liquidity_score=liquidity_score,
            momentum_score=momentum_score,
            confidence=confidence,
            liquidity_usd=snapshot.liquidity_usd,
            age_seconds=snapshot.age_seconds,
            universal_market=self._to_universal_market(snapshot),
            status="discovered",
            explanation=explanation,
            telemetry=telemetry,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ENGINE_NAME",
    "SolanaLaunchOpportunity",
    "SolanaLaunchDiscoveryEngine",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.solana_launch_discovery_model.solana_launch_discovery_contract import (
    SolanaLaunchDiscoveryFamily,
    SolanaLaunchDiscoveryRequest,
)
from qseries_v2.oracle_intelligence.solana_launch_discovery_model.solana_launch_discovery_engine import (
    SolanaLaunchDiscoveryEngine,
)


def test_sld_003_solana_launch_discovery_engine():
    raw_records = [
        {
            "token_mint": "mint_a",
            "ticker": "ALPHA",
            "name": "Alpha Token",
            "pool_address": "pool_a",
            "dex": "raydium",
            "quote_asset": "SOL",
            "liquidity_usd": 50000,
            "market_cap_usd": 200000,
            "volume_5m_usd": 15000,
            "holder_count": 250,
            "age_seconds": 30,
            "mint_authority_disabled": True,
            "freeze_authority_disabled": True,
            "lp_burned": True,
            "pool_status": "active",
            "deployer_wallet": "wallet_a",
            "tx_signature": "tx_a",
            "detected_at": "2026-01-01T00:01:00Z",
        },
        {
            "mint": "mint_b",
            "symbol": "BETA",
            "name": "Beta Token",
            "pool": "pool_b",
            "dex": "Raydium",
            "quote": "SOL",
            "liquidity": 25000,
            "market_cap": 120000,
            "volume_5m": 8000,
            "holders": 120,
            "age": 90,
            "mint_disabled": True,
            "freeze_disabled": True,
            "liquidity_burned": True,
            "status": "active",
            "creator": "wallet_b",
            "signature": "tx_b",
            "timestamp": "2026-01-01T00:02:00Z",
        },
        {
            "mint": "mint_bad",
            "symbol": "BAD",
            "pool": "pool_bad",
            "liquidity": 100,
            "age": 900,
            "mint_disabled": False,
            "freeze_disabled": False,
            "liquidity_burned": False,
            "status": "active",
        },
    ]

    request = SolanaLaunchDiscoveryRequest(
        request_id="sld003.test.request",
        family=SolanaLaunchDiscoveryFamily.NEW_TOKEN_LAUNCH,
        source_name="sld_003_test_feed",
        mints=("mint_a", "mint_b", "mint_bad"),
        pools=("pool_a", "pool_b", "pool_bad"),
        metadata={"raw_records": raw_records},
    )

    engine = SolanaLaunchDiscoveryEngine(
        min_liquidity_usd=1000,
        max_age_seconds=600,
        min_launch_score=0.55,
    )

    caps = engine.capabilities()
    health = engine.health()
    report_1 = engine.discover(request)
    report_2 = engine.discover(request)

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.telemetry is True
    assert caps.metadata["signing_allowed"] is False
    assert caps.metadata["fund_movement_allowed"] is False
    assert caps.metadata["swap_allowed"] is False
    assert caps.metadata["snipe_allowed"] is False
    assert health.status == "ok"
    assert health.read_only is True

    assert report_1.schema_version == "SLD-001"
    assert report_1.engine_id == "oracle.discovery.solana_launch"
    assert report_1.status == "passed"
    assert report_1.read_only is True
    assert len(report_1.opportunities) == 2

    ids_1 = [o.opportunity_id for o in report_1.opportunities]
    ids_2 = [o.opportunity_id for o in report_2.opportunities]
    assert ids_1 == ids_2

    first = report_1.opportunities[0]
    assert first.read_only is True
    assert first.opportunity_type == "solana_launch_signal"
    assert first.source_engine_id == "oracle.discovery.solana_launch"
    assert first.launch_score >= 0.55
    assert 0.0 <= first.confidence <= 1.0
    assert first.liquidity_usd >= 1000
    assert first.age_seconds <= 600
    assert first.status == "discovered"
    assert first.universal_market["market_type"] == "solana_launch"
    assert first.universal_market["read_only"] is True
    assert first.universal_market["execution_allowed"] is False
    assert first.universal_market["signing_allowed"] is False
    assert first.universal_market["fund_movement_allowed"] is False
    assert first.universal_market["swap_allowed"] is False
    assert first.universal_market["snipe_allowed"] is False
    assert first.explanation["rules"]

    try:
        first.universal_market["execution_allowed"] = True
        raise AssertionError("universal_market should be immutable")
    except TypeError:
        pass

    d = report_1.to_dict()
    assert d["read_only"] is True
    assert d["telemetry"]["records_seen"] == 3
    assert d["telemetry"]["launches_seen"] == 3
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["rejected_records"] == 1
    assert d["telemetry"]["read_only"] is True

    print("[PASS] SLD-003 Solana Launch Discovery Engine")
    print(
        {
            "schema_version": "SLD-003",
            "engine_id": d["engine_id"],
            "status": d["status"],
            "opportunities": len(d["opportunities"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_sld_003_solana_launch_discovery_engine()
'''

INIT_EXPORT = '''
try:
    from .solana_launch_discovery_engine import (
        SolanaLaunchDiscoveryEngine,
        SolanaLaunchOpportunity,
    )
except Exception:
    pass
'''

ENGINE_FILE.write_text(ENGINE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "SolanaLaunchDiscoveryEngine" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" SLD-003 INSTALLER")
print(" Solana Launch Discovery Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] SLD-003 installed")
print()
print("Run:")
print("py test_sld_003_solana_launch_discovery_engine.py")