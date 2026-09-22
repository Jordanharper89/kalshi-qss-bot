from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_031_pump_exact_trade_discriminator_registry.py"
TEST=ROOT/"test_usls_031_pump_exact_trade_discriminator_registry.py"

MOD_TEXT=r"""from __future__ import annotations
import hashlib,json
from pathlib import Path

ALPHABET="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
PUMP="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

NAMES=("buy","sell","buy_exact_sol_in")
REGISTRY={hashlib.sha256(("global:"+n).encode()).digest()[:8].hex():n for n in NAMES}

def b58decode(s):
 n=0
 for c in s:n=n*58+ALPHABET.index(c)
 b=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
 return b"\0"*(len(s)-len(s.lstrip("1")))+b

def classify(data):
 raw=b58decode(data or "")
 disc=raw[:8].hex() if len(raw)>=8 else None
 name=REGISTRY.get(disc)
 side="BUY" if name in ("buy","buy_exact_sol_in") else ("SELL" if name=="sell" else "UNKNOWN_TRADE_TYPE")
 return {"discriminator_hex":disc,"instruction_name":name,"side":side,
  "decoder_state":"EXACT_DISCRIMINATOR" if name else "UNKNOWN_DISCRIMINATOR"}

def write(root):
 d={"revision":"USLS_031","program_id":PUMP,"registry":REGISTRY,
  "unknown_retention":True,"execution_authority":False,"read_only":True}
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_trade_discriminator_registry.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import hashlib,json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_031_pump_exact_trade_discriminator_registry import write,classify
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_registry(self):
  p,d=write(ROOT)
  checks={}
  for name in ("buy","sell","buy_exact_sol_in"):
   raw=hashlib.sha256(("global:"+name).encode()).digest()[:8]
   # local tiny base58 encoder for deterministic fixture
   n=int.from_bytes(raw,"big");alpha="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";s=""
   while n:n,r=divmod(n,58);s=alpha[r]+s
   x=classify(s or "1");checks[name]=x["side"]
  print("[STATE]",json.dumps({"registry":d["registry"],"fixture_sides":checks},sort_keys=True))
  self.assertEqual(checks["buy"],"BUY");self.assertEqual(checks["sell"],"SELL")
  self.assertEqual(checks["buy_exact_sol_in"],"BUY")
  self.assertEqual(classify("1")["side"],"UNKNOWN_TRADE_TYPE")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-031 Pump exact trade discriminator registry certified")
  print("[PASS] unknown Pump instructions are retained, never guessed into BUY/SELL")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
