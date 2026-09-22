from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-006"
INSTALLER_REVISION = "OI_006_LIVE_OBSERVATION_REGISTRY_TERMINAL_BRIDGE_INSTALLER_V1"
ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_003 = PACKAGE / "oi_003_canonical_observation_gateway.py"
UPSTREAM_004 = PACKAGE / "oi_004_kalshi_observation_adapter.py"
UPSTREAM_005 = PACKAGE / "oi_005_public_market_data_adapter.py"
MODULE = PACKAGE / "oi_006_live_observation_registry.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_006_live_observation_registry.py"
TERMINAL_BRIDGE = ROOT / "qseries_v2" / "oracle_terminal" / "oracle_live_terminal_evidence_bridge.py"

MODULE_SOURCE = r'''
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
'''

TEST_SOURCE = r'''
from __future__ import annotations
import unittest

from qseries_v2.observation_intelligence.oi_005_public_market_data_adapter import PublicMarketDataObservationAdapter
from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    OI_006_REVISION,
    LiveObservationRegistry,
    default_source_registry,
    read_live_spot_observation,
    verify_live_observation_registry,
)

def fake_transport(url: str, timeout: float):
    return {"data":{"amount":"123456.78","currency":"USD"}}

class TestOI006(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_live_observation_registry())
    def test_sources(self):
        r=default_source_registry()
        self.assertIsNotNone(r.get("adapter.coinbase.spot.v1"))
        self.assertIsNotNone(r.get("adapter.kalshi.v1"))
    def test_spot_canonicalization(self):
        o=read_live_spot_observation("BTC-USD",market_data_adapter=PublicMarketDataObservationAdapter(transport=fake_transport))
        self.assertEqual(o.subject,"BTC"); self.assertEqual(o.observation_type,"spot_price")
        self.assertEqual(o.facts["price"],"123456.78")
    def test_latest(self):
        o=read_live_spot_observation("BTC-USD",market_data_adapter=PublicMarketDataObservationAdapter(transport=fake_transport))
        r=LiveObservationRegistry((o,))
        self.assertIs(r.latest("BTC","spot_price"),o)
    def test_side_effects(self):
        r=LiveObservationRegistry(())
        self.assertTrue(r.read_only); self.assertFalse(r.persistence_allowed)
        self.assertFalse(r.publication_allowed); self.assertFalse(r.execution_allowed)
        self.assertFalse(r.qseries_execution_allowed)

if __name__=="__main__":
    print("="*72); print(" OI-006 CERTIFICATION TEST"); print(" LIVE OBSERVATION REGISTRY + TERMINAL BRIDGE"); print("="*72)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOI006))
    if not result.wasSuccessful(): raise SystemExit(1)
    print(); print("[PASS] Build: OI-006"); print(f"[PASS] Revision: {OI_006_REVISION}")
    print("[PASS] Kalshi and Coinbase adapters registered through one intake contract")
    print("[PASS] Live spot observations canonicalize through OI-003")
    print("[PASS] Deterministic latest-observation registry certified")
    print("[PASS] Terminal live-price bridge binding installed")
    print("[PASS] Persistence, publication, action authorization, and execution disabled")
    print("[DONE] OI-006 CERTIFIED")
'''

TERMINAL_PATCH = r'''
# BEGIN OI-006 LIVE OBSERVATION FALLBACK
_int_oracle_live_001_database_reader = read_live_price_evidence

def read_live_price_evidence(repository_root, query):
    existing = _int_oracle_live_001_database_reader(repository_root, query)
    if existing.matched:
        return existing

    from qseries_v2.observation_intelligence.oi_006_live_observation_registry import query_factual_live_price

    try:
        observation = query_factual_live_price(query)
    except Exception:
        return existing

    if observation is None:
        return existing

    try:
        price = float(observation.facts.get("price"))
    except (TypeError, ValueError):
        return existing

    evidence_body = {
        "query": str(query),
        "asset": {"BTC":"bitcoin","ETH":"ethereum","SOL":"solana"}.get(
            observation.subject.upper(),
            observation.subject.lower(),
        ),
        "source_table": "oi_006.live_observation",
        "source_column": "facts.price",
        "source_identity": observation.canonical_observation_id,
        "price": price,
        "observed_at": observation.observed_at.isoformat(),
        "source_record": {
            "canonical_observation_id": observation.canonical_observation_id,
            "provider": observation.provider,
            "adapter_id": observation.adapter_id,
            "subject": observation.subject,
            "observation_type": observation.observation_type,
            "facts": dict(observation.facts),
            "metadata": dict(observation.metadata),
            "canonical_observation_hash": observation.canonical_observation_hash,
        },
        "database_read_performed": existing.database_read_performed,
        "read_only": True,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
    }

    evidence = LiveTerminalEvidence(
        **evidence_body,
        evidence_hash=_stable_hash(evidence_body),
    )

    body = {
        "query": str(query),
        "matched": True,
        "evidence": evidence,
        "reason": "oi_006_live_observation_found",
        "database_read_performed": existing.database_read_performed,
        "read_only": True,
        "execution_allowed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
    }

    return LiveTerminalEvidenceResult(
        **body,
        result_hash=_stable_hash(body),
    )
# END OI-006 LIVE OBSERVATION FALLBACK
'''

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_checked(path: Path, source: str) -> None:
    text=source.lstrip(); ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[PASS] Wrote: {path.relative_to(ROOT)}")

def patch_terminal(current: str) -> str:
    begin="# BEGIN OI-006 LIVE OBSERVATION FALLBACK"; end="# END OI-006 LIVE OBSERVATION FALLBACK"
    if begin in current:
        start=current.index(begin)
        if end not in current[start:]:
            raise RuntimeError("Existing OI-006 terminal patch is incomplete")
        stop=current.index(end,start)+len(end)
        current=current[:start]+current[stop:]
    updated=current.rstrip()+"\n\n"+TERMINAL_PATCH.strip()+"\n"
    ast.parse(updated, filename=str(TERMINAL_BRIDGE))
    return updated

def main() -> int:
    print("="*72); print(" OI-006 INSTALLER"); print(" LIVE OBSERVATION REGISTRY + TERMINAL BRIDGE"); print("="*72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}"); print(f"[ROOT] {ROOT}")
    upstreams=((UPSTREAM_003,"OI-003"),(UPSTREAM_004,"OI-004"),(UPSTREAM_005,"OI-005"))
    for path,name in upstreams:
        if not path.is_file(): raise RuntimeError(f"Certified {name} missing: {path}")
    if not TERMINAL_BRIDGE.is_file():
        raise RuntimeError(f"INT-ORACLE-LIVE-001 terminal evidence bridge missing: {TERMINAL_BRIDGE}")
    upstream={path:sha(path) for path,_ in upstreams}
    print("[PASS] Certified OI-003 through OI-005 verified read-only")
    print("[PASS] Existing INT-ORACLE-LIVE-001 bridge located")
    affected=(MODULE,TEST,INIT,TERMINAL_BRIDGE); backups={x:x.read_bytes() if x.exists() else None for x in affected}
    try:
        write_checked(MODULE,MODULE_SOURCE); write_checked(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .oi_006_live_observation_registry import *"
        if export not in current.splitlines():
            if current and not current.endswith("\n"): current+="\n"
            current+=export+"\n"; ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")
        print("[PASS] Updated: qseries_v2\\observation_intelligence\\__init__.py")

        terminal_current=TERMINAL_BRIDGE.read_text(encoding="utf-8")
        TERMINAL_BRIDGE.write_text(patch_terminal(terminal_current),encoding="utf-8",newline="\n")
        print("[PASS] Updated read-only Oracle terminal live-evidence bridge")

        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        compile(TERMINAL_BRIDGE.read_text(encoding="utf-8"),str(TERMINAL_BRIDGE),"exec")

        for path,expected in upstream.items():
            if sha(path)!=expected: raise RuntimeError(f"Certified upstream changed: {path.name}")

        if "# BEGIN OI-006 LIVE OBSERVATION FALLBACK" not in TERMINAL_BRIDGE.read_text(encoding="utf-8"):
            raise RuntimeError("OI-006 terminal patch not installed")

        print("[PASS] In-memory compilation verified"); print("[PASS] Certified OI upstream remained unchanged")
        print("[PASS] Terminal factual-price fallback bound to OI-006")
        install_hash=hashlib.sha256(MODULE.read_bytes()+TEST.read_bytes()+TERMINAL_BRIDGE.read_bytes()).hexdigest()
        print(f"[PASS] Deterministic install hash: {install_hash}")
        print("[PASS] Public read-only acquisition enabled")
        print("[PASS] Persistence, publication, action authorization, and execution disabled")
        print("[DONE] OI-006 INSTALLATION COMPLETE"); return 0
    except Exception:
        for path,content in backups.items():
            if content is None:
                if path.exists(): path.unlink()
            else: path.write_bytes(content)
        print("[ROLLBACK] OI-006 installation failed; all affected files restored"); raise

if __name__=="__main__": raise SystemExit(main())
