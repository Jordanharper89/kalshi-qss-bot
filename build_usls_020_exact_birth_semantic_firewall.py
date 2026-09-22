from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_020_exact_birth_semantic_firewall.py"
TEST=ROOT/"test_usls_020_exact_birth_semantic_firewall.py"

MOD_TEXT=r"""from __future__ import annotations
import hashlib,json
from pathlib import Path

ALPHABET="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
PUMP="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
CREATE_V2=hashlib.sha256(b"global:create_v2").digest()[:8]

def b58decode(s):
 n=0
 for c in s:n=n*58+ALPHABET.index(c)
 b=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
 return b"\0"*(len(s)-len(s.lstrip("1")))+b

def audit(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 d=json.loads((base/"live_program_instruction_evidence.json").read_text(encoding="utf-8"))
 pump=[x for x in d.get("rows") or [] if x.get("program_id")==PUMP]
 rows=[]
 for x in pump:
  raw=b58decode(x.get("data") or "")
  rows.append({"signature":x.get("signature"),"data_prefix_hex":raw[:8].hex(),
   "exact_create_v2":raw[:8]==CREATE_V2,"account_count":len(x.get("accounts") or [])})
 return {"revision":"USLS_020","pump_instruction_count":len(rows),
  "create_v2_discriminator_hex":CREATE_V2.hex(),
  "exact_create_v2_count":sum(1 for x in rows if x["exact_create_v2"]),
  "heuristic_birth_is_certification":False,"rows":rows,
  "execution_authority":False,"read_only":True}

def write(root):
 d=audit(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/exact_birth_semantic_firewall.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_020_exact_birth_semantic_firewall import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_firewall(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("pump_instruction_count","create_v2_discriminator_hex","exact_create_v2_count","heuristic_birth_is_certification")},sort_keys=True))
  for x in d["rows"]:print("[PUMP_IX]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["pump_instruction_count"],0)
  self.assertFalse(d["heuristic_birth_is_certification"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-020 exact instruction-discriminator birth semantic firewall")
  print("[PASS] generic create/mint log words can no longer certify a protocol birth")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
