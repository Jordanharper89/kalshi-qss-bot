import ast,unittest
from pathlib import Path

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")

class T(unittest.TestCase):
 def test_runtime(self):
  ast.parse(R.read_text(encoding="utf-8"))

 def test_native_swap2(self):
  s=R.read_text(encoding="utf-8")
  a=s.index("def build_meteora_ix_hot")
  b=s.index("\ndef ",a+5)
  f=s[a:b]
  self.assertIn("bytes([65,75,63,76,235,91,91,136])",f)
  self.assertNotIn("bytes([248,198,158,145,225,117,135,200])",f)

 def test_bin_arrays_attached(self):
  s=R.read_text(encoding="utf-8")
  a=s.index("def build_meteora_ix_hot")
  b=s.index("\ndef ",a+5)
  f=s[a:b]
  self.assertIn("accounts.extend",f)
  self.assertIn("for _,address in chosen",f)
  self.assertIn("MRY034_NO_BIN_ARRAY_ACCOUNTS",f)

 def test_swap2_layout(self):
  s=R.read_text(encoding="utf-8")
  a=s.index("def build_meteora_ix_hot")
  b=s.index("\ndef ",a+5)
  f=s[a:b]
  self.assertIn("fixed[:13]+[memo]+fixed[13:]",f)
  self.assertIn('struct.pack("<I",0)',f)

 def test_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
  self.assertIn("FAST_010_MIN_REALIZED_LAMPORTS=10_000",s)

if __name__=="__main__":
 unittest.main(verbosity=2)
