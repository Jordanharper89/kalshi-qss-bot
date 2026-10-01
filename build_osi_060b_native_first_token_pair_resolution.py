from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_060_live_token_pair_resolution_audit.py"
TEST=ROOT/"test_osi_060b_native_first_token_pair_resolution.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history

def _pair(record):
 payload=getattr(record,"payload",{}) or {}
 pools=payload.get("pools") or []
 for p in pools:
  if not isinstance(p,dict):continue
  pair=p.get("pair_address")
  price=p.get("price_usd")
  if pair:
   return str(pair),price
 return None,None

def audit(root):
 intake=root/"runtime_state/solana_opportunities/intake/normalized_events.jsonl"
 lines=intake.read_text(encoding="utf-8",errors="replace").splitlines()
 if not lines:raise RuntimeError("NO_LIVE_SOLANA_OPPORTUNITY")
 opp=json.loads(lines[-1]);asset=str(opp.get("asset_key") or "")
 records=tuple(read_pinned_pool_history(asset,root=root,limit=512))
 matches=[]
 for r in records:
  pair,price=_pair(r)
  if pair:
   matches.append({
    "observation_id":r.observation_id,
    "observed_at":r.observed_at,
    "source_id":r.source_id,
    "pair_address":pair,
    "price_usd":price,
   })
 return {
  "revision":"OSI_060B","asset_key":asset,
  "native_history_records":len(records),
  "matches":matches,"match_count":len(matches),
  "resolution_source":"NATIVE_PINNED_POOL_HISTORY",
  "execution_authority":False,"read_only":True,
 }

def write(root):
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/live_token_pair_resolution.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_060_live_token_pair_resolution_audit import audit,write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT)
  self.assertFalse(d["execution_authority"])
  print("[ASSET]",d["asset_key"])
  print("[NATIVE_HISTORY_RECORDS]",d["native_history_records"])
  print("[PAIR_MATCHES]",d["match_count"])
  for x in d["matches"][:10]:
   print("[MATCH]",json.dumps(x,sort_keys=True))
  if d["native_history_records"]==0:
   self.fail("NO_NATIVE_PINNED_POOL_HISTORY_FOR_LIVE_TOKEN")
  if d["match_count"]==0:
   self.fail("NATIVE_HISTORY_HAS_NO_PAIR_ADDRESS")
  print("[PASS] OSI-060B native-first live token/pair resolution")
  print("[TRADER] Resolves the live token from certified native Solana history; GMGN is no longer mandatory")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
"""

def main():
 print("="*116)
 print(" OSI-060B NATIVE-FIRST LIVE TOKEN / PAIR RESOLUTION")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] replaced:",MOD.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Replacement for failed GMGN-dependent OSI-060")

if __name__=="__main__":
 main()
