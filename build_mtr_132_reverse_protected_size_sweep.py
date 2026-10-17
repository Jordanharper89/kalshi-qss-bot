from pathlib import Path

p=Path("mtr_132_reverse_protected_size_sweep.py")

p.write_text(r'''from __future__ import annotations
import json,time
from pathlib import Path

import mtr_118_target_only_24_route_scale as b118
import mtr_119_canonical_alt_atomic_preflight as m119
import mtr_131_reverse_official_bound_economics as m131

from qseries_v2.oracle_execution import (
    oracle_025_single_hydration_exact_live_reuse as q25
)
from qseries_v2.solana_live_execution import (
    qarb_097_official_meteora_sdk_executor as q97
)

OUT=Path("mtr_132_reverse_protected_size_sweep.json")

SIZES=(
    1_000_000,
    2_500_000,
    5_000_000,
    7_500_000,
    10_000_000,
)

def main():
    print("[MTR-132] START",flush=True)
    print("[DIRECTION] METEORA_TO_PUMP",flush=True)
    print("[SIZES_SOL] 0.001,0.0025,0.005,0.0075,0.010",flush=True)
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

    state,_=b118.prepare_once(Path.cwd())
    q25.bind_cached_state(state)

    rows=[]
    positives=[]

    for n,pair in enumerate(state["pairs"],1):
        token=str(pair.token)
        pump=str(pair.pump_pool)
        meteora=str(pair.meteora_pool)

        for start in SIZES:
            try:
                mb=m131.retry(
                    lambda:q97.native_meteora_swap_ixs(
                        m119.PUBLIC_USER,
                        meteora,
                        m119.sae.q87.c.WSOL,
                        token,
                        start,
                    ),
                    "METEORA",
                )

                token_floor=int(mb["min_out"])

                base_in,pump_floor=m131.retry(
                    lambda:m131.pump_sell(
                        m119.PUBLIC_USER,
                        pump,
                        token_floor,
                    ),
                    "PUMP",
                )

                if base_in!=token_floor:
                    raise RuntimeError(
                        "MTR132_BASE_BINDING_DRIFT"
                    )

                floor_net=pump_floor-start
                floor_bps=floor_net/start*10000.0

                row={
                    "token":token,
                    "pump_pool":pump,
                    "meteora_pool":meteora,
                    "size_lamports":start,
                    "size_sol":start/1e9,
                    "meteora_min_base":token_floor,
                    "pump_min_quote":pump_floor,
                    "floor_net":floor_net,
                    "floor_bps":floor_bps,
                }

                rows.append(row)

                print(
                    "[MTR132_ROUTE] pair=%d token=%s size=%.4f "
                    "floor_net=%+d floor_bps=%+.2f"
                    %(
                        n,
                        token[:10],
                        start/1e9,
                        floor_net,
                        floor_bps,
                    ),
                    flush=True,
                )

                if floor_net>0:
                    positives.append(row)
                    print(
                        "[MTR132_POSITIVE] token=%s size=%.4f "
                        "floor_net=%+d floor_bps=%+.2f"
                        %(
                            token[:10],
                            start/1e9,
                            floor_net,
                            floor_bps,
                        ),
                        flush=True,
                    )

            except Exception as exc:
                print(
                    "[MTR132_HOLD] token=%s size=%.4f error=%s"
                    %(
                        token[:10],
                        start/1e9,
                        type(exc).__name__+":"+str(exc),
                    ),
                    flush=True,
                )

            time.sleep(.10)

    rows.sort(
        key=lambda x:x["floor_net"],
        reverse=True,
    )
    positives.sort(
        key=lambda x:x["floor_net"],
        reverse=True,
    )

    out={
        "mtr":"MTR-132",
        "direction":"METEORA_TO_PUMP",
        "sizes_lamports":list(SIZES),
        "rows_checked":len(rows),
        "positive_count":len(positives),
        "best_overall":rows[0] if rows else None,
        "best_positive":positives[0] if positives else None,
        "positives":positives,
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }

    OUT.write_text(
        json.dumps(
            out,
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )

    print(
        "[SUMMARY] rows=%d protected_positive=%d"
        %(len(rows),len(positives)),
        flush=True,
    )

    if rows:
        b=rows[0]
        print(
            "[BEST_OVERALL] token=%s size=%.4f "
            "floor_net=%+d floor_bps=%+.2f"
            %(
                b["token"][:10],
                b["size_sol"],
                b["floor_net"],
                b["floor_bps"],
            ),
            flush=True,
        )

    if positives:
        b=positives[0]
        print(
            "[BEST_POSITIVE] token=%s size=%.4f "
            "floor_net=%+d floor_bps=%+.2f"
            %(
                b["token"][:10],
                b["size_sol"],
                b["floor_net"],
                b["floor_bps"],
            ),
            flush=True,
        )
        print(
            "[RESULT] REVERSE_PROTECTED_SIZE_PROFIT_FOUND",
            flush=True,
        )
    else:
        print(
            "[RESULT] NO_REVERSE_PROTECTED_PROFIT_ANY_TESTED_SIZE",
            flush=True,
        )

    print("[OUTPUT] "+str(OUT))
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[MTR-132] COMPLETE")

if __name__=="__main__":
    main()
''',encoding="utf-8")

print("[BUILD] wrote",p)
print("[BUILD] official reverse protected size sweep")
print("[SCOPE] economics only; no transaction; no key; no send")