from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_008_program_identity_evidence_audit.py"
TEST=ROOT/"test_suls_008_program_identity_evidence_audit.py"
MOD_TEXT=r"""from __future__ import annotations
import json,re
from pathlib import Path
B58=re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
KEYS=("program_id","programId","program","owner","dex_id","pumpfun","pumpswap","raydium","meteora","moonshot","stonk","bonk","orca")
def audit(root):
 bases=[root/"qseries_v2/oracle_adapters/independent",root/"runtime_state/solana_opportunities"]
 rows=[]
 for base in bases:
  if not base.exists():continue
  pats=("*.py","*.json","*.jsonl")
  for pat in pats:
   for p in base.rglob(pat):
    try:text=p.read_text(encoding="utf-8",errors="ignore")
    except Exception:continue
    if not any(k.lower() in text.lower() for k in KEYS):continue
    addrs=sorted(set(B58.findall(text)))[:30]
    labels=sorted({k for k in KEYS if k.lower() in text.lower()})
    if addrs or labels:rows.append({"file":str(p.relative_to(root)),"labels":labels,"base58_candidates":addrs})
 return {"revision":"SULS_008","evidence_files":len(rows),"rows":rows[:200],"execution_authority":False,"read_only":True}
def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/program_identity_evidence_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_008_program_identity_evidence_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"]);print("[EVIDENCE_FILES]",d["evidence_files"])
  for r in d["rows"][:40]:print("[PROGRAM_EVIDENCE]",json.dumps(r,sort_keys=True))
  if d["evidence_files"]==0:self.fail("NO_PROGRAM_IDENTITY_EVIDENCE")
  print("[PASS] SULS-008 program identity evidence audit")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*116);print(" SULS-008 PROGRAM IDENTITY EVIDENCE AUDIT");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
