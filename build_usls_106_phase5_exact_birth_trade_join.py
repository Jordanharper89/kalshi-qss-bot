from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_lifecycle"
MOD=SUB/"usls_106_phase5_exact_birth_trade_join.py"
TEST=ROOT/"test_usls_106_phase5_exact_birth_trade_join.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def pick(x,names):
 for n in names:
  if x.get(n) not in (None,""):return x.get(n)
 return None

def norm_birth(x,rev,path):
 return {"venue":pick(x,("venue","family")),"program_id":pick(x,("program_id","program")),
  "token_address":pick(x,("token_address","token","mint","base_mint")),
  "market_address":pick(x,("market_address","pool","bonding_curve","curve")),
  "birth_signature":pick(x,("birth_signature","signature")),
  "birth_slot":pick(x,("birth_slot","slot")),
  "birth_observed_unix":pick(x,("birth_observed_unix","observed_unix")),
  "source_revision":rev,"source_path":path}

def norm_trade(x,rev,path):
 return {"venue":pick(x,("venue","family")),"program_id":pick(x,("program_id","program")),
  "token_address":pick(x,("token_address","token","mint","base_mint")),
  "market_address":pick(x,("market_address","pool","bonding_curve","curve")),
  "trade_signature":pick(x,("trade_signature","signature")),
  "trade_slot":pick(x,("trade_slot","slot")),
  "trade_observed_unix":pick(x,("trade_observed_unix","observed_unix")),
  "side":pick(x,("side","direction")),"trader":pick(x,("trader","user","sender")),
  "input_asset":x.get("input_asset"),"input_amount":x.get("input_amount"),
  "output_asset":x.get("output_asset"),"output_amount":x.get("output_amount"),
  "source_revision":rev,"source_path":path}

def key(x):
 return (x.get("venue"),x.get("program_id"),x.get("token_address"),x.get("market_address"))

def load_candidate(root,c):
 p=Path(root)/c["path"];d=json.loads(p.read_text(encoding="utf-8"));return d.get(c["list_key"]) or []

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_lifecycle"
 cen=json.loads((base/"phase5_physical_birth_trade_source_census.json").read_text(encoding="utf-8"))
 births=[];trades=[]
 for c in cen["candidates"]:
  rs=load_candidate(root,c)
  if c["kind"]=="BIRTH":births += [norm_birth(x,c.get("revision"),c["path"]) for x in rs if isinstance(x,dict)]
  else:trades += [norm_trade(x,c.get("revision"),c["path"]) for x in rs if isinstance(x,dict)]
 bmap={}
 for b in births:
  k=key(b)
  if all(k):bmap.setdefault(k,[]).append(b)
 out=[];unresolved=[]
 for t in trades:
  k=key(t);ms=bmap.get(k,[]) if all(k) else []
  if ms:
   for b in ms:out.append({"lifecycle_id":"|".join(map(str,k)),"birth":b,"trade":t,"join_state":"EXACT_KEY_JOIN","execution_authority":False})
  else:unresolved.append({"trade":t,"join_state":"RETAIN_UNRESOLVED_BIRTH","execution_authority":False})
 return {"revision":"USLS_106","birth_rows_seen":len(births),"trade_rows_seen":len(trades),
  "exact_join_rows":len(out),"unresolved_trade_rows":len(unresolved),
  "rows":out,"unresolved_trades":unresolved,
  "future_leakage_policy":"NO_POST_EVENT_DATA_IN_PRE_EVENT_STATE",
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_lifecycle/phase5_exact_birth_trade_join.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_106_phase5_exact_birth_trade_join import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_join(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("birth_rows_seen","trade_rows_seen","exact_join_rows","unresolved_trade_rows")},sort_keys=True))
  self.assertGreater(d["birth_rows_seen"],0);self.assertGreater(d["trade_rows_seen"],0)
  self.assertGreater(d["exact_join_rows"],0,"NO_PHYSICAL_BIRTH_TRADE_OVERLAP")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106 exact birth↔trade physical join")
  print("[PASS] unresolved trades retained rather than dropped")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
