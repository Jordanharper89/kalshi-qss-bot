from __future__ import annotations
import json,time
from pathlib import Path

import mtr_134_new_inventory_bidirectional_protected_sweep as m134

SRC=Path("mtr_135_multi_dlmm_inventory_expansion.json")
OUT=Path("mtr_136_alternative_dlmm_protected_sweep.json")

SIZES=(1_000_000,2_500_000,5_000_000,7_500_000,10_000_000)

def main():
    print("[MTR-136] START",flush=True)
    print("[SCOPE] previously untested alternative DLMM pools only",flush=True)
    print("[DIRECTIONS] PUMP_TO_METEORA + METEORA_TO_PUMP",flush=True)
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

    if not SRC.is_file():
        raise RuntimeError("MTR135_REPORT_MISSING")

    src=json.loads(SRC.read_text(encoding="utf-8"))

    routes=[
        x for x in (src.get("rows") or [])
        if not x.get("was_prior_pool")
    ]

    if not routes:
        raise RuntimeError("MTR135_NO_ALTERNATIVE_ROUTES")

    results=[]
    positives=[]
    holds=0

    for n,row in enumerate(routes,1):
        print(
            "[MTR136_PAIR] %d/%d token=%s pool=%s score=%.2f"
            %(
                n,len(routes),
                row["token"][:10],
                row["meteora_pool"][:12],
                float(row.get("score") or 0),
            ),
            flush=True,
        )

        for start in SIZES:
            for fn in (m134.p2m,m134.m2p):
                try:
                    x=fn(m134.m119.PUBLIC_USER,row,start)

                    x.update({
                        "token":row["token"],
                        "pump_pool":row["pump_pool"],
                        "meteora_pool":row["meteora_pool"],
                        "meteora_score":float(row.get("score") or 0),
                        "requested_size_lamports":start,
                        "requested_size_sol":start/1e9,
                    })

                    results.append(x)

                    print(
                        "[MTR136_ROUTE] token=%s pool=%s dir=%s "
                        "size=%.4f net=%+d bps=%+.2f cap_ok=%s"
                        %(
                            row["token"][:10],
                            row["meteora_pool"][:10],
                            x["direction"],
                            start/1e9,
                            x["floor_net"],
                            x["floor_bps"],
                            x["cap_ok"],
                        ),
                        flush=True,
                    )

                    if x["floor_net"]>0 and x["cap_ok"]:
                        positives.append(x)

                        print(
                            "[MTR136_POSITIVE] token=%s pool=%s dir=%s "
                            "size=%.4f net=%+d bps=%+.2f"
                            %(
                                row["token"][:10],
                                row["meteora_pool"][:10],
                                x["direction"],
                                start/1e9,
                                x["floor_net"],
                                x["floor_bps"],
                            ),
                            flush=True,
                        )

                except Exception as e:
                    holds+=1

                    print(
                        "[MTR136_HOLD] token=%s pool=%s size=%.4f "
                        "lane=%s error=%s:%s"
                        %(
                            row["token"][:10],
                            row["meteora_pool"][:10],
                            start/1e9,
                            fn.__name__,
                            type(e).__name__,
                            str(e)[:120],
                        ),
                        flush=True,
                    )

                time.sleep(.08)

    results.sort(
        key=lambda x:x["floor_net"],
        reverse=True,
    )

    positives.sort(
        key=lambda x:x["floor_net"],
        reverse=True,
    )

    out={
        "mtr":"MTR-136",
        "alternative_routes":len(routes),
        "evaluations":len(results),
        "holds":holds,
        "protected_positive_count":len(positives),
        "best_overall":results[0] if results else None,
        "best_positive":positives[0] if positives else None,
        "positives":positives,
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }

    OUT.write_text(
        json.dumps(out,indent=2,sort_keys=True,default=str),
        encoding="utf-8",
    )

    print(
        "[SUMMARY] alternatives=%d evaluations=%d holds=%d "
        "protected_positive=%d"
        %(
            len(routes),
            len(results),
            holds,
            len(positives),
        ),
        flush=True,
    )

    if results:
        b=results[0]

        print(
            "[BEST_OVERALL] token=%s pool=%s dir=%s "
            "size=%.4f net=%+d bps=%+.2f"
            %(
                b["token"][:10],
                b["meteora_pool"][:10],
                b["direction"],
                b["requested_size_sol"],
                b["floor_net"],
                b["floor_bps"],
            ),
            flush=True,
        )

    if positives:
        b=positives[0]

        print(
            "[BEST_POSITIVE] token=%s pool=%s dir=%s "
            "size=%.4f net=%+d bps=%+.2f"
            %(
                b["token"][:10],
                b["meteora_pool"][:10],
                b["direction"],
                b["requested_size_sol"],
                b["floor_net"],
                b["floor_bps"],
            ),
            flush=True,
        )

        print(
            "[RESULT] ALTERNATIVE_DLMM_PROTECTED_PROFIT_FOUND",
            flush=True,
        )

    else:
        print(
            "[RESULT] ALTERNATIVE_DLMM_NO_PROTECTED_PROFIT",
            flush=True,
        )

    print("[OUTPUT] "+str(OUT))
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[MTR-136] COMPLETE")

if __name__=="__main__":
    main()
