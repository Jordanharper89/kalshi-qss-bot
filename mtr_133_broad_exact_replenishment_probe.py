from __future__ import annotations
import json,time
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine as eng
)
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    qarb_044_dynamic_exact_crossvenue_binding as q44
)

OUT=Path("mtr_133_broad_exact_replenishment_probe.json")
OLD=Path("mtr_131_reverse_official_bound_economics.json")
DISCOVERY_SECONDS=60.0
MAX_VERIFY=96

def verify_retry(token):
    last=None
    for n in range(1,5):
        try:
            return q44.verify(token)
        except Exception as e:
            last=e
            s=str(e)
            if "429" not in s and "Too Many Requests" not in s:
                raise
            d=min(.75*(2**(n-1)),6.0)
            print(
                "[MTR133_429] token=%s attempt=%d sleep=%.2f"
                %(token[:10],n,d),
                flush=True,
            )
            time.sleep(d)
    raise last

def main():
    print("[MTR-133] START",flush=True)
    print("[PURPOSE] broaden replenishment beyond retired 24-route set",flush=True)
    print("[SOURCES] MRIYA + PUMPSWAP_PROGRAM",flush=True)
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

    root=Path.cwd()

    old_tokens=set()
    if OLD.is_file():
        j=json.loads(OLD.read_text(encoding="utf-8"))
        old_tokens={
            str(x.get("token"))
            for x in (j.get("rows") or [])
            if x.get("token")
        }

    before=eng._merged_discovery_registry()
    before_tokens=set((before.get("tokens") or {}).keys())

    print(
        "[BEFORE] merged_tokens=%d retired_inventory_tokens=%d"
        %(len(before_tokens),len(old_tokens)),
        flush=True,
    )

    eng._ensure_oracle_discovery(root,DISCOVERY_SECONDS+10)
    eng._ensure_broad_discovery(root,DISCOVERY_SECONDS+10)

    started=time.monotonic()
    while time.monotonic()-started<DISCOVERY_SECONDS:
        time.sleep(10)
        reg=eng._merged_discovery_registry()
        print(
            "[DISCOVERY] elapsed=%.0fs merged_tokens=%d"
            %(time.monotonic()-started,len(reg.get("tokens") or {})),
            flush=True,
        )

    eng._stop_oracle_discovery()

    merged=eng._merged_discovery_registry()
    tokens=merged.get("tokens") or {}

    items=list(tokens.items())
    items.sort(
        key=lambda kv:(
            -float(kv[1].get("last_seen_epoch",0) or 0),
            -int(kv[1].get("touches",0) or 0),
        )
    )

    fresh=[
        (t,info) for t,info in items
        if t not in old_tokens
    ]

    rows=[]
    fails=[]
    attempts=0

    for token,info in fresh:
        if attempts>=MAX_VERIFY:
            break

        attempts+=1

        try:
            pump,meta=verify_retry(token)

            row={
                "token":token,
                "pump_pool":pump,
                "meteora_pool":meta["address"],
                "meteora_meta":meta,
                "last_seen_epoch":info.get("last_seen_epoch"),
                "touches":info.get("touches"),
                "sources":info.get("sources") or [],
            }
            rows.append(row)

            print(
                "[MTR133_NEW_EXACT_BIND] token=%s pump=%s meteora=%s sources=%s"
                %(
                    token[:10],
                    pump[:12],
                    str(meta["address"])[:12],
                    ",".join(row["sources"]),
                ),
                flush=True,
            )

        except Exception as e:
            fails.append({
                "token":token,
                "error":type(e).__name__+":"+str(e),
            })
            print(
                "[MTR133_SKIP] token=%s error=%s:%s"
                %(token[:10],type(e).__name__,str(e)[:100]),
                flush=True,
            )

        time.sleep(.15)

    after_tokens=set(tokens.keys())

    out={
        "mtr":"MTR-133",
        "merged_before":len(before_tokens),
        "merged_after":len(after_tokens),
        "new_discovered_tokens":len(after_tokens-before_tokens),
        "retired_inventory_tokens":len(old_tokens),
        "verify_attempts":attempts,
        "new_exact_bindings":len(rows),
        "rows":rows,
        "failures":fails,
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }

    OUT.write_text(
        json.dumps(out,indent=2,sort_keys=True,default=str),
        encoding="utf-8",
    )

    print(
        "[SUMMARY] merged_before=%d merged_after=%d discovered_new=%d "
        "verified=%d new_exact_bindings=%d"
        %(
            out["merged_before"],
            out["merged_after"],
            out["new_discovered_tokens"],
            attempts,
            len(rows),
        ),
        flush=True,
    )

    if rows:
        print("[RESULT] BROAD_NEW_EXACT_INVENTORY_FOUND",flush=True)
    else:
        print("[RESULT] BROAD_DISCOVERY_NO_NEW_EXACT_BINDINGS",flush=True)

    print("[OUTPUT] "+str(OUT))
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[MTR-133] COMPLETE")

if __name__=="__main__":
    main()
