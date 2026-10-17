from pathlib import Path

p=Path("mtr_135_multi_dlmm_inventory_expansion.py")

p.write_text(r'''from __future__ import annotations
import json,time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import (
    crosslisted as cross
)
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import (
    core as c
)

SRC=Path("mtr_133_broad_exact_replenishment_probe.json")
OUT=Path("mtr_135_multi_dlmm_inventory_expansion.json")

def main():
    print("[MTR-135] START",flush=True)
    print("[PURPOSE] expand each new token across every exact WSOL DLMM pool",flush=True)
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

    if not SRC.is_file():
        raise RuntimeError("MTR133_REPORT_MISSING")

    src=json.loads(SRC.read_text(encoding="utf-8"))
    bindings=src.get("rows") or []

    if not bindings:
        raise RuntimeError("MTR133_BINDINGS_EMPTY")

    expanded=[]
    token_rows=[]

    for n,row in enumerate(bindings,1):
        token=str(row["token"])
        pump=str(row["pump_pool"])
        prior=str(row["meteora_pool"])

        try:
            matches=cross.meteora_matches(token)
        except Exception as e:
            print(
                "[MTR135_HOLD] token=%s error=%s:%s"
                %(token[:10],type(e).__name__,str(e)[:160]),
                flush=True,
            )
            token_rows.append({
                "token":token,
                "pump_pool":pump,
                "prior_pool":prior,
                "pool_count":0,
                "error":type(e).__name__+":"+str(e),
            })
            continue

        good=[]

        for meta in matches:
            try:
                addr=str(meta["address"])

                if {
                    str(meta.get("token_x")),
                    str(meta.get("token_y")),
                } != {token,c.WSOL}:
                    continue

                c.account(addr)

                x={
                    "token":token,
                    "pump_pool":pump,
                    "meteora_pool":addr,
                    "meteora_meta":meta,
                    "score":float(meta.get("score") or 0),
                    "was_prior_pool":addr==prior,
                }

                good.append(x)
                expanded.append(x)

            except Exception as e:
                print(
                    "[MTR135_POOL_SKIP] token=%s pool=%s error=%s:%s"
                    %(token[:10],str(meta.get("address"))[:12],
                      type(e).__name__,str(e)[:100]),
                    flush=True,
                )

        good.sort(key=lambda x:x["score"],reverse=True)

        print(
            "[MTR135_TOKEN] %d/%d token=%s pools=%d alternatives=%d prior_present=%s"
            %(
                n,len(bindings),token[:10],len(good),
                len([x for x in good if not x["was_prior_pool"]]),
                any(x["was_prior_pool"] for x in good),
            ),
            flush=True,
        )

        for rank,x in enumerate(good,1):
            print(
                "[MTR135_POOL] token=%s rank=%d pool=%s score=%.2f prior=%s"
                %(token[:10],rank,x["meteora_pool"][:12],
                  x["score"],x["was_prior_pool"]),
                flush=True,
            )

        token_rows.append({
            "token":token,
            "pump_pool":pump,
            "prior_pool":prior,
            "pool_count":len(good),
            "alternative_count":
                len([x for x in good if not x["was_prior_pool"]]),
        })

        time.sleep(.20)

    unique={
        (x["token"],x["pump_pool"],x["meteora_pool"]):x
        for x in expanded
    }
    expanded=list(unique.values())

    alternatives=[
        x for x in expanded
        if not x["was_prior_pool"]
    ]

    out={
        "mtr":"MTR-135",
        "input_tokens":len(bindings),
        "expanded_exact_routes":len(expanded),
        "alternative_routes":len(alternatives),
        "tokens_with_multiple_pools":
            sum(1 for x in token_rows if x.get("pool_count",0)>1),
        "token_rows":token_rows,
        "rows":expanded,
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }

    OUT.write_text(
        json.dumps(out,indent=2,sort_keys=True,default=str),
        encoding="utf-8",
    )

    print(
        "[SUMMARY] tokens=%d exact_routes=%d alternatives=%d multi_pool_tokens=%d"
        %(
            out["input_tokens"],
            out["expanded_exact_routes"],
            out["alternative_routes"],
            out["tokens_with_multiple_pools"],
        ),
        flush=True,
    )

    if alternatives:
        print("[RESULT] MULTI_DLMM_ALTERNATIVE_INVENTORY_FOUND",flush=True)
    else:
        print("[RESULT] NO_MULTI_DLMM_ALTERNATIVES_FOUND",flush=True)

    print("[OUTPUT] "+str(OUT))
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[MTR-135] COMPLETE")

if __name__=="__main__":
    main()
''',encoding="utf-8")

print("[BUILD] wrote",p)
print("[BUILD] multi-DLMM exact inventory expansion")
print("[SCOPE] inventory only; frozen scanner unchanged; no key; no send")