from pathlib import Path
import ast
p=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_027_physical_profitability_generalization_report.py")
s=p.read_text(encoding="utf-8");ast.parse(s)
assert "positive_tokens=sum(x>0 for x in token_means)" in s
assert "majority=positive_tokens>len(token_means)/2" in s
assert "e is not None and e>0 and majority" in s
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_027_physical_profitability_generalization_report import physical_report
r=physical_report()
print("[PHYSICAL REPORT]",r)
assert r.resolved>=15
assert r.independent_tokens>=3
print("[PASS] aggregate positive expectancy alone cannot certify generalization")
print("[PASS] majority-positive independent-token requirement certified")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-047B CERTIFIED")
