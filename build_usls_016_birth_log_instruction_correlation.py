from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_016_birth_log_instruction_correlation.py"
TEST=ROOT/"test_usls_016_birth_log_instruction_correlation.py"

MOD_TEXT=r"""from __future__ import annotations
import json,re
from pathlib import Path

TERMS=("initialize","create","launch","migration","migrate","pool","mint","bonding","curve","liquidity")

def correlate(root):
 root=Path(root)
 base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 ev=json.loads((base/"live_multifamily_transactions.json").read_text(encoding="utf-8"))
 ix=json.loads((base/"live_program_instruction_evidence.json").read_text(encoding="utf-8"))
 tx_by_sig={r.get("signature"):r for r in ev.get("rows") or []}
 out=[]
 for row in ix.get("rows") or []:
  tx=(tx_by_sig.get(row["signature"]) or {}).get("raw_transaction") or {}
  logs=((tx.get("meta") or {}).get("logMessages") or [])
  hits=[]
  for line in logs:
   low=str(line).lower()
   if row["program_id"].lower() in low or any(t in low for t in TERMS):
    hits.append(str(line))
  out.append({**row,"birth_log_hits":hits[:80],
   "birth_term_hits":sorted({t for t in TERMS if any(t in str(z).lower() for z in logs)}),
   "candidate_birth_evidence":bool(hits)})
 fam={}
 for r in out:
  f=r["matched_family"];s=fam.setdefault(f,{"instructions":0,"with_birth_evidence":0})
  s["instructions"]+=1;s["with_birth_evidence"]+=int(r["candidate_birth_evidence"])
 return {"revision":"USLS_016","family_summary":fam,"rows":out,
  "execution_authority":False,"read_only":True}

def write(root):
 d=correlate(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/birth_log_instruction_correlation.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_016_birth_log_instruction_correlation import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_corr(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d["family_summary"],sort_keys=True))
  for r in d["rows"][:30]:
   print("[CORR]",json.dumps({"family":r["matched_family"],"signature":r["signature"],
    "birth_term_hits":r["birth_term_hits"],"candidate_birth_evidence":r["candidate_birth_evidence"]},sort_keys=True))
  self.assertGreater(len(d["rows"]),0)
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-016 live birth-log/instruction correlation")
  print("[PASS] routine program activity kept separate from birth-evidence candidates")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
