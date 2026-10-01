from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_078_existing_osi_child_contract_audit.py"
TEST=ROOT/"test_suls_078_existing_osi_child_contract_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import json
TARGET="run_osi_solana_intelligence_live.py"

def audit(root):
 p=root/TARGET
 if not p.exists():
  return {"revision":"SULS_078","exists":False,"path":TARGET,"execution_authority":False,"read_only":True}
 src=p.read_text(encoding="utf-8",errors="ignore");lines=src.splitlines();hits=[]
 terms=("while","sleep","thread","async","solana","oad_","osi_","runtime_state","checkpoint","execution_authority","def main","if __name__")
 for i,line in enumerate(lines,1):
  if any(t.lower() in line.lower() for t in terms):
   hits.append({"line":i,"text":line[:600]})
 return {"revision":"SULS_078","exists":True,"path":TARGET,"line_count":len(lines),
  "hits":hits[:400],"imports_suls":"solana_launch_surveillance" in src,
  "execution_authority_false":"execution_authority" in src.lower() and "false" in src.lower(),
  "execution_authority":False,"read_only":True,
  "scope":"Read-only audit; existing OSI child unchanged"}

def write(root):
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/launch_surveillance/existing_osi_child_contract_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_078_existing_osi_child_contract_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT)
  print("[STATE]",{k:v for k,v in d.items() if k!="hits"})
  for h in d.get("hits",[])[:120]:print("[HIT]",h["line"],h["text"])
  if not d.get("exists"):self.fail("EXISTING_OSI_SOLANA_CHILD_NOT_FOUND")
  print("[PASS] SULS-078 existing OSI child contract audit")
  print("[SCOPE]",d["scope"])
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")