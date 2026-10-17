from __future__ import annotations
import json,os,shutil,subprocess,time
from pathlib import Path

import mtr_118_target_only_24_route_scale as b118
import mtr_119_canonical_alt_atomic_preflight as m119

from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
from qseries_v2.solana_live_execution import qarb_097_official_meteora_sdk_executor as q97

OUT=Path("mtr_131_reverse_official_bound_economics.json")
START=10_000_000
ROOT=Path("qseries_v2/oracle_strategy_intelligence/solana_money/qsb059d_pump_native")

def retry(fn,label):
    last=None
    for n in range(1,6):
        try:
            return fn()
        except Exception as e:
            last=e
            if "429" not in str(e):
                raise
            d=min(.75*(2**(n-1)),6.0)
            print("[MTR131_429] stage=%s attempt=%d sleep=%.2f"%(label,n,d),flush=True)
            time.sleep(d)
    raise last

def pump_sell(user,pool,base_amount):
    node=shutil.which("node")
    if not node:
        raise RuntimeError("MTR131_NODE_MISSING")

    req={
        "rpc":os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com"),
        "user":str(user),
        "pool":str(pool),
        "slippagePct":float(m119.sae.q87.las.q59.SLIPPAGE_BPS)/100.0,
        "baseAmounts":[int(base_amount),int(base_amount)],
        "pumpProgram":m119.sae.q87.c.PUMP,
    }

    z=subprocess.run(
        [node,"oracle012_pump_sell.mjs"],
        cwd=ROOT,
        input=json.dumps(req),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=45,
    )

    if z.returncode!=0:
        raise RuntimeError("MTR131_PUMP_SELL_NODE:"+z.stderr[-2000:])

    j=json.loads(z.stdout.strip().splitlines()[-1])
    if not j.get("ok"):
        raise RuntimeError("MTR131_PUMP_SELL:"+str(j.get("reason")))

    first=j["first"]
    return int(first["baseIn"]),int(first["minQuoteOut"])

def main():
    print("[MTR-131] START",flush=True)
    print("[DIRECTION] METEORA_TO_PUMP",flush=True)
    print("[SIZE] 0.010 SOL",flush=True)
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

        try:
            mb=retry(
                lambda:q97.native_meteora_swap_ixs(
                    m119.PUBLIC_USER,
                    meteora,
                    m119.sae.q87.c.WSOL,
                    token,
                    START,
                ),
                "METEORA",
            )

            token_floor=int(mb["min_out"])

            base_in,pump_floor=retry(
                lambda:pump_sell(
                    m119.PUBLIC_USER,
                    pump,
                    token_floor,
                ),
                "PUMP",
            )

            if base_in!=token_floor:
                raise RuntimeError("MTR131_BASE_BINDING_DRIFT")

            floor_net=pump_floor-START
            floor_bps=floor_net/START*10000.0

            row={
                "token":token,
                "pump_pool":pump,
                "meteora_pool":meteora,
                "meteora_quote_out":int(mb["quoted_out"]),
                "meteora_min_base":token_floor,
                "pump_min_quote":pump_floor,
                "floor_net":floor_net,
                "floor_bps":floor_bps,
            }
            rows.append(row)

            print(
                "[MTR131_ROUTE] %d token=%s meteora_min=%d "
                "pump_min=%d floor_net=%+d floor_bps=%+.2f"
                %(n,token[:10],token_floor,pump_floor,floor_net,floor_bps),
                flush=True,
            )

            if floor_net>0:
                positives.append(row)
                print(
                    "[MTR131_POSITIVE] token=%s floor_bps=%+.2f floor_net=%+d"
                    %(token[:10],floor_bps,floor_net),
                    flush=True,
                )

        except Exception as e:
            print(
                "[MTR131_HOLD] token=%s error=%s"
                %(token[:10],type(e).__name__+":"+str(e)),
                flush=True,
            )

        time.sleep(.15)

    positives.sort(key=lambda x:x["floor_net"],reverse=True)

    out={
        "mtr":"MTR-131",
        "direction":"METEORA_TO_PUMP",
        "start_lamports":START,
        "routes_checked":len(rows),
        "protected_positive_count":len(positives),
        "best":positives[0] if positives else None,
        "positives":positives,
        "rows":rows,
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }

    OUT.write_text(
        json.dumps(out,indent=2,sort_keys=True,default=str),
        encoding="utf-8",
    )

    print(
        "[SUMMARY] routes_checked=%d protected_positive=%d"
        %(len(rows),len(positives)),
        flush=True,
    )

    if positives:
        b=positives[0]
        print(
            "[BEST] token=%s floor_net=%+d floor_bps=%+.2f"
            %(b["token"][:10],b["floor_net"],b["floor_bps"]),
            flush=True,
        )
        print(
            "[RESULT] REVERSE_OFFICIAL_PROTECTED_PROFIT_FOUND",
            flush=True,
        )
    else:
        print(
            "[RESULT] NO_REVERSE_PROTECTED_PROFIT_AT_010_NOW",
            flush=True,
        )

    print("[OUTPUT] "+str(OUT))
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[MTR-131] COMPLETE")

if __name__=="__main__":
    main()
