from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_106w_exact_birth_source_truth_audit.py"
TEST=ROOT/"test_usls_106w_exact_birth_source_truth_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import ast,json,re
from pathlib import Path

ULS="qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
SLS="qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"

def _funcs(src):
 try:t=ast.parse(src)
 except Exception:return []
 out=[]
 for n in ast.walk(t):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
   out.append({"name":n.name,"args":[a.arg for a in n.args.args],
    "async":isinstance(n,ast.AsyncFunctionDef),"lineno":n.lineno})
 return out

def _interesting(src):
 keep=[]
 for i,line in enumerate(src.splitlines(),1):
  low=line.lower()
  if any(k in low for k in ("create_v2","discriminator","pump","birth","instruction","base58",
                              "decode","program_id","_birth(","is_birth(")):
   keep.append({"line":i,"text":line.rstrip()})
 return keep[:220]

def _scan(root,base,patterns):
 out=[]
 b=Path(root)/base
 for pat in patterns:
  for p in sorted(b.glob(pat)):
   src=p.read_text(encoding="utf-8",errors="ignore")
   out.append({"path":str(p.relative_to(root)),"functions":_funcs(src),
    "interesting":_interesting(src)})
 return out

def run(root):
 pump=_scan(root,ULS,["usls_020*.py","usls_021*.py","usls_022*.py","usls_023*.py","usls_024*.py"])
 meteora=_scan(root,SLS,["suls_067*.py","suls_067b*.py","suls_067c*.py"])
 pump_callable=[]
 for x in pump:
  for f in x["functions"]:
   if any(k in f["name"].lower() for k in ("birth","create","decode","exact","detect","match")):
    pump_callable.append({"path":x["path"],**f})
 meteora_callable=[]
 for x in meteora:
  for f in x["functions"]:
   if f["name"]=="_birth" or "birth" in f["name"].lower():
    meteora_callable.append({"path":x["path"],**f})
 return {"revision":"USLS_106W",
  "pump_source_count":len(pump),"meteora_source_count":len(meteora),
  "pump_candidate_callables":pump_callable,
  "meteora_candidate_callables":meteora_callable,
  "pump_sources":pump,"meteora_sources":meteora,
  "next_boundary":"EXACT_BIRTH_DISPATCH_USING_VERIFIED_EXISTING_SOURCE_CONTRACTS",
  "certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_exact_birth_source_truth_audit.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106w_exact_birth_source_truth_audit import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({
   "pump_source_count":d["pump_source_count"],
   "meteora_source_count":d["meteora_source_count"],
   "pump_candidate_callables":d["pump_candidate_callables"],
   "meteora_candidate_callables":d["meteora_candidate_callables"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  for group in ("pump_sources","meteora_sources"):
   for x in d[group]:
    print("[SOURCE]",x["path"])
    for y in x["interesting"]:print(f'{y["line"]}: {y["text"]}')
  self.assertGreater(d["pump_source_count"],0,"NO_USLS_020_024_PUMP_SOURCES_FOUND")
  self.assertGreater(d["meteora_source_count"],0,"NO_SULS_067_METEORA_SOURCES_FOUND")
  self.assertGreater(len(d["meteora_candidate_callables"]),0,"NO_METEORA_BIRTH_CALLABLE_FOUND")
  self.assertFalse(d["certification_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106W exact birth source-truth audit")
  print("[PASS] Pump and Meteora existing birth pavement physically inspected")
  print("[NEXT] EXACT_BIRTH_DISPATCH_USING_VERIFIED_EXISTING_SOURCE_CONTRACTS")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
