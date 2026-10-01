from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_050_native_commitment_latency_probe.py"
TEST=ROOT/"test_suls_050_native_commitment_latency_probe.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc

def _slot(commitment):
 return int(_rpc("getSlot",[{"commitment":commitment}],15.0))

def _block_time(slot):
 try:return _rpc("getBlockTime",[int(slot)],15.0)
 except Exception:return None

def probe():
 now=time.time();rows=[]
 for c in ("processed","confirmed","finalized"):
  try:
   s=_slot(c);bt=_block_time(s)
   age=None if bt is None else max(0.0,now-float(bt))
   rows.append({"commitment":c,"slot":s,"block_time":bt,"head_age_seconds":age,"ok":True})
  except Exception as e:
   rows.append({"commitment":c,"ok":False,"error":f"{type(e).__name__}: {e}"})
 by={x["commitment"]:x for x in rows}
 ps=by.get("processed",{}).get("slot");cs=by.get("confirmed",{}).get("slot");fs=by.get("finalized",{}).get("slot")
 return {"revision":"SULS_050","observed_unix":now,"rows":rows,
  "processed_minus_finalized_slots":None if ps is None or fs is None else ps-fs,
  "confirmed_minus_finalized_slots":None if cs is None or fs is None else cs-fs,
  "processed_5s_possible":bool(by.get("processed",{}).get("head_age_seconds") is not None and by["processed"]["head_age_seconds"]<=5.0),
  "confirmed_5s_possible":bool(by.get("confirmed",{}).get("head_age_seconds") is not None and by["confirmed"]["head_age_seconds"]<=5.0),
  "execution_authority":False,"read_only":True,
  "scope":"Existing OAD-148 RPC boundary reused; no new acquisition stack"}

def write(root):
 d=probe();p=root/"runtime_state/solana_opportunities/launch_surveillance/native_commitment_latency_probe.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_050_native_commitment_latency_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT)
  for x in d["rows"]:print("[COMMITMENT]",json.dumps(x,sort_keys=True))
  print("[PROCESSED_MINUS_FINALIZED_SLOTS]",d["processed_minus_finalized_slots"])
  print("[CONFIRMED_MINUS_FINALIZED_SLOTS]",d["confirmed_minus_finalized_slots"])
  print("[PROCESSED_5S_POSSIBLE]",d["processed_5s_possible"])
  print("[CONFIRMED_5S_POSSIBLE]",d["confirmed_5s_possible"])
  if not any(x.get("ok") for x in d["rows"]):self.fail("NO_NATIVE_COMMITMENT_PROBE_SUCCEEDED")
  print("[PASS] SULS-050 native commitment latency probe")
  print("[SCOPE]",d["scope"])
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-050 NATIVE COMMITMENT LATENCY PROBE");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
