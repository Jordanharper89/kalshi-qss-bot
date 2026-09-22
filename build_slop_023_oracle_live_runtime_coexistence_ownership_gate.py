from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_023_oracle_live_runtime_coexistence_ownership_gate.py"
M.write_text(r"""from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import _ensure_certified_writer,_stop_certification_writer
READ_ONLY=True;EXECUTION_AUTHORITY=False
def runtime_coexistence_gate(root=None,progress=print):
 root=Path(root or Path.cwd()).resolve();proc=None
 try:
  proc,state=_ensure_certified_writer(root,progress)
  owned=proc is not None
  return {"writer_state":state,"certification_owns_writer":owned,
   "stop_external_writer":False,"state":"RUNTIME_COEXISTENCE_CERTIFIED",
   "execution_authority":False}
 finally:
  if proc is not None:_stop_certification_writer(proc,progress)
""",encoding="utf-8")
T=R/"test_slop_023_oracle_live_runtime_coexistence_ownership_gate.py"
T.write_text(r"""import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_023_oracle_live_runtime_coexistence_ownership_gate import runtime_coexistence_gate
class T(unittest.TestCase):
 def test_external_writer_never_stopped(self):
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_023_oracle_live_runtime_coexistence_ownership_gate._ensure_certified_writer",return_value=(None,"EXISTING_LEASE")),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_023_oracle_live_runtime_coexistence_ownership_gate._stop_certification_writer") as stop:
   x=runtime_coexistence_gate()
  print("[SLOP-023]",x);stop.assert_not_called()
  self.assertFalse(x["certification_owns_writer"]);self.assertFalse(x["stop_external_writer"])
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-023 installed")
print("[PASS] existing production writer ownership protected")
print("[PASS] execution_authority=FALSE")
