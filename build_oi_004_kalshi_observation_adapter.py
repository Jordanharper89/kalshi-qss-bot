from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-004"
INSTALLER_REVISION = "OI_004_KALSHI_UNIVERSAL_OBSERVATION_ADAPTER_INSTALLER_V1"
ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_001 = PACKAGE / "oi_001_universal_observation_intake.py"
UPSTREAM_003 = PACKAGE / "oi_003_canonical_observation_gateway.py"
MODULE = PACKAGE / "oi_004_kalshi_observation_adapter.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_004_kalshi_observation_adapter.py"

MODULE_SOURCE = r'''
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .oi_001_universal_observation_intake import ObservationSourceIdentity, RawObservationEnvelope

BUILD_ID = "OI-004"
OI_004_REVISION = "OI_004_KALSHI_UNIVERSAL_OBSERVATION_ADAPTER_V1"
READ_ONLY = True
NETWORK_ALLOWED = True
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
KALSHI_BASE_URL = "https://external-api.kalshi.com/trade-api/v2"

class KalshiObservationAdapterError(RuntimeError):
    pass

def _default_transport(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "Oracle-OI-004/1.0"}, method="GET")
    with urlopen(request, timeout=timeout) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise KalshiObservationAdapterError("Kalshi response must be a JSON object")
    return value

class KalshiUniversalObservationAdapter:
    read_only = True
    network_allowed = True
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(self, *, transport: Callable[[str, float], dict[str, Any]] | None = None, timeout_seconds: float = 10.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._transport = transport or _default_transport
        self._timeout_seconds = float(timeout_seconds)
        self._source = ObservationSourceIdentity(
            source_id="kalshi.public",
            source_kind="market_venue",
            provider="Kalshi",
            adapter_id="adapter.kalshi.v1",
        )

    @property
    def source_identity(self) -> ObservationSourceIdentity:
        return self._source

    def fetch_markets(self, *, limit: int = 100, status: str = "open", cursor: str | None = None) -> tuple[RawObservationEnvelope, ...]:
        if not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("limit must be an integer from 1 through 1000")
        normalized_status = str(status).strip().lower()
        if normalized_status not in {"unopened", "open", "closed", "settled"}:
            raise ValueError("unsupported Kalshi market status")
        params: dict[str, Any] = {"limit": limit, "status": normalized_status}
        if cursor:
            params["cursor"] = str(cursor).strip()
        response = self._transport(KALSHI_BASE_URL + "/markets?" + urlencode(params), self._timeout_seconds)
        markets = response.get("markets", ())
        if not isinstance(markets, list):
            raise KalshiObservationAdapterError("Kalshi markets response missing list field 'markets'")
        observed_at = datetime.now(timezone.utc)
        envelopes = []
        for market in markets:
            if not isinstance(market, dict):
                raise KalshiObservationAdapterError("Kalshi market item must be an object")
            ticker = str(market.get("ticker", "")).strip()
            title = str(market.get("title") or market.get("subtitle") or ticker).strip()
            if not ticker or not title:
                raise KalshiObservationAdapterError("Kalshi market requires ticker and title")
            envelopes.append(
                RawObservationEnvelope(
                    source=self._source,
                    external_observation_id=f"{ticker}:{observed_at.isoformat()}",
                    observed_at=observed_at,
                    subject=title,
                    observation_type="market_snapshot",
                    payload=dict(market),
                    metadata={
                        "venue": "kalshi",
                        "market_ticker": ticker,
                        "market_status": normalized_status,
                        "source_endpoint": "/markets",
                    },
                )
            )
        return tuple(sorted(envelopes, key=lambda item: (str(item.metadata.get("market_ticker", "")), item.external_observation_id)))

def verify_kalshi_observation_adapter() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-004 must remain read-only")
    if PERSISTENCE_ALLOWED or PUBLICATION_ALLOWED or EXECUTION_ALLOWED or QSERIES_EXECUTION_ALLOWED:
        raise AssertionError("OI-004 forbidden capability enabled")
    return True
'''

TEST_SOURCE = r'''
from __future__ import annotations
import unittest
from qseries_v2.observation_intelligence.oi_004_kalshi_observation_adapter import OI_004_REVISION, KalshiUniversalObservationAdapter, verify_kalshi_observation_adapter

def fake_transport(url: str, timeout: float):
    assert "/markets?" in url and timeout > 0
    return {"markets": [
        {"ticker":"KXBTC-TEST","title":"Will Bitcoin be above $100,000?","status":"open","yes_bid":54,"yes_ask":56,"volume":1000},
        {"ticker":"KXCPI-TEST","title":"Will CPI exceed 3 percent?","status":"open","yes_bid":42,"yes_ask":44,"volume":500},
    ], "cursor":""}

class TestOI004(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_kalshi_observation_adapter())
    def test_all_categories_share_adapter(self):
        values = KalshiUniversalObservationAdapter(transport=fake_transport).fetch_markets()
        self.assertEqual(len(values), 2)
        self.assertEqual({item.metadata["market_ticker"] for item in values}, {"KXBTC-TEST","KXCPI-TEST"})
    def test_source(self):
        item = KalshiUniversalObservationAdapter(transport=fake_transport).fetch_markets()[0]
        self.assertEqual(item.source.adapter_id, "adapter.kalshi.v1")
    def test_payload(self):
        item = KalshiUniversalObservationAdapter(transport=fake_transport).fetch_markets()[0]
        self.assertIn("yes_bid", item.payload)
    def test_bad_status(self):
        with self.assertRaises(ValueError):
            KalshiUniversalObservationAdapter(transport=fake_transport).fetch_markets(status="bad")
    def test_side_effects(self):
        a = KalshiUniversalObservationAdapter(transport=fake_transport)
        self.assertTrue(a.read_only); self.assertTrue(a.network_allowed)
        self.assertFalse(a.persistence_allowed); self.assertFalse(a.publication_allowed)
        self.assertFalse(a.execution_allowed); self.assertFalse(a.qseries_execution_allowed)

if __name__ == "__main__":
    print("="*72); print(" OI-004 CERTIFICATION TEST"); print(" KALSHI UNIVERSAL OBSERVATION ADAPTER"); print("="*72)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOI004))
    if not result.wasSuccessful(): raise SystemExit(1)
    print(); print("[PASS] Build: OI-004"); print(f"[PASS] Revision: {OI_004_REVISION}")
    print("[PASS] One Kalshi adapter supports markets across categories")
    print("[PASS] Public market snapshots normalize into OI-001 envelopes")
    print("[PASS] Persistence, publication, and execution disabled")
    print("[DONE] OI-004 CERTIFIED")
'''

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_checked(path: Path, source: str) -> None:
    text=source.lstrip(); ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[PASS] Wrote: {path.relative_to(ROOT)}")

def main() -> int:
    print("="*72); print(" OI-004 INSTALLER"); print(" KALSHI UNIVERSAL OBSERVATION ADAPTER"); print("="*72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}"); print(f"[ROOT] {ROOT}")
    for path,name in ((UPSTREAM_001,"OI-001"),(UPSTREAM_003,"OI-003")):
        if not path.is_file(): raise RuntimeError(f"Certified {name} missing: {path}")
    upstream={path:sha(path) for path in (UPSTREAM_001,UPSTREAM_003)}
    print("[PASS] Certified OI-001 and OI-003 verified read-only")
    affected=(MODULE,TEST,INIT); backups={x:x.read_bytes() if x.exists() else None for x in affected}
    try:
        write_checked(MODULE,MODULE_SOURCE); write_checked(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .oi_004_kalshi_observation_adapter import *"
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
        print("[PASS] Read-only public acquisition only; persistence/publication/execution disabled")
        print("[DONE] OI-004 INSTALLATION COMPLETE"); return 0
    except Exception:
        for path,content in backups.items():
            if content is None:
                if path.exists(): path.unlink()
            else: path.write_bytes(content)
        print("[ROLLBACK] OI-004 installation failed; all affected files restored"); raise

if __name__=="__main__": raise SystemExit(main())
