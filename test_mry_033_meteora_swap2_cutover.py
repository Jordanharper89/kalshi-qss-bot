import ast,unittest
from pathlib import Path

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")

class T(unittest.TestCase):
 def test_runtime_parses(self):
  ast.parse(R.read_text(encoding="utf-8"))

 def test_swap2_cutover_present(self):
  s=R.read_text(encoding="utf-8")
  a=s.index("def _mry019_align_meteora_programs")
  b=s.index("\ndef ",a+5)
  f=s[a:b]
  self.assertIn("bytes([248,198,158,145,225,117,135,200])",f)
  self.assertIn("bytes([65,75,63,76,235,91,91,136])",f)
  self.assertIn("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",f)
  self.assertIn('struct.pack("<I",0)',f)

 def test_official_swap2_account_shift(self):
  s=R.read_text(encoding="utf-8")
  a=s.index("def _mry019_align_meteora_programs")
  b=s.index("\ndef ",a+5)
  f=s[a:b]
  self.assertIn('ac[11]["pubkey"]=x_program',f)
  self.assertIn('ac[12]["pubkey"]=y_program',f)
  self.assertIn('ac=ac[:13]+[memo_meta]+ac[13:]',f)

 def test_money_and_send_guards_preserved(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
  self.assertIn("FAST_010_MIN_REALIZED_LAMPORTS=10_000",s)
  self.assertIn("FAST_010_6040_CHAIN_TRUTH",s)

if __name__=="__main__":
 unittest.main(verbosity=2)
