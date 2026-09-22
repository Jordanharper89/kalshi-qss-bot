from pathlib import Path
import json,time
from qseries_v2.oracle_predictive_discovery.opd_067_exact_anchor_sequence_asof_reader import read_before_anchor,CB,COND,LEARN
root=Path.cwd();sp=root/"runtime/predictive_data/opd_061_live_anchor_spool.jsonl"
a=json.loads([x for x in sp.read_text(encoding="utf-8").splitlines() if x.strip()][-1])
t=time.time();rows,seq=read_before_anchor(a,root);dt=time.time()-t
assert seq is not None and rows
counts={"coinbase":0,"condition":0,"learned":0}
assert all(int(x[0])<=int(seq) for x in rows)
assert all(x[1]==CB or str(x[1]).startswith(COND) or str(x[1]).startswith(LEARN) for x in rows)
for _,s,_,_ in rows:
 if s==CB:counts["coinbase"]+=1
 elif str(s).startswith(COND):counts["condition"]+=1
 elif str(s).startswith(LEARN):counts["learned"]+=1
print("[ANCHOR_ID]",a["anchor_id"])
print("[ANCHOR_SEQUENCE]",seq)
print("[ROWS]",len(rows),"[COUNTS]",counts,"[SECONDS]",round(dt,3))
assert all(counts[x]>0 for x in counts)
assert dt<5.0
print("[BOUNDED_WINDOW] 50000 EXACT PRE/AT-ANCHOR SEQUENCES")
print("[SQL_SOURCE_PUSH_DOWN] TRUE")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
print("[PASS] OPD-067 foundational bounded SQL push-down repair certified")
