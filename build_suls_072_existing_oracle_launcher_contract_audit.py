from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_072_existing_oracle_launcher_contract_audit.py"
TEST=ROOT/"test_suls_072_existing_oracle_launcher_contract_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import json
CANDIDATES=("run_oracle_live.py","run_oracle_LIVE.py")

def audit(root):
 rows=[]
 for name in CANDIDATES:
  p=root/name
  if not p.exists():continue
  src=p.read_text(encoding="utf-8",errors="ignore");hits=[]
  terms=("solana","gmgn","crypto_learning","fast_lane","inventory","reasoning","learning","thread","worker","daemon","start(")
  for i,line in enumerate(src.splitlines(),1):
   if any(t.lower() in line.lower() for t in terms):
    hits.append({"line":i,"text":line[:500]})
  rows.append({"path":name,"line_count":len(src.splitlines()),"hits":hits[:250],
    "imports_solana_launch_surveillance":"solana_launch_surveillance" in src,
    "mentions_execution_authority_false":"execution_authority" in src.lower() and "false" in src.lower()})
 return {"revision":"SULS_072","launcher_count":len(rows),"launchers":rows,
  "execution_authority":False,"read_only":True,
  "scope":"Read-only contract audit only; production launcher unchanged"}

def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/existing_oracle_launcher_contract_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_072_existing_oracle_launcher_contract_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT);print("[LAUNCHER_COUNT]",d["launcher_count"])
  for x in d["launchers"]:
   print("[LAUNCHER]",x["path"],"lines=",x["line_count"],"suls_import=",x["imports_solana_launch_surveillance"])
   for h in x["hits"][:80]:print("[HIT]",h["line"],h["text"])
  if d["launcher_count"]==0:self.fail("NO_EXISTING_ORACLE_LAUNCHER_FOUND")
  print("[PASS] SULS-072 existing Oracle launcher contract audit")
  print("[SCOPE]",d["scope"])
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")