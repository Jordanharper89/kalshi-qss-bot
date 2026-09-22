from pathlib import Path
P=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_025_live_freeze_maturity_resolution_worker.py")
assert P.exists(),P
s=P.read_text()
old="before=unresolved_view(root);watch=tuple(sorted(set(active)|set(before.tokens)))"
new="before=unresolved_view(root);pending=tuple(before.tokens);fresh=tuple(x for x in active if x not in set(pending));watch=pending+fresh[:max(0,int(token_limit)-len(pending))]"
assert old in s,"exact SLOP-025 boundary changed"
s=s.replace(old,new)
old2="life=lifecycle_pass(active,root=root);after=unresolved_view(root);resolved=[]"
new2="life=lifecycle_pass(fresh[:int(token_limit)],root=root);after=unresolved_view(root);resolved=[]"
assert old2 in s,"exact lifecycle call changed"
P.write_text(s.replace(old2,new2),encoding="utf-8")
print("[PASS] SLOP-041 pending-first surveillance installed")
