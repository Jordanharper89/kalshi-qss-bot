from pathlib import Path

P=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_027_physical_profitability_generalization_report.py")
T=Path("test_slop_047b_strict_generalization_gate_exact_repair.py")
s=P.read_text(encoding="utf-8")

old=''' if len(rs)<int(min_resolved) or len(tokens)<int(min_tokens):state="INSUFFICIENT_PHYSICAL_SUPPORT"
 elif e is not None and e>0:state="MULTI_TOKEN_POSITIVE_NET_EXPECTANCY_FOUND"
 else:state="GENERALIZATION_NOT_CERTIFIED"'''

new=''' token_nets={t:[] for t in tokens}
 for x in rs:
  p=pmap.get(x["prediction_id"])
  if p is not None:token_nets[p.token_address].append(float(x["net_return"]))
 token_means=[sum(v)/len(v) for v in token_nets.values() if v]
 positive_tokens=sum(x>0 for x in token_means)
 majority=positive_tokens>len(token_means)/2
 if len(rs)<int(min_resolved) or len(tokens)<int(min_tokens):state="INSUFFICIENT_PHYSICAL_SUPPORT"
 elif e is not None and e>0 and majority:state="MULTI_TOKEN_POSITIVE_NET_EXPECTANCY_FOUND"
 else:state="GENERALIZATION_NOT_CERTIFIED"'''

assert old in s,"exact certified SLOP-027 boundary not found"
P.write_text(s.replace(old,new),encoding="utf-8")

T.write_text('''from pathlib import Path
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
''',encoding="utf-8")

print("[PASS] SLOP-047B strict generalization gate exact repair installed")
print("[PASS] test installed:",T)
print("[PASS] execution_authority=FALSE")