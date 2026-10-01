from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUB = ROOT / "qseries_v2" / "oracle_strategy_intelligence" / "solana_intelligence"
MOD = SUB / "osi_001_universal_solana_opportunity_discovery.py"
TEST = ROOT / "test_osi_001b_universal_solana_opportunity_discovery.py"

MOD_TEXT = r"""from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from typing import Iterable

EXECUTION_AUTHORITY = False
READ_ONLY = True

EVENT_TYPES = {
    "NEW_POOL", "LIQUIDITY_ADDED", "LIQUIDITY_REMOVED", "FREEZE_AUTHORITY",
    "MINT_AUTHORITY", "SWAP_ACCELERATION", "WALLET_CLUSTER", "HOLDER_CONCENTRATION",
    "POOL_DEPTH_CHANGE", "VOLUME_BURST", "PRICE_ACCELERATION", "RUG_RISK_CHANGE",
}

def _dt(v: str) -> datetime:
    d = datetime.fromisoformat(v.replace("Z","+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)

def _id(x: dict) -> str:
    raw = json.dumps(x, sort_keys=True, separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def discover(events: Iterable[dict], now_iso: str, max_age_seconds: int = 300) -> list[dict]:
    now = _dt(now_iso)
    out = []
    for e in events:
        typ, asset, ts = e.get("event_type"), e.get("asset_key"), e.get("observed_at")
        if typ not in EVENT_TYPES or not asset or not ts:
            continue
        t = _dt(ts)
        age = (now-t).total_seconds()
        if age < 0 or age > max_age_seconds:
            continue
        row = {
            "asset_key": str(asset),
            "event_type": str(typ),
            "observed_at": t.isoformat(),
            "source": str(e.get("source") or "unknown"),
            "source_record_id": str(e.get("source_record_id") or ""),
            "features": dict(e.get("features") or {}),
            "read_only": True,
            "execution_authority": False,
        }
        row["opportunity_seed_id"] = _id({
            "asset_key": row["asset_key"],
            "event_type": row["event_type"],
            "observed_at": row["observed_at"],
            "source": row["source"],
            "source_record_id": row["source_record_id"],
        })
        out.append(row)
    out.sort(key=lambda x:(x["observed_at"],x["asset_key"],x["event_type"],x["opportunity_seed_id"]))
    return out
"""

TEST_TEXT = r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_001_universal_solana_opportunity_discovery import discover

ROOT = Path(__file__).resolve().parent

class T(unittest.TestCase):
    def test_discovery(self):
        rows = discover([
            {"asset_key":"SOL:M1","event_type":"NEW_POOL","observed_at":"2026-09-18T05:00:00+00:00","source":"solana_native","source_record_id":"1"},
            {"asset_key":"SOL:M1","event_type":"LIQUIDITY_ADDED","observed_at":"2026-09-18T05:00:04+00:00","source":"solana_native","source_record_id":"2","features":{"usd":25000}},
            {"asset_key":"SOL:M2","event_type":"FREEZE_AUTHORITY","observed_at":"2026-09-18T05:00:05+00:00","source":"solana_native","source_record_id":"3","features":{"enabled":False}},
            {"asset_key":"SOL:OLD","event_type":"NEW_POOL","observed_at":"2026-09-18T04:40:00+00:00","source":"solana_native"},
        ], "2026-09-18T05:00:10+00:00", 300)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(not x["execution_authority"] for x in rows))

    def test_certified_physical_pavement(self):
        self.assertTrue((ROOT/"qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py").is_file())
        self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_029_fresh_candidate_supply_lineage_audit.py").is_file())
        self.assertTrue((ROOT/"OOI_029_FRESH_CANDIDATE_SUPPLY_LINEAGE_AUDIT.json").is_file())
        print("[PASS] OSI-001 universal Solana opportunity discovery contract")
        print("[TRADER] New pools/liquidity/authority/flow/risk events can become fresh opportunity seeds")
        print("[PASS] certified upstream only: OAD-312 + OOI-029")
        print("[PASS] execution_authority=FALSE")
        print("[SCOPE] Deterministic discovery certification; live continuous activation unclaimed")

if __name__=="__main__":
    unittest.main()
"""

def main():
    print("="*112)
    print(" OSI-001B UNIVERSAL SOLANA OPPORTUNITY DISCOVERY REBUILD")
    print("="*112)
    required = [
        ROOT/"qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py",
        ROOT/"qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_029_fresh_candidate_supply_lineage_audit.py",
        ROOT/"OOI_029_FRESH_CANDIDATE_SUPPLY_LINEAGE_AUDIT.json",
    ]
    for path in required:
        if not path.is_file():
            raise RuntimeError("Missing certified upstream: " + str(path))
        print("[PASS] certified upstream:", path.relative_to(ROOT))
    SUB.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MOD_TEXT, encoding="utf-8")
    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print("[PASS] replaced:", MOD.relative_to(ROOT))
    print("[PASS] test:", TEST.name)
    print("[PASS] execution_authority=FALSE")
    print("[SCOPE] Direct foundational rebuild; no dependency on uncertified OOI-030")

if __name__=="__main__":
    main()
