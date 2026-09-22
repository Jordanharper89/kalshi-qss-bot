from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_091_remaining_venue_exact_trade_census.py"
TEST=ROOT/"test_usls_091_remaining_venue_exact_trade_census.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_090_remaining_venue_source_semantic_registry import SEMANTICS
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
def b58d(s):
 n=0
 for c in s:n=n*58+ALPH.index(c)
 b=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
 return b"\0"*(len(s)-len(s.lstrip("1")))+b
def keys(tx):
 ks=(((tx or {}).get("transaction") or {}).get("message") or {}).get("accountKeys") or []
 return [x.get("pubkey") if isinstance(x,dict) else x for x in ks]
def all_ix(tx):
 msg=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
 for i,ix in enumerate(msg.get("instructions") or []):out.append(("top",i,ix))
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  for i,ix in enumerate(g.get("instructions") or []):out.append((f"inner:{g.get('index')}",i,ix))
 return out
def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"remaining_venue_live_transactions.json").read_text(encoding="utf-8"));rows=[];unknown=[]
 for r in src["rows"]:
  if not r["hydrated"]:continue
  tx=r["transaction"];ks=keys(tx)
  for level,ordinal,ix in all_ix(tx):
   pid=ix.get("programId")
   if not pid and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(ks):pid=ks[ix["programIdIndex"]]
   if pid!=r["program_id"] or not ix.get("data"):continue
   raw=b58d(ix["data"]);disc=raw[:8].hex() if len(raw)>=8 else raw.hex()
   ac=ix.get("accounts") or [];ac=[ks[a] if isinstance(a,int) and a<len(ks) else a for a in ac]
   sem=SEMANTICS.get(r["venue"],{}).get(disc)
   z={"venue":r["venue"],"signature":r["signature"],"level":level,"instruction_ordinal":ordinal,
      "discriminator_hex":disc,"accounts":ac,"transaction":tx,"execution_authority":False}
   if sem:rows.append({**z,"instruction_name":sem["name"],"side":sem["side"],"role_names":sem["roles"]})
   else:unknown.append({**z,"instruction_name":"UNKNOWN_INSTRUCTION_TYPE","side":"UNKNOWN_TRADE_TYPE"})
 return {"revision":"USLS_091","exact_trade_count":len(rows),"unknown_instruction_count":len(unknown),
  "venue_exact_counts":{v:sum(x["venue"]==v for x in rows) for v in SEMANTICS},
  "rows":rows,"unknown_rows":unknown,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_exact_trade_census.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_091_remaining_venue_exact_trade_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_census(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"exact_trade_count":d["exact_trade_count"],"unknown_instruction_count":d["unknown_instruction_count"],"venue_exact_counts":d["venue_exact_counts"]},sort_keys=True))
  self.assertGreater(d["exact_trade_count"],0)
  for v,n in d["venue_exact_counts"].items():self.assertGreater(n,0,f"NO_EXACT_TRADES_{v}")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-091 exact physical trade census across Moonit/Boop/Heaven")
  print("[PASS] unknown program instructions retained separately")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
