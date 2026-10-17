from pathlib import Path

P=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/alt_manager.py"
)

s=P.read_text(encoding="utf-8")

old='''        rows=r.q18.exact_snapshot_opportunities(snap,0.001)
        opp=next((x for x in rows if x["direction"]=="PUMP_TO_METEORA"),None)
        if opp is None:
            continue
'''

new='''        try:
            rows=r.q18.exact_snapshot_opportunities(
                snap,
                0.001
            )
        except RuntimeError as exc:
            if str(exc)=="DLMM_PARTIAL":
                print(
                    "[CANONICAL_ALT_PAIR_SKIP] "
                    "token=%s reason=DLMM_PARTIAL"
                    %token[:10],
                    flush=True,
                )
                continue
            raise

        opp=next(
            (
                x for x in rows
                if x["direction"]=="PUMP_TO_METEORA"
            ),
            None
        )

        if opp is None:
            continue
'''

if old not in s:
    raise RuntimeError(
        "ALT_MANAGER_DLMM_SEAM_NOT_FOUND"
    )

s=s.replace(old,new,1)

P.write_text(
    s,
    encoding="utf-8"
)

print("[PASS] canonical ALT manager DLMM_PARTIAL skip installed")
print("[BEHAVIOR] incomplete DLMM pair skipped; next ready pair attempted")
print("[BROADCAST] default remains disabled")