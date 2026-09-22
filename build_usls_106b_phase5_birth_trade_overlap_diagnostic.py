from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_lifecycle"
MOD=SUB/"usls_106b_phase5_birth_trade_overlap_diagnostic.py"
TEST=ROOT/"test_usls_106b_phase5_birth_trade_overlap_diagnostic.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def pick(x,names):
 for n in names:
  v=x.get(n)
  if v not in (None,""):return str(v)
 return None

def venue(x):
 v=pick(x,("venue","launcher_family","family","source_family"))
 if not v:return None
 u=v.upper().replace(".","_").replace("-","_").replace(" ","_")
 aliases={"PUMPSWAP":"PUMP_SWAP","PUMP_SWAP_AMM":"PUMP_SWAP","PUMPFUN":"PUMP_FUN","PUMP_FUN":"PUMP_FUN",
  "MOONSHOT":"MOONIT","MOONIT":"MOONIT","BOOP":"BOOP_FUN","BOOP_FUN":"BOOP_FUN"}
 return aliases.get(u,u)

def norm(x):
 return {"venue":venue(x),
  "program_id":pick(x,("program_id","program")),
  "token":pick(x,("token_address","token_mint","mint","base_mint","token")),
  "market":pick(x,("market_address","pair_address","pool","bonding_curve","curve")),
  "signature":pick(x,("birth_signature","trade_signature","signature"))}

def load(root,c):
 p=Path(root)/c["path"];d=json.loads(p.read_text(encoding="utf-8"))
 return [norm(x) for x in (d.get(c["list_key"]) or []) if isinstance(x,dict)]

def nz(xs,k):return {x[k] for x in xs if x.get(k)}
def combo(xs,*ks):return {tuple(x.get(k) for k in ks) for x in xs if all(x.get(k) for k in ks)}

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_lifecycle"
 cen=json.loads((base/"phase5_physical_birth_trade_source_census.json").read_text(encoding="utf-8"))
 births=[c for c in cen["candidates"] if c["kind"]=="BIRTH"]
 trades=[c for c in cen["candidates"] if c["kind"]=="TRADE"]
 out=[]
 for b in births:
  br=load(root,b)
  for t in trades:
   tr=load(root,t)
   stats={"venue":len(nz(br,"venue")&nz(tr,"venue")),
    "program":len(nz(br,"program_id")&nz(tr,"program_id")),
    "token":len(nz(br,"token")&nz(tr,"token")),
    "market":len(nz(br,"market")&nz(tr,"market")),
    "signature":len(nz(br,"signature")&nz(tr,"signature")),
    "token_market":len(combo(br,"token","market")&combo(tr,"token","market")),
    "venue_token_market":len(combo(br,"venue","token","market")&combo(tr,"venue","token","market")),
    "program_token_market":len(combo(br,"program_id","token","market")&combo(tr,"program_id","token","market"))}
   score=stats["program_token_market"]*1000+stats["venue_token_market"]*500+stats["token_market"]*100+stats["market"]*10+stats["token"]
   if score:
    out.append({"birth_path":b["path"],"birth_revision":b.get("revision"),"birth_key":b["list_key"],"birth_rows":len(br),
     "trade_path":t["path"],"trade_revision":t.get("revision"),"trade_key":t["list_key"],"trade_rows":len(tr),
     "overlap":stats,"score":score})
 out.sort(key=lambda x:x["score"],reverse=True)
 return {"revision":"USLS_106B","pair_count":len(out),"pairs":out[:50],
  "certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_lifecycle/phase5_birth_trade_overlap_diagnostic.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_106b_phase5_birth_trade_overlap_diagnostic import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_diag(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"pair_count":d["pair_count"]},sort_keys=True))
  for x in d["pairs"][:30]:print("[PAIR]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["pair_count"],0,"NO_BIRTH_TRADE_OVERLAP_AT_ANY_IDENTITY_LEVEL")
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106B birth↔trade overlap diagnostic")
  print("[PASS] no lifecycle certification claimed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
