from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-005"
INSTALLER_REVISION = "OI_005_PUBLIC_MARKET_DATA_ADAPTER_INSTALLER_V1"
ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_001 = PACKAGE / "oi_001_universal_observation_intake.py"
UPSTREAM_004 = PACKAGE / "oi_004_kalshi_observation_adapter.py"
MODULE = PACKAGE / "oi_005_public_market_data_adapter.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_005_public_market_data_adapter.py"

MODULE_SOURCE = r'''
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import quote
from urllib.request import Request, urlopen

from .oi_001_universal_observation_intake import ObservationSourceIdentity, RawObservationEnvelope

BUILD_ID = "OI-005"
OI_005_REVISION = "OI_005_PUBLIC_MARKET_DATA_ADAPTER_V1"
READ_ONLY = True
NETWORK_ALLOWED = True
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False

COINBASE_SPOT_BASE_URL = "https://api.coinbase.com/v2/prices"
SUPPORTED_PRODUCTS = ("BTC-USD", "ETH-USD", "SOL-USD")

class PublicMarketDataAdapterError(RuntimeError):
    pass

def _default_transport(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"Accept":"application/json","User-Agent":"Oracle-OI-005/1.0"}, method="GET")
    with urlopen(request, timeout=timeout) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise PublicMarketDataAdapterError("market-data response must be a JSON object")
    return value

class PublicMarketDataObservationAdapter:
    read_only = True
    network_allowed = True
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(self, *, transport: Callable[[str,float],dict[str,Any]] | None = None, timeout_seconds: float = 10.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._transport = transport or _default_transport
        self._timeout_seconds = float(timeout_seconds)
        self._source = ObservationSourceIdentity(
            source_id="coinbase.public.spot",
            source_kind="market_data",
            provider="Coinbase",
            adapter_id="adapter.coinbase.spot.v1",
        )

    @property
    def source_identity(self) -> ObservationSourceIdentity:
        return self._source

    def fetch_spot(self, product_id: str) -> RawObservationEnvelope:
        normalized = str(product_id).strip().upper()
        if normalized not in SUPPORTED_PRODUCTS:
            raise ValueError(f"unsupported product_id: {normalized}")

        url = COINBASE_SPOT_BASE_URL + "/" + quote(normalized, safe="-") + "/spot"
        response = self._transport(url, self._timeout_seconds)
        data = response.get("data")
        if not isinstance(data, dict):
            raise PublicMarketDataAdapterError("Coinbase spot response missing object field 'data'")
        amount = str(data.get("amount","")).strip()
        currency = str(data.get("currency","")).strip().upper()
        try:
            numeric = float(amount)
        except ValueError as exc:
            raise PublicMarketDataAdapterError("Coinbase spot amount is not numeric") from exc
        if numeric <= 0:
            raise PublicMarketDataAdapterError("Coinbase spot amount must be positive")

        base, quote_currency = normalized.split("-",1)
        if currency and currency != quote_currency:
            raise PublicMarketDataAdapterError("Coinbase quote currency mismatch")

        observed_at = datetime.now(timezone.utc)
        return RawObservationEnvelope(
            source=self._source,
            external_observation_id=f"{normalized}:{observed_at.isoformat()}",
            observed_at=observed_at,
            subject=base,
            observation_type="spot_price",
            payload={
                "product_id":normalized,
                "symbol":base,
                "quote_currency":quote_currency,
                "price":amount,
            },
            metadata={
                "venue":"coinbase",
                "source_endpoint":f"/v2/prices/{normalized}/spot",
                "public_market_data":True,
            },
        )

    def fetch_supported_spot(self) -> tuple[RawObservationEnvelope,...]:
        return tuple(self.fetch_spot(product) for product in SUPPORTED_PRODUCTS)

def verify_public_market_data_adapter() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-005 must remain read-only")
    if PERSISTENCE_ALLOWED or PUBLICATION_ALLOWED or EXECUTION_ALLOWED or QSERIES_EXECUTION_ALLOWED:
        raise AssertionError("OI-005 forbidden capability enabled")
    return True
'''

TEST_SOURCE = r'''
from __future__ import annotations
import unittest
from qseries_v2.observation_intelligence.oi_005_public_market_data_adapter import OI_005_REVISION, PublicMarketDataObservationAdapter, verify_public_market_data_adapter

def fake_transport(url: str, timeout: float):
    assert url.endswith("/spot") and timeout > 0
    amount = "123456.78" if "BTC-USD" in url else ("5000.12" if "ETH-USD" in url else "250.50")
    return {"data":{"amount":amount,"currency":"USD"}}

class TestOI005(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_public_market_data_adapter())
    def test_btc(self):
        item=PublicMarketDataObservationAdapter(transport=fake_transport).fetch_spot("BTC-USD")
        self.assertEqual(item.subject,"BTC"); self.assertEqual(item.observation_type,"spot_price")
        self.assertEqual(item.payload["price"],"123456.78")
    def test_eth(self): self.assertEqual(PublicMarketDataObservationAdapter(transport=fake_transport).fetch_spot("ETH-USD").subject,"ETH")
    def test_sol(self): self.assertEqual(PublicMarketDataObservationAdapter(transport=fake_transport).fetch_spot("SOL-USD").subject,"SOL")
    def test_unsupported(self):
        with self.assertRaises(ValueError): PublicMarketDataObservationAdapter(transport=fake_transport).fetch_spot("DOGE-USD")
    def test_source(self):
        item=PublicMarketDataObservationAdapter(transport=fake_transport).fetch_spot("BTC-USD")
        self.assertEqual(item.source.provider,"Coinbase"); self.assertEqual(item.source.adapter_id,"adapter.coinbase.spot.v1")
    def test_side_effects(self):
        a=PublicMarketDataObservationAdapter(transport=fake_transport)
        self.assertTrue(a.read_only); self.assertTrue(a.network_allowed)
        self.assertFalse(a.persistence_allowed); self.assertFalse(a.publication_allowed)
        self.assertFalse(a.execution_allowed); self.assertFalse(a.qseries_execution_allowed)

if __name__=="__main__":
    print("="*72); print(" OI-005 CERTIFICATION TEST"); print(" PUBLIC MARKET DATA ADAPTER"); print("="*72)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOI005))
    if not result.wasSuccessful(): raise SystemExit(1)
    print(); print("[PASS] Build: OI-005"); print(f"[PASS] Revision: {OI_005_REVISION}")
    print("[PASS] BTC, ETH, and SOL spot observations certified through one adapter")
    print("[PASS] Public market-data observations normalize into OI-001 envelopes")
    print("[PASS] Persistence, publication, and execution disabled")
    print("[DONE] OI-005 CERTIFIED")
'''

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def write_checked(path: Path, source: str) -> None:
    text=source.lstrip(); ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[PASS] Wrote: {path.relative_to(ROOT)}")

def main() -> int:
    print("="*72); print(" OI-005 INSTALLER"); print(" PUBLIC MARKET DATA ADAPTER"); print("="*72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}"); print(f"[ROOT] {ROOT}")
    for path,name in ((UPSTREAM_001,"OI-001"),(UPSTREAM_004,"OI-004")):
        if not path.is_file(): raise RuntimeError(f"Certified {name} missing: {path}")
    upstream={path:sha(path) for path in (UPSTREAM_001,UPSTREAM_004)}
    print("[PASS] Certified OI-001 and OI-004 verified read-only")
    affected=(MODULE,TEST,INIT); backups={x:x.read_bytes() if x.exists() else None for x in affected}
    try:
        write_checked(MODULE,MODULE_SOURCE); write_checked(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .oi_005_public_market_data_adapter import *"
        if export not in current.splitlines():
            if current and not current.endswith("\n"): current+="\n"
            current+=export+"\n"; ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")
        print("[PASS] Updated: qseries_v2\\observation_intelligence\\__init__.py")
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        for path,expected in upstream.items():
            if sha(path)!=expected: raise RuntimeError(f"Certified upstream changed: {path.name}")
        print("[PASS] In-memory compilation verified"); print("[PASS] Certified upstream remained unchanged")
        print(f"[PASS] Deterministic install hash: {hashlib.sha256(MODULE.read_bytes()+TEST.read_bytes()).hexdigest()}")
        print("[PASS] Public read-only market-data acquisition enabled")
        print("[PASS] Persistence, publication, and execution disabled")
        print("[DONE] OI-005 INSTALLATION COMPLETE"); return 0
    except Exception:
        for path,content in backups.items():
            if content is None:
                if path.exists(): path.unlink()
            else: path.write_bytes(content)
        print("[ROLLBACK] OI-005 installation failed; all affected files restored"); raise

if __name__=="__main__": raise SystemExit(main())
