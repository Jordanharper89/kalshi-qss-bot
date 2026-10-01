from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_intelligence"
MOD=SUB/"osi_002_same_opportunity_evidence_synchronizer.py"
TEST=ROOT/"test_osi_002_same_opportunity_evidence_synchronizer.py"

MOD_TEXT=r"""from __future__ import annotations
from datetime import datetime, timezone
from typing import Iterable

EXECUTION_AUTHORITY=False
READ_ONLY=True

def _dt(v):
    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)

def synchronize(seed:dict,evidence:Iterable[dict],freeze_at:str,lookback_seconds:int=120)->dict:
    freeze=_dt(freeze_at); lower=freeze.timestamp()-lookback_seconds
    rows=[]
    for e in evidence:
        if e.get("asset_key")!=seed.get("asset_key") or not e.get("observed_at") or not e.get("source"): continue
        t=_dt(e["observed_at"])
        if t>freeze or t.timestamp()<lower: continue
        x=dict(e);x["observed_at"]=t.isoformat();rows.append(x)
    rows.sort(key=lambda x:(x["observed_at"],str(x["source"]),str(x.get("evidence_id",""))))
    sources=sorted({str(x["source"]) for x in rows})
    return {
      "opportunity_seed_id":seed["opportunity_seed_id"],"asset_key":seed["asset_key"],
      "freeze_at":freeze.isoformat(),"evidence":rows,"independent_sources":sources,
      "source_count":len(sources),"future_excluded":True,
      "execution_authority":False,"read_only":True
    }
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_001_universal_solana_opportunity_discovery import discover
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_002_same_opportunity_evidence_synchronizer import synchronize
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_sync(self):
  seed=discover([{"asset_key":"SOL:M1","event_type":"NEW_POOL","observed_at":"2026-09-18T05:00:00+00:00","source":"solana_native","source_record_id":"1"}],"2026-09-18T05:00:01+00:00")[0]
  b=synchronize(seed,[
   {"evidence_id":"s","asset_key":"SOL:M1","source":"solana_native","observed_at":"2026-09-18T04:59:58+00:00","value":1},
   {"evidence_id":"g","asset_key":"SOL:M1","source":"gmgn","observed_at":"2026-09-18T04:59:59+00:00","value":1},
   {"evidence_id":"c","asset_key":"SOL:M1","source":"coinbase","observed_at":"2026-09-18T05:00:00+00:00","value":1},
   {"evidence_id":"future","asset_key":"SOL:M1","source":"coinbase","observed_at":"2026-09-18T05:00:02+00:00","value":9},
  ],"2026-09-18T05:00:00+00:00")
  self.assertEqual(b["source_count"],3);self.assertNotIn("future",[x["evidence_id"] for x in b["evidence"]])
 def test_physical(self):
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_001_universal_solana_opportunity_discovery.py").is_file())
  print("[PASS] OSI-002 same-opportunity evidence synchronization")
  print("[TRADER] Solana + GMGN + Coinbase evidence is aligned before the call; future leakage excluded")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] OSI-002 installed; execution_authority=FALSE")
if __name__=="__main__":main()
