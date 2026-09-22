from pathlib import Path
from collections import Counter
from qseries_v2.oracle_predictive_discovery.opd_043_exact_durable_maturity_queue import rebuild_exact,mature_exact
from qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome import exact_anchor_sequence
from qseries_v2.oracle_predictive_discovery.opd_055_event_time_highwater_coverage import read_until_witness

root=Path.cwd()
rebuild_exact(root)
rows=mature_exact(root)[:24]

counts=Counter()
horizons=Counter()

for i,state in enumerate(rows,1):
    seq=exact_anchor_sequence(state,root)

    if seq is None:
        reason="MISSING_EXACT_ANCHOR_SEQUENCE"
    else:
        end=float(state["observed_epoch"])+int(state["horizon_seconds"])
        path,witness,highwater=read_until_witness(
            state["ticker"],
            state["observed_epoch"],
            end,
            root,
            seq,
            2000,
            16,
        )

        reason="RESOLVABLE" if witness is not None else "MISSING_POST_HORIZON_SAME_TICKER_WITNESS"

    counts[reason]+=1
    horizons[(int(state["horizon_seconds"]),reason)]+=1

    print(
        f"[{i:02d}]",
        state["ticker"],
        "H=",state["horizon_seconds"],
        "REASON=",reason,
    )

print("="*92)
print("MATURE_ROWS_PROBED=",len(rows))

for key,value in counts.items():
    print(key,"=",value)

print("HORIZON_BREAKDOWN")
for key,value in sorted(horizons.items()):
    print(key,"=",value)

print("EXECUTION_AUTHORITY=FALSE")