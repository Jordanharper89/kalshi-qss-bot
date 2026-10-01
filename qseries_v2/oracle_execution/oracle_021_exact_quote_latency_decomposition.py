from __future__ import annotations
import argparse,json,time,statistics
from pathlib import Path

from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
from qseries_v2.oracle_execution import oracle_019_venue_native_reserve_feed_cutover as q19
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False
SIZES=(0.001,0.010,0.050)

def ms(fn,*a,**k):
    t=time.perf_counter_ns()
    r=fn(*a,**k)
    return r,(time.perf_counter_ns()-t)/1e6

def pct(xs,p):
    if not xs:return None
    s=sorted(xs)
    return s[min(len(s)-1,int(len(s)*p))]

def first_pair(root):
    state=q19.persistent.m.prepare(Path(root))
    pairs=list(state.get("pairs") or [])
    if not pairs: raise RuntimeError("NO_LIVE_PAIR_STATE")
    return pairs[0]

def snap(pair):
    return {
        "token":pair.token,
        "pump_pool":pair.pump_pool,
        "meteora":{
            "address":pair.meteora_pool,
            "token_x":pair.token_x,
            "token_y":pair.token_y,
            "decimals_x":pair.decimals_x,
            "decimals_y":pair.decimals_y,
        },
        "dlmm_state":pair.dlmm_state,
        "pump_base_reserve":int(pair.pump_base_reserve),
        "pump_quote_reserve":int(pair.pump_quote_reserve),
    }

def run(iterations=3):
    pair=first_pair(Path.cwd())
    s=snap(pair)
    w=q18.worker()
    w.warm(pair.pump_pool)

    rows=[]
    print("[ORACLE-021] EXACT QUOTE LATENCY DECOMPOSITION",flush=True)
    print("[PAIR] token=%s pump=%s meteora=%s"%(pair.token[:12],pair.pump_pool[:12],pair.meteora_pool[:12]),flush=True)
    print("[PRIVATE_KEY] not required",flush=True)
    print("[BROADCAST] disabled",flush=True)

    for size in SIZES:
        start=int(size*1e9)
        for i in range(int(iterations)):
            pump_buy,pb_ms=ms(w.buy,s,start)
            fwd_token=q18.token_net(pair.token,int(pump_buy["baseOut"]))
            meteora_sell,ms_ms=ms(core.dlmm_quote_snapshot,s,fwd_token,pair.token)

            meteora_buy,mb_ms=ms(core.dlmm_quote_snapshot,s,start,core.WSOL)
            reverse_token=q18.token_net(pair.token,int(meteora_buy["raw_out"]))
            pump_sell,ps_ms=ms(w.sell,s,reverse_token)

            row={
                "size_sol":size,
                "iteration":i+1,
                "pump_buy_ms":pb_ms,
                "meteora_sell_ms":ms_ms,
                "meteora_buy_ms":mb_ms,
                "pump_sell_ms":ps_ms,
                "forward_total_ms":pb_ms+ms_ms,
                "reverse_total_ms":mb_ms+ps_ms,
                "forward_end":int(meteora_sell["raw_out"]),
                "reverse_end":int(pump_sell["uiQuote"]),
            }
            rows.append(row)
            print(
                "[ORACLE021_POINT] size=%.3f i=%d pump_buy_ms=%.3f meteora_sell_ms=%.3f "
                "meteora_buy_ms=%.3f pump_sell_ms=%.3f"
                %(size,i+1,pb_ms,ms_ms,mb_ms,ps_ms),
                flush=True,
            )

    summary={}
    for key in ("pump_buy_ms","pump_sell_ms","meteora_buy_ms","meteora_sell_ms","forward_total_ms","reverse_total_ms"):
        vals=[float(r[key]) for r in rows]
        summary[key]={"p50":statistics.median(vals),"p95":pct(vals,.95),"max":max(vals)}

    payload={
        "oracle_build":"ORACLE-021",
        "pair":{"token":pair.token,"pump_pool":pair.pump_pool,"meteora_pool":pair.meteora_pool},
        "iterations":int(iterations),
        "rows":rows,
        "summary":summary,
        "execution_authority":False,
        "paper_only":True,
        "real_money_moved":False,
        "broadcast":False,
    }
    out=Path("runtime_state/oracle/oracle_live_execution/oracle_021_exact_quote_latency_decomposition.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

    print("[ORACLE021_SUMMARY] "+json.dumps(summary,sort_keys=True),flush=True)
    print("[REPORT] %s"%out,flush=True)
    print("[BROADCAST] disabled",flush=True)

    if getattr(q18,"_worker",None) is not None:
        q18._worker.close()
        q18._worker=None
    return 0

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--iterations",type=int,default=3)
    a=ap.parse_args(argv)
    return run(a.iterations)

if __name__=="__main__":
    raise SystemExit(main())
