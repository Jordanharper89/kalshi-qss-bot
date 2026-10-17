from __future__ import annotations
import json,time
from pathlib import Path

from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b_existing_runtime_multidex_cutover as q60b

META=Path("mtr_114_exact_deep_meta.json")
OUT=Path("mtr_114_controlled_replenishment_warm_cutover.json")
ORIG=q60b._ORIG_PREPARE

def dec(mint):
    raw,_=c.account(mint)
    if len(raw)<45: raise RuntimeError("MINT_ACCOUNT_SHORT:"+mint)
    return int(raw[44])

def hydrate_exact(row):
    pump=row["pump_pool"]; pool=row["meteora_pool"]; token=row["base_mint"]
    raw,_=c.account(pump); pp=c.decode_pump_pool(raw)
    if pp["quote_mint"]!=c.WSOL: raise RuntimeError("PUMP_NOT_WSOL")
    br,_=c.account(pp["base_vault"]); qr,_=c.account(pp["quote_vault"])
    lb,_=c.account(pool); arrays=c.dlmm_arrays(pool)

    p=pd.PairState(
        token=token,pump_pool=pump,meteora_pool=pool,
        token_x=row["token_x"],token_y=row["token_y"],
        decimals_x=dec(row["token_x"]),decimals_y=dec(row["token_y"]),
        pump_base_vault=pp["base_vault"],pump_quote_vault=pp["quote_vault"],
        pump_base_reserve=pd._token_amount_from_raw(br),
        pump_quote_reserve=pd._token_amount_from_raw(qr),
        lb_bytes=lb,arrays=list(arrays),dlmm_state=None,
    )
    p.dlmm_state=pd._build_dlmm_state(p)
    return p

def exact_prepare(root):
    state=ORIG(root)
    rows=json.loads(META.read_text(encoding="utf-8"))
    pairs=[]

    for r in rows:
        try:
            t=time.perf_counter_ns()
            p=hydrate_exact(r); pairs.append(p)
            print("[MTR114_WARM] token=%s arrays=%d warm_ms=%.3f"%(
                p.token[:12],len(p.arrays),(time.perf_counter_ns()-t)/1e6),flush=True)
        except Exception as e:
            print("[MTR114_WARM_HOLD] token=%s reason=%s:%s"%(
                r["base_mint"][:12],type(e).__name__,str(e)[:180]),flush=True)
        time.sleep(.35)

    if not pairs: raise RuntimeError("MTR114_NO_EXACT_PAIRS")

    state["pairs"]=pairs
    state["preg"]=pd.account_registry(pairs)

    eps=state["eps"]
    for token in list(eps):
        eps[token]=[e for e in eps[token] if e.venue not in ("PUMPSWAP","METEORA_DLMM")]

    for p in pairs:
        eps[p.token].extend((m._pump_ep(p),m._dlmm_ep(p)))

    print("[MTR114_INVENTORY] exact_pairs=%d unique_tokens=%d preg=%d"%(
        len(pairs),len({p.token for p in pairs}),len(state["preg"])),flush=True)
    return state

def main():
    print("[MTR-114] START",flush=True)
    print("[SCOPE] 12 deepest unique replenished tokens -> canonical warm PairState",flush=True)

    if not META.exists(): raise RuntimeError("MTR114_META_MISSING")

    q60b._ORIG_PREPARE=exact_prepare
    rc=q25.run(seconds=60.0)

    p25=Path("runtime_state/oracle/oracle_live_execution/oracle_025_single_hydration_exact_live_reuse.json")
    p20=Path("runtime_state/oracle/oracle_live_execution/oracle_020_latest_state_exact_pricing_worker.json")
    a=json.loads(p25.read_text(encoding="utf-8"))
    b=json.loads(p20.read_text(encoding="utf-8"))

    report={
      "mtr":"MTR-114","requested_unique_routes":12,
      "exact_pairs":a.get("exact_pairs"),"accounts":a.get("accounts"),
      "submitted":b.get("submitted"),"processed":b.get("processed"),
      "stale_drops":b.get("stale_drops"),"scan_replaced":b.get("scan_replaced"),
      "positive":b.get("positive"),"p99_event_start_ms":b.get("p99_event_start_ms"),
      "p99_scan_ms":b.get("p99_scan_ms"),"return_code":rc,
      "execution_authority":False,"broadcast":False,"private_key_used":False
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    print("[SUMMARY] exact_pairs=%s accounts=%s submitted=%s processed=%s stale=%s "
          "p99_start_ms=%s p99_scan_ms=%s"%(
          report["exact_pairs"],report["accounts"],report["submitted"],
          report["processed"],report["stale_drops"],
          report["p99_event_start_ms"],report["p99_scan_ms"]),flush=True)

    if int(report["exact_pairs"] or 0)>=8 and int(report["processed"] or 0)>0:
        print("[RESULT] REPLENISHMENT_CANONICAL_WARM_CUTOVER_ACTIVE",flush=True)
    else:
        print("[RESULT] REPLENISHMENT_CANONICAL_WARM_CUTOVER_NOT_CERTIFIED",flush=True)

    print("[OUTPUT] "+str(OUT),flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[BROADCAST] FALSE",flush=True)
    print("[MTR-114] COMPLETE",flush=True)

if __name__=="__main__":
    main()
