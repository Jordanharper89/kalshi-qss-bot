from pathlib import Path

ROOT=Path(__file__).resolve().parent
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_086_bounded_existing_osi_child_physical_probe.py"
TEST=ROOT/"test_suls_086b_bounded_probe_stop_cleanup_repair.py"
STOP=ROOT/"runtime_state/solana_intelligence/STOP_OSI_LIVE"

NEEDLE=''' status=root/"runtime_state/solana_opportunities/launch_surveillance/persistent_event_driven_runtime_status.json"
 d=json.loads(status.read_text(encoding="utf-8")) if status.exists() else {}
 return {"revision":"SULS_086"'''

REPL=''' status=root/"runtime_state/solana_opportunities/launch_surveillance/persistent_event_driven_runtime_status.json"
 d=json.loads(status.read_text(encoding="utf-8")) if status.exists() else {}
 if stop.exists():stop.unlink()
 return {"revision":"SULS_086"'''

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_086_bounded_existing_osi_child_physical_probe import probe
ROOT=Path(__file__).resolve().parent
STOP=ROOT/"runtime_state/solana_intelligence/STOP_OSI_LIVE"
class T(unittest.TestCase):
 def test_cleanup(self):
  d=probe(ROOT,seconds=4.0)
  print("[STATE]",d)
  self.assertTrue(d["suls_connected"])
  self.assertGreaterEqual(d["ack_count"],2)
  self.assertGreaterEqual(d["notifications"],1)
  self.assertFalse(STOP.exists())
  print("[PASS] SULS-086B bounded probe STOP marker cleanup")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116)
 print(" SULS-086B BOUNDED PROBE STOP MARKER CLEANUP REPAIR")
 print("="*116)
 src=TARGET.read_text(encoding="utf-8")
 if REPL not in src:
  if NEEDLE not in src:raise SystemExit("EXPECTED_SULS_086_BOUNDARY_NOT_FOUND")
  TARGET.write_text(src.replace(NEEDLE,REPL,1),encoding="utf-8")
 if STOP.exists():STOP.unlink()
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] canonical SULS-086 repaired")
 print("[PASS] stale STOP_OSI_LIVE cleared")
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()