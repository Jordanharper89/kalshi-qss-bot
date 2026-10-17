from __future__ import annotations
import json,time,urllib.error
from pathlib import Path

from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b_existing_runtime_multidex_cutover as q60b

META=Path("mtr_115_multi_link_meta.json")
OUT=Path("mtr_116_fast_gate_route_queue_hardening.json")
ORIG=q60b._ORIG_PREPARE
FAST=(0.001,0.005,0.010,0.020,0.030)
ST={"pairs":0,"tokens":0,"shared":0,"max_fanout":0,
    "fanout_events":0,"fanout_submissions":0,"hydrate_retries":0}

def dec(x):
    raw,_=c.account(x)
    if len(raw)<45: raise RuntimeError("MINT_SHORT")
    return int(raw[44])

def hydrate_once(r):
    raw,_=c.account(r["pump_pool"]);pp=c.decode_pump_pool(raw)
    if pp["quote_mint"]!=c.WSOL: raise RuntimeError("PUMP_NOT_WSOL")
    br,_=c.account(pp["base_vault"]);qr,_=c.account(pp["quote_vault"])
    lb,_=c.account(r["meteora_pool"]);arrays=c.dlmm_arrays(r["meteora_pool"])
    p=pd.PairState(
        r["base_mint"],r["pump_pool"],r["meteora_pool"],
        r["token_x"],r["token_y"],dec(r["token_x"]),dec(r["token_y"]),
        pp["base_vault"],pp["quote_vault"],
        pd._token_amount_from_raw(br),pd._token_amount_from_raw(qr),
        lb,list(arrays),None
    )
    p.dlmm_state=pd._build_dlmm_state(p)
    return p

def hydrate(r):
    last=None
    for attempt in range(1,9):
        try:
            return hydrate_once(r)
        except urllib.error.HTTPError as e:
            last=e
            if getattr(e,"code",None)!=429: raise
        except Exception as e:
            last=e
            if "429" not in str(e): raise
        ST["hydrate_retries"]+=1
        delay=min(.75*(2**(attempt-1)),6.0)
        print("[MTR116_HYDRATE_RETRY] attempt=%d sleep=%.2f pump=%s"%(
            attempt,delay,r["pump_pool"][:10]),flush=True)
        time.sleep(delay)
    raise last

def prepare(root):
    state=ORIG(root);pairs=[]
    rows=json.loads(META.read_text(encoding="utf-8"))

    for n,r in enumerate(rows,1):
        try:
            t=time.perf_counter_ns()
            p=hydrate(r);pairs.append(p)
            print("[MTR116_WARM] %d/%d token=%s arrays=%d warm_ms=%.3f"%(
                n,len(rows),p.token[:10],len(p.arrays),
                (time.perf_counter_ns()-t)/1e6),flush=True)
        except Exception as e:
            print("[MTR116_WARM_HOLD] pump=%s reason=%s:%s"%(
                r["pump_pool"][:10],type(e).__name__,str(e)[:160]),flush=True)
        time.sleep(.65)

    if not pairs: raise RuntimeError("MTR116_NO_PAIRS")

    multi={};single={}
    for i,p in enumerate(pairs):
        refs=[(p.pump_base_vault,"PUMP_BASE"),
              (p.pump_quote_vault,"PUMP_QUOTE"),
              (p.meteora_pool,"DLMM_POOL")]
        refs += [(a[1],"DLMM_ARRAY_%d"%j) for j,a in enumerate(p.arrays)]
        for a,k in refs:
            multi.setdefault(a,[]).append((i,k))
            single.setdefault(a,(i,k))

    state["pairs"]=pairs
    state["preg"]=single
    state["preg_multi"]=multi

    for token in list(state["eps"]):
        state["eps"][token]=[
            e for e in state["eps"][token]
            if e.venue not in ("PUMPSWAP","METEORA_DLMM")
        ]
    for p in pairs:
        state["eps"][p.token].extend((m._pump_ep(p),m._dlmm_ep(p)))

    ST["pairs"]=len(pairs)
    ST["tokens"]=len({p.token for p in pairs})
    ST["shared"]=sum(len(v)>1 for v in multi.values())
    ST["max_fanout"]=max(map(len,multi.values()))

    print("[MTR116_REGISTRY] pairs=%d tokens=%d accounts=%d shared=%d max_fanout=%d retries=%d"%(
        ST["pairs"],ST["tokens"],len(multi),ST["shared"],
        ST["max_fanout"],ST["hydrate_retries"]),flush=True)
    return state

def process(state,ev,counter,sim_lane):
    refs=state.get("preg_multi",{}).get(ev["address"])
    if not refs:
        return q20._original_process_event(state,ev,counter,sim_lane)

    if len(refs)>1: ST["fanout_events"]+=1

    for i,kind in refs:
        pair=state["pairs"][i]
        try:
            changed=pd.apply_account_event(
                pair,kind,ev["address"],ev["raw"],ev["slot"],ev["received_ns"]
            )
        except Exception:
            counter["event_errors"]+=1
            continue

        if not changed: continue
        counter["priced_events"]+=1
        key="%s|%s|%s"%(pair.token,pair.pump_pool,pair.meteora_pool)
        q20._lane.submit(
            key,q20._pair_snapshot(pair),ev["slot"],ev["received_ns"]
        )
        if len(refs)>1: ST["fanout_submissions"]+=1

def main():
    print("[MTR-116] START",flush=True)
    print("[FAST_GATE] sizes="+",".join("%.3f"%x for x in FAST),flush=True)

    if not META.exists(): raise RuntimeError("MTR115_META_NOT_FOUND")

    q20.FAST_SIZES=FAST
    q20.FULL_SIZE_CURVE=FAST
    q20.EXPAND_SIZES=()
    q20._patched_process_event=process
    q60b._ORIG_PREPARE=prepare

    rc=q25.run(seconds=60.0)

    r=json.loads(Path(
        "runtime_state/oracle/oracle_live_execution/"
        "oracle_020_latest_state_exact_pricing_worker.json"
    ).read_text(encoding="utf-8"))

    out={**ST,
         "fast_sizes":FAST,
         "submitted":r.get("submitted"),
         "processed":r.get("processed"),
         "replaced":r.get("replaced_before_start"),
         "scan_replaced":r.get("scan_replaced"),
         "stale":r.get("stale_drops"),
         "positive":r.get("positive"),
         "p99_start_ms":r.get("p99_event_start_ms"),
         "p99_scan_ms":r.get("p99_scan_ms"),
         "best":r.get("best"),
         "return_code":rc,
         "execution_authority":False,
         "broadcast":False,
         "private_key_used":False}

    OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str),
                   encoding="utf-8")

    print("[SUMMARY] pairs=%d tokens=%d shared=%d fanout_events=%d "
          "fanout_submissions=%d submitted=%s processed=%s stale=%s "
          "p99_start_ms=%s p99_scan_ms=%s positive=%s"%(
          ST["pairs"],ST["tokens"],ST["shared"],ST["fanout_events"],
          ST["fanout_submissions"],out["submitted"],out["processed"],
          out["stale"],out["p99_start_ms"],out["p99_scan_ms"],
          out["positive"]),flush=True)

    age=out["p99_start_ms"]
    ok=(ST["pairs"]==12 and ST["pairs"]>ST["tokens"] and
        ST["shared"]>0 and ST["fanout_events"]>0 and
        int(out["processed"] or 0)>0 and int(out["stale"] or 0)==0 and
        age is not None and float(age)<500.0)

    print("[RESULT] FAST_GATE_ROUTE_QUEUE_PASS" if ok
          else "[RESULT] FAST_GATE_ROUTE_QUEUE_NOT_CERTIFIED",flush=True)
    print("[OUTPUT] "+str(OUT),flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[BROADCAST] FALSE",flush=True)
    print("[MTR-116] COMPLETE",flush=True)

if __name__=="__main__":
    main()
