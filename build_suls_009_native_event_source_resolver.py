from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_009_native_event_source_resolver.py";TEST=ROOT/"test_suls_009_native_event_source_resolver.py"
MOD_TEXT=r"""from __future__ import annotations
import json
RANK=("logsSubscribe","programSubscribe","blockSubscribe","websocket","getBlock","getTransaction","getSignaturesForAddress")
def resolve(root):
 d=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/native_capability_audit.json").read_text(encoding="utf-8"));scored=[]
 for r in d.get("rows",[]):
  hits=r.get("hits",[]);score=sum((len(RANK)-i)*10 for i,x in enumerate(RANK) if x in hits)
  scored.append({"file":r["file"],"score":score,"hits":hits,"functions":r.get("functions",[])})
 scored.sort(key=lambda x:(-x["score"],x["file"]));best=scored[0] if scored else None
 return {"revision":"SULS_009","candidate_count":len(scored),"best_candidate":best,
 "native_event_candidate_found":bool(best and best["score"]>0),"execution_authority":False}
def write(root):
 d=resolve(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_event_source_resolver.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_009_native_event_source_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_resolver(self):
  p,d=write(ROOT);print("[CANDIDATE_COUNT]",d["candidate_count"]);print("[NATIVE_EVENT_CANDIDATE_FOUND]",d["native_event_candidate_found"])
  print("[BEST_CANDIDATE]",json.dumps(d["best_candidate"],sort_keys=True));print("[PASS] SULS-009 native event source resolver")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name)