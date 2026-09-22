from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .oi_002_source_adapter_registry import SourceAdapterDescriptor, SourceAdapterRegistry
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation, CanonicalLiveObservationGateway
from .oi_004_kalshi_observation_adapter import KalshiUniversalObservationAdapter
from .oi_005_public_market_data_adapter import PublicMarketDataObservationAdapter

BUILD_ID = "OI-006"
OI_006_REVISION = "OI_006_LIVE_OBSERVATION_REGISTRY_V1"
READ_ONLY = True
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False

class LiveObservationRegistryError(ValueError):
    pass

@dataclass(frozen=True, slots=True)
class LiveObservationLookup:
    query_key: str
    observation: CanonicalLiveObservation

class LiveObservationRegistry:
    read_only = True
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(self, observations: tuple[CanonicalLiveObservation,...] = ()) -> None:
        values=tuple(observations)
        if any(not isinstance(item,CanonicalLiveObservation) for item in values):
            raise TypeError("all observations must be CanonicalLiveObservation")
        ordered=tuple(sorted(values,key=lambda item:(item.observed_at,item.canonical_observation_id)))
        if values!=ordered:
            raise LiveObservationRegistryError("observations must be deterministically sorted")
        ids=tuple(item.canonical_observation_id for item in values)
        if len(ids)!=len(set(ids)):
            raise LiveObservationRegistryError("duplicate canonical observation id")
        self._observations=values
        latest={}
        for item in values:
            latest[(item.subject.strip().upper(),item.observation_type.strip().lower())]=item
        self._latest=MappingProxyType(latest)

    @property
    def observations(self) -> tuple[CanonicalLiveObservation,...]:
        return self._observations

    def latest(self, subject: str, observation_type: str) -> CanonicalLiveObservation | None:
        return self._latest.get((str(subject).strip().upper(),str(observation_type).strip().lower()))

def default_source_registry() -> SourceAdapterRegistry:
    return SourceAdapterRegistry((
        SourceAdapterDescriptor(
            adapter_id="adapter.coinbase.spot.v1",
            source_id="coinbase.public.spot",
            source_kind="market_data",
            provider="Coinbase",
            adapter_version="1.0.0",
            capabilities=("spot price",),
            enabled_for_intake=True,
        ),
        SourceAdapterDescriptor(
            adapter_id="adapter.kalshi.v1",
            source_id="kalshi.public",
            source_kind="market_venue",
            provider="Kalshi",
            adapter_version="1.0.0",
            capabilities=("market discovery","market snapshot"),
            enabled_for_intake=True,
        ),
    ))

def read_live_spot_observation(
    product_id: str,
    *,
    market_data_adapter: PublicMarketDataObservationAdapter | None = None,
) -> CanonicalLiveObservation:
    adapter=market_data_adapter or PublicMarketDataObservationAdapter()
    envelope=adapter.fetch_spot(product_id)
    return CanonicalLiveObservationGateway(default_source_registry()).canonicalize(envelope).canonical_observation

def read_live_kalshi_observations(
    *,
    limit: int = 100,
    status: str = "open",
    kalshi_adapter: KalshiUniversalObservationAdapter | None = None,
) -> tuple[CanonicalLiveObservation,...]:
    adapter=kalshi_adapter or KalshiUniversalObservationAdapter()
    gateway=CanonicalLiveObservationGateway(default_source_registry())
    values=tuple(gateway.canonicalize(item).canonical_observation for item in adapter.fetch_markets(limit=limit,status=status))
    return tuple(sorted(values,key=lambda item:(item.observed_at,item.canonical_observation_id)))

def query_factual_live_price(query: str) -> CanonicalLiveObservation | None:
    normalized=" ".join(str(query).strip().lower().split())
    price_intent=(
        any(token in normalized for token in ("price","value","trading"))
        and any(token in normalized for token in ("current","latest","live","now"))
    )
    if not price_intent:
        return None
    for names,product_id in (
        (("bitcoin","btc"),"BTC-USD"),
        (("ethereum","eth"),"ETH-USD"),
        (("solana","sol"),"SOL-USD"),
    ):
        if any(name in normalized for name in names):
            return read_live_spot_observation(product_id)
    return None

def verify_live_observation_registry() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-006 must remain read-only")
    if PERSISTENCE_ALLOWED or PUBLICATION_ALLOWED or EXECUTION_ALLOWED or QSERIES_EXECUTION_ALLOWED:
        raise AssertionError("OI-006 forbidden capability enabled")
    return True
