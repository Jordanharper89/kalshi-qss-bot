from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_060_live_token_pair_resolution_audit.py"
TEST=ROOT/"test_osi_060_live_token_pair_resolution_audit.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_045_exact_solana_gmgn_postgresql_reader import read
def _flat(v,out=None):
 out={} if out is None else out
 if isinstance(v,dict):
  for k,x in v.items():
   out.setdefault(str(k).lower(),x)
   if isinstance(x,(dict,list)):_flat(x,out)
 elif isinstance(v,list):
  for x in v[:20]:
   if isinstance(x,(dict,list)):_flat(x,out)
 return out
def audit(root):
 intake=root/"runtime_state/solana_opportunities/intake/normalized_events.jsonl"
 lines=intake.read_text(encoding="utf-8",errors="replace").splitlines()
 if not lines:raise RuntimeError("NO_LIVE_SOLANA_OPPORTUNITY")
 opp=json.loads(lines[-1]);asset=str(opp.get("asset_key") or "")
 rows=read(root,5000)["rows"];matches=[]
 for r in rows:
  if not r["source_id"].startswith("source.gmgn.solana.token."):continue
  f=_flat(r.get("canonical_observation_json") or {})
  values={str(v) for v in f.values() if not isinstance(v,(dict,list))}
  if asset and (asset in r["source_id"] or asset in values):
   pair=f.get("pair_address") or f.get("address") or f.get("pool_address")
   price=f.get("price_usd") or f.get("price")
   matches.append({"observation_id":r["observation_id"],"observed_at":r["observed_at"],"source_id":r["source_id"],"observation_type":r["observation_type"],"pair_address":pair,"price":price})
 return {"revision":"OSI_060","asset_key":asset,"matches":matches,"match_count":len(matches),"execution_authority":False,"read_only":True}
def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/live_token_pair_resolution.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_060_live_token_pair_resolution_audit import audit,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT)
  print("[ASSET]",d["asset_key"]);print("[MATCHES]",d["match_count"])
  for x in d["matches"][:10]:print("[MATCH]",json.dumps(x,sort_keys=True))
  if d["match_count"]==0:self.fail("LIVE_TOKEN_HAS_NO_GMGN_PAIR_HISTORY")
  print("[PASS] OSI-060 live token/pair resolution audit")
  print("[TRADER] Resolves the current opportunity to its historical GMGN pool identity before outcome grading")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*116);print(" OSI-060 LIVE TOKEN / PAIR RESOLUTION AUDIT");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
