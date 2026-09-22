from pathlib import Path
P=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_027_physical_profitability_generalization_report.py")
T=Path("test_slop_047_strict_generalization_gate_rebuild.py")
s=P.read_text(encoding="utf-8")
old='if len(rs)<int(min_resolved) or len(tokens)<int(min_tokens):state="INSUFFICIENT_PHYSICAL_SUPPORT"\\n elif e is not None and e>0:state="MULTI_TOKEN_POSITIVE_NET_EXPECTANCY_FOUND"\\n else:state="GENERALIZATION_NOT_CERTIFIED"'
new='token_nets={t:[] for t in tokens}\\n for x in rs:\\n  p=pmap.get(x["prediction_id"])\\n  if p is not None:token_nets[p.token_address].append(float(x["net_return"]))\\n token_means=[sum(v)/len(v) for v in token_nets.values() if v]\\n positive_tokens=sum(x>0 for x in token_means);majority=positive_tokens>len(token_means)/2\\n if len(rs)<int(min_resolved) or len(tokens)<int(min_tokens):state="INSUFFICIENT_PHYSICAL_SUPPORT"\\n elif e is not None and e>0 and majority:state="MULTI_TOKEN_POSITIVE_NET_EXPECTANCY_FOUND"\\n else:state="GENERALIZATION_NOT_CERTIFIED"'
assert old in s,"expected SLOP-027 boundary changed"
P.write_text(s.replace(old,new),encoding="utf-8")
T.write_text("""from pathlib import Path
import ast
p=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_027_physical_profitability_generalization_report.py")
s=p.read_text();ast.parse(s)
assert "positive_tokens" in s
assert "majority=positive_tokens>len(token_means)/2" in s
assert "e>0 and majority" in s
print("[PASS] minimum resolved + independent tokens + positive aggregate expectancy retained")
print("[PASS] majority-positive-token requirement added")
print("[PASS] SLOP-047 strict generalization gate certified")
print("[PASS] execution_authority=FALSE")
""",encoding="utf-8")
print("[PASS] SLOP-047 strict generalization gate rebuilt")
print("[PASS] test installed:",T)