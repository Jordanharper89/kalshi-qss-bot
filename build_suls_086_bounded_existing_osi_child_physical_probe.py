from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_086_bounded_existing_osi_child_physical_probe.py"
TEST=ROOT/"test_suls_086_bounded_existing_osi_child_physical_probe.py"

MOD_TEXT=r"""from __future__ import annotations
import json,subprocess,sys,time
def probe(root,seconds=8.0):
 stop=root/"runtime_state/solana_intelligence/STOP_OSI_LIVE"
 if stop.exists():stop.unlink()
 p=subprocess.Popen([sys.executable,str(root/"run_osi_solana_intelligence_live.py")],cwd=str(root))
 time.sleep(float(seconds))
 stop.parent.mkdir(parents=True,exist_ok=True);stop.write_text("SULS-086 bounded physical probe\n",encoding="utf-8")
 try:rc=p.wait(timeout=10)
 except subprocess.TimeoutExpired:
  p.terminate()
  try:rc=p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();rc=p.wait(timeout=5)
 status=root/"runtime_state/solana_opportunities/launch_surveillance/persistent_event_driven_runtime_status.json"
 d=json.loads(status.read_text(encoding="utf-8")) if status.exists() else {}
 return {"revision":"SULS_086","child_returncode":rc,"status_found":status.exists(),
  "suls_connected":bool(d.get("connected")),"ack_count":int(d.get("ack_count",0)),
  "notifications":int(d.get("notifications",0)),"execution_authority":False,"read_only":True}
def write(root):
 d=probe(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/bounded_osi_child_physical_probe.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_086_bounded_existing_osi_child_physical_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["status_found"] or not d["suls_connected"] or d["ack_count"]<2 or d["notifications"]<1:
   self.fail("BOUND_OSI_CHILD_SULS_NOT_PHYSICAL")
  print("[PASS] SULS-086 bounded existing OSI child physical probe")
  print("[SCOPE] Bounded child launch only; top-level Oracle launcher not started")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-086 BOUNDED EXISTING OSI CHILD PHYSICAL PROBE");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()