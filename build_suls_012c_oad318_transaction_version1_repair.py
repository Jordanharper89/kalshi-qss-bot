from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent
TARGET=ROOT/"qseries_v2/oracle_adapters/independent/oad_318_solana_native_finalized_block_stream.py"
TEST=ROOT/"test_suls_012c_oad318_transaction_version1_repair.py"

TEST_TEXT=r"""import inspect, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_repair(self):
  import qseries_v2.oracle_adapters.independent.oad_318_solana_native_finalized_block_stream as m
  src=inspect.getsource(m)

  self.assertIn('"maxSupportedTransactionVersion":1', src.replace(" ",""))
  self.assertNotIn('"maxSupportedTransactionVersion":0', src.replace(" ",""))
  print("[PASS] OAD-318 maxSupportedTransactionVersion=1")

  from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_012_native_block_shape_probe import probe
  d=probe()
  print("[SULS012_OK]",d.get("ok"))
  if d.get("shape") is not None:
   print("[SULS012_SHAPE]",d["shape"])
  if d.get("error"):
   print("[SULS012_ERROR]",d["error"])

  if not d.get("ok"):
   self.fail("SULS-012 native finalized-block probe still failed")

  print("[PASS] SULS-012C OAD-318 transaction-version-1 foundation repair")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
"""

def main():
 print("="*116)
 print(" SULS-012C OAD-318 TRANSACTION VERSION 1 FOUNDATION REPAIR")
 print("="*116)

 if not TARGET.is_file():
  raise FileNotFoundError(TARGET)

 text=TARGET.read_text(encoding="utf-8")

 old='"maxSupportedTransactionVersion":0'
 new='"maxSupportedTransactionVersion":1'

 compact=text.replace(" ","")
 if old not in compact:
  if new in compact:
   print("[PASS] OAD-318 already declares maxSupportedTransactionVersion=1")
  else:
   raise RuntimeError("EXPECTED_OAD318_TRANSACTION_VERSION_CONFIG_NOT_FOUND")
 else:
  backup=TARGET.with_suffix(TARGET.suffix+".pre_suls012c.bak")
  if not backup.exists():
   shutil.copy2(TARGET,backup)

  replaced=text.replace('"maxSupportedTransactionVersion":0','"maxSupportedTransactionVersion":1')
  if replaced==text:
   replaced=text.replace('"maxSupportedTransactionVersion": 0','"maxSupportedTransactionVersion": 1')

  TARGET.write_text(replaced,encoding="utf-8")
  print("[PASS] repaired:",TARGET.relative_to(ROOT))
  print("[PASS] backup:",backup.relative_to(ROOT))

 verify=TARGET.read_text(encoding="utf-8").replace(" ","")
 if '"maxSupportedTransactionVersion":1' not in verify:
  raise RuntimeError("OAD318_TRANSACTION_VERSION1_REPAIR_NOT_APPLIED")
 if '"maxSupportedTransactionVersion":0' in verify:
  raise RuntimeError("OAD318_TRANSACTION_VERSION0_STILL_PRESENT")

 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] maxSupportedTransactionVersion=1")
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Repairs existing OAD-318 native getBlock compatibility; no parallel acquisition path")

if __name__=="__main__":
 main()
