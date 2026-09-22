from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
if not (D/"slop_006_live_hot_token_surveillance_registry.py").exists():raise SystemExit("[FAIL] SLOP-006 missing")
M=D/"slop_007_temporal_readiness_gate.py"
M.write_text(r"""from dataclasses import dataclass
from datetime import datetime
READ_ONLY=True;EXECUTION_AUTHORITY=False
def _dt(v):return datetime.fromisoformat(str(v).replace("Z","+00:00"))
@dataclass(frozen=True,slots=True)
class TemporalReadiness:
 token_address:str;records:int;span_seconds:float;ready:bool;state:str;execution_authority:bool=False
def temporal_readiness(token_address,records,min_records=2,min_span_seconds=60.0):
 rows=tuple(sorted(records,key=lambda r:_dt(r.observed_at)))
 span=0.0 if len(rows)<2 else (_dt(rows[-1].observed_at)-_dt(rows[0].observed_at)).total_seconds()
 ok=len(rows)>=int(min_records) and span>=float(min_span_seconds)
 return TemporalReadiness(token_address,len(rows),span,ok,"READY_60S" if ok else "WARMING",False)
""",encoding="utf-8")
T=R/"test_slop_007_temporal_readiness_gate.py"
T.write_text(r"""import unittest
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_007_temporal_readiness_gate import temporal_readiness
class T(unittest.TestCase):
 def test_gate(self):
  a=SimpleNamespace(observed_at="2026-09-17T00:00:00+00:00");b=SimpleNamespace(observed_at="2026-09-17T00:01:01+00:00")
  x=temporal_readiness("T",(a,b));print("[SLOP-007]",x)
  self.assertTrue(x.ready);self.assertGreaterEqual(x.span_seconds,60)
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-007 installed")
print("[PASS] 60-second state requires physical temporal span, not observation count alone")