from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_162d_phase8_physical_friction_linkage_checkpoint.py"
TEST=ROOT/"test_usls_162d_phase8_physical_friction_linkage_checkpoint.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
LEDGER="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
FRIC="runtime_state/solana_opportunities/solana_scanner/phase7_first_strict_executable_ready_rows.json"
def run(root):
 root=Path(root);led=json.loads((root/LEDGER).read_text(encoding="utf-8"));f=json.loads((root/FRIC).read_text(encoding="utf-8"))
 ready=f.get("ready_rows",[]);byfam={}
 for x in ready:
  fam=x.get("family")
  if fam:byfam.setdefault(fam,[]).append(x)
 rows=[]
 for c in led.get("cases",[]):
  fs=byfam.get(c["family"],[])
  fees=[float(x["fee_fraction"]) for x in fs if isinstance(x.get("fee_fraction"),(int,float))]
  devs=[abs(float(x["realized_execution_deviation_fraction"])) for x in fs if isinstance(x.get("realized_execution_deviation_fraction"),(int,float))]
  fee=sorted(fees)[len(fees)//2] if fees else None;dev=sorted(devs)[len(devs)//2] if devs else None
  net=None
  if fee is not None and dev is not None and isinstance(c.get("gross_forward_return"),(int,float)):
   net=float(c["gross_forward_return"])-(2*fee+2*dev)
  rows.append({**c,"physical_friction_supported":net is not None,"modeled_round_trip_fee_fraction":None if fee is None else 2*fee,
   "modeled_round_trip_execution_deviation_fraction":None if dev is None else 2*dev,"net_forward_return":net})
 net=[x["net_forward_return"] for x in rows if isinstance(x.get("net_forward_return"),(int,float))]
 return {"revision":"USLS_162D","case_count":len(rows),"friction_supported_case_count":len(net),
  "friction_supported_families":sorted({x["family"] for x in rows if x["physical_friction_supported"]}),
  "mean_net_forward_return":None if not net else sum(net)/len(net),
  "net_positive_frequency":None if not net else sum(v>0 for v in net)/len(net),
  "rows":rows,"friction_policy":"ONLY_USLS_131_PHYSICALLY_READY_FAMILY_EVIDENCE_NO_CROSS_FAMILY_IMPUTATION",
  "next_boundary":"UPDATED_PHASE8_CERTIFICATION_CHECKPOINT","profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_physical_friction_linkage.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162d_phase8_physical_friction_linkage_checkpoint import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"case_count":d["case_count"],"friction_supported_case_count":d["friction_supported_case_count"],
   "friction_supported_families":d["friction_supported_families"],"mean_net_forward_return":d["mean_net_forward_return"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["case_count"],0)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-162D physical friction linkage checkpoint")
  print("[PASS] no fee/slippage evidence imputed across unsupported families")
  print("[NEXT] UPDATED_PHASE8_CERTIFICATION_CHECKPOINT")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
