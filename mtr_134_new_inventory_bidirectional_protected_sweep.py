from __future__ import annotations
import base64,json,struct,time
from pathlib import Path

import mtr_119_canonical_alt_atomic_preflight as m119
import mtr_131_reverse_official_bound_economics as m131

from qseries_v2.solana_live_execution import (
    qarb_097_official_meteora_sdk_executor as q97
)

SRC=Path("mtr_133_broad_exact_replenishment_probe.json")
OUT=Path("mtr_134_new_inventory_bidirectional_protected_sweep.json")

SIZES=(1_000_000,2_500_000,5_000_000,7_500_000,10_000_000)
LIVE_CAP=10_000_000

def p2m(user,row,start):
    ixs,q=m131.retry(
        lambda:m119.sae.q87.las.q59.native_pump_buy_ixs(
            user,row["pump_pool"],start
        ),
        "PUMP_BUY",
    )

    px=[x for x in ixs if x.get("programId")==m119.sae.q87.c.PUMP]
    if len(px)!=1:
        raise RuntimeError("MTR134_PUMP_BUY_COUNT:"+str(len(px)))

    raw=base64.b64decode(px[0].get("data") or "")
    if len(raw)<24:
        raise RuntimeError("MTR134_PUMP_BUY_DATA_SHORT")

    disc=raw[:8]

    if disc==m119.sae.BUY_DISC:
        base_out=struct.unpack("<Q",raw[8:16])[0]
        capital=struct.unpack("<Q",raw[16:24])[0]
        family="BUY"
    elif disc==m119.sae.BUY_EXACT_QUOTE_IN_DISC:
        capital=struct.unpack("<Q",raw[8:16])[0]
        base_out=struct.unpack("<Q",raw[16:24])[0]
        family="BUY_EXACT_QUOTE_IN"
    else:
        raise RuntimeError("MTR134_UNKNOWN_BUY:"+disc.hex())

    mb=m131.retry(
        lambda:q97.native_meteora_swap_ixs(
            user,row["meteora_pool"],row["token"],
            m119.sae.q87.c.WSOL,base_out
        ),
        "METEORA_SELL",
    )

    end=int(mb["min_out"])
    net=end-capital

    return {
        "direction":"PUMP_TO_METEORA",
        "family":family,
        "capital_lamports":capital,
        "intermediate_floor":base_out,
        "end_floor":end,
        "floor_net":net,
        "floor_bps":net/capital*10000.0,
        "cap_ok":capital<=LIVE_CAP,
        "pump_quote":int(q),
    }

def m2p(user,row,start):
    mb=m131.retry(
        lambda:q97.native_meteora_swap_ixs(
            user,row["meteora_pool"],
            m119.sae.q87.c.WSOL,row["token"],start
        ),
        "METEORA_BUY",
    )

    base_floor=int(mb["min_out"])

    base_in,end=m131.retry(
        lambda:m131.pump_sell(
            user,row["pump_pool"],base_floor
        ),
        "PUMP_SELL",
    )

    if base_in!=base_floor:
        raise RuntimeError("MTR134_REVERSE_BINDING_DRIFT")

    net=end-start

    return {
        "direction":"METEORA_TO_PUMP",
        "family":"SELL_BASE_INPUT",
        "capital_lamports":start,
        "intermediate_floor":base_floor,
        "end_floor":end,
        "floor_net":net,
        "floor_bps":net/start*10000.0,
        "cap_ok":start<=LIVE_CAP,
        "meteora_quote":int(mb["quoted_out"]),
    }

def main():
    print("[MTR-134] START",flush=True)
    print("[SCOPE] new MTR-133 inventory only; both directions",flush=True)
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

    if not SRC.is_file():
        raise RuntimeError("MTR133_REPORT_MISSING")

    rows=json.loads(SRC.read_text(encoding="utf-8")).get("rows") or []

    if not rows:
        raise RuntimeError("MTR133_NO_NEW_BINDINGS")

    results=[]
    positives=[]

    for n,row in enumerate(rows,1):
        for start in SIZES:
            for fn in (p2m,m2p):
                try:
                    x=fn(m119.PUBLIC_USER,row,start)
                    x.update({
                        "token":row["token"],
                        "pump_pool":row["pump_pool"],
                        "meteora_pool":row["meteora_pool"],
                        "requested_size_lamports":start,
                        "requested_size_sol":start/1e9,
                    })
                    results.append(x)

                    print(
                        "[MTR134_ROUTE] pair=%d token=%s dir=%s size=%.4f "
                        "capital=%d net=%+d bps=%+.2f cap_ok=%s"
                        %(n,row["token"][:10],x["direction"],start/1e9,
                          x["capital_lamports"],x["floor_net"],
                          x["floor_bps"],x["cap_ok"]),
                        flush=True,
                    )

                    if x["floor_net"]>0 and x["cap_ok"]:
                        positives.append(x)
                        print(
                            "[MTR134_POSITIVE] token=%s dir=%s size=%.4f "
                            "net=%+d bps=%+.2f"
                            %(row["token"][:10],x["direction"],
                              start/1e9,x["floor_net"],x["floor_bps"]),
                            flush=True,
                        )

                except Exception as e:
                    print(
                        "[MTR134_HOLD] token=%s size=%.4f lane=%s error=%s:%s"
                        %(row["token"][:10],start/1e9,fn.__name__,
                          type(e).__name__,str(e)[:120]),
                        flush=True,
                    )

                time.sleep(.08)

    results.sort(key=lambda x:x["floor_net"],reverse=True)
    positives.sort(key=lambda x:x["floor_net"],reverse=True)

    out={
        "mtr":"MTR-134",
        "input_bindings":len(rows),
        "evaluations":len(results),
        "protected_positive_count":len(positives),
        "best_overall":results[0] if results else None,
        "best_positive":positives[0] if positives else None,
        "positives":positives,
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }

    OUT.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")

    print(
        "[SUMMARY] bindings=%d evaluations=%d protected_positive=%d"
        %(len(rows),len(results),len(positives)),
        flush=True,
    )

    if results:
        b=results[0]
        print(
            "[BEST_OVERALL] token=%s dir=%s size=%.4f net=%+d bps=%+.2f"
            %(b["token"][:10],b["direction"],b["requested_size_sol"],
              b["floor_net"],b["floor_bps"]),
            flush=True,
        )

    if positives:
        b=positives[0]
        print(
            "[BEST_POSITIVE] token=%s dir=%s size=%.4f net=%+d bps=%+.2f"
            %(b["token"][:10],b["direction"],b["requested_size_sol"],
              b["floor_net"],b["floor_bps"]),
            flush=True,
        )
        print("[RESULT] NEW_INVENTORY_PROTECTED_PROFIT_FOUND",flush=True)
    else:
        print("[RESULT] NEW_INVENTORY_NO_PROTECTED_PROFIT",flush=True)

    print("[OUTPUT] "+str(OUT))
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[MTR-134] COMPLETE")

if __name__=="__main__":
    main()
