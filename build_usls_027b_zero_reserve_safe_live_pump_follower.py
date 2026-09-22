from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_027b_zero_reserve_safe_live_pump_follower.py"
TEST=ROOT/"test_usls_027b_zero_reserve_safe_live_pump_follower.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_022_live_pump_create_v2_capture import capture
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_023_pump_create_v2_exact_account_decoder import decode
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_025_pump_bonding_curve_state_decoder import _rpc,decode_account
H=(1,5,15,30)

def _state(addr):
 r=_rpc("getAccountInfo",[addr,{"encoding":"base64","commitment":"confirmed"}])
 return decode_account((r or {}).get("value"))

def _sample(addr,h,target):
 obs=time.time();s=_state(addr)
 vt=(s or {}).get("virtual_token_reserves") or 0
 vq=(s or {}).get("virtual_quote_reserves") or 0
 return {"horizon_seconds":h,"target_unix":target,"observed_unix":obs,
  "lag_seconds":max(0.0,obs-target),"state":s,
  "price_state":"PRICE_AVAILABLE" if vt>0 and vq>0 else "PRICE_UNAVAILABLE_ZERO_RESERVES",
  "price_available":bool(vt>0 and vq>0)}

def run(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 cap=asyncio.run(capture(seconds=35,max_hits=1))
 (base/"pump_create_v2_live_capture.json").write_text(json.dumps(cap,indent=2,sort_keys=True),encoding="utf-8")
 dec=decode(root)
 if not dec["rows"]:raise RuntimeError("NO_EXACT_PUMP_BIRTH_DECODED")
 b=dec["rows"][0];anchor=time.time();samples=[]
 samples.append(_sample(b["bonding_curve"],0,anchor))
 for h in H:
  delay=anchor+h-time.time()
  if delay>0:time.sleep(delay)
  samples.append(_sample(b["bonding_curve"],h,anchor+h))
 return {"revision":"USLS_027B","signature":b["signature"],"token_address":b["mint"],
  "bonding_curve":b["bonding_curve"],"quote_mint":b["quote_mint"],
  "birth_observed_unix":b["observed_unix"],"sampling_anchor_unix":anchor,
  "samples":samples,"price_available_samples":sum(1 for x in samples if x["price_available"]),
  "price_unavailable_samples":sum(1 for x in samples if not x["price_available"]),
  "remaining_horizons":[60,300,900],"execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/pump_short_horizon_curve_follow.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_027b_zero_reserve_safe_live_pump_follower import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_follow(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"token_address":d["token_address"],"sample_count":len(d["samples"]),
   "price_available_samples":d["price_available_samples"],"price_unavailable_samples":d["price_unavailable_samples"],
   "remaining_horizons":d["remaining_horizons"]},sort_keys=True))
  for x in d["samples"]:
   print("[SAMPLE]",json.dumps({"horizon_seconds":x["horizon_seconds"],"target_unix":x["target_unix"],
    "observed_unix":x["observed_unix"],"lag_seconds":x["lag_seconds"],"price_state":x["price_state"],
    "virtual_token_reserves":(x["state"] or {}).get("virtual_token_reserves"),
    "virtual_quote_reserves":(x["state"] or {}).get("virtual_quote_reserves")},sort_keys=True))
  self.assertEqual([x["horizon_seconds"] for x in d["samples"]],[0,1,5,15,30])
  self.assertTrue(all(x["state"] and x["state"].get("valid") for x in d["samples"]))
  self.assertEqual(d["price_available_samples"]+d["price_unavailable_samples"],5)
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-027B zero-reserve-safe prospective Pump curve follower")
  print("[PASS] unavailable reserve states retained instead of fabricated or dropped")
  print("[PASS] 60s/5m/15m remain explicitly pending")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
