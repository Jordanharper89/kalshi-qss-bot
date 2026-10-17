from __future__ import annotations
import asyncio,base64,time,urllib.error
from solders.transaction import VersionedTransaction
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint7_live_90s_fee_ranked_watch as c7
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint12_multi_pool_live_size_optimizer as c12
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint13_live_reverse_fee_execution_proof as c13

SECONDS=90.0
MAX_EVENT_AGE_MS=1500.0
WATCH={"quotes":0,"gross_positive":0,"fee_positive":0,"sim_attempts":0,"sim_pass":0,"sim_fail":0,"stale_holds":0,"superseded_holds":0,"best_after_fee":None}
SIGNER=None
USER=None

def _signed_simulation(compiled):
    tx=VersionedTransaction(compiled["msg"],[SIGNER])
    encoded=base64.b64encode(bytes(tx)).decode()
    last=None
    for attempt in range(1,7):
        try:
            result=r.q87.c.rpc("simulateTransaction",[encoded,{"encoding":"base64","sigVerify":True,"replaceRecentBlockhash":False,"commitment":"processed"}])
            if not isinstance(result,dict): raise RuntimeError("CHECKPOINT14_SIM_RESULT_NOT_MAPPING")
            value=result.get("value")
            if not isinstance(value,dict): raise RuntimeError("CHECKPOINT14_SIM_VALUE_NOT_MAPPING")
            return {"err":value.get("err"),"units":value.get("unitsConsumed"),"logs":list(value.get("logs") or [])}
        except urllib.error.HTTPError as exc:
            last=exc
            if getattr(exc,"code",None)!=429: raise
            delay=min(4.0,.50*(2**(attempt-1)))
            print("[CHECKPOINT14_SIM_429] attempt=%d sleep=%.2fs"%(attempt,delay),flush=True)
            time.sleep(delay)
    raise last or RuntimeError("CHECKPOINT14_SIM_429_EXHAUSTED")

def _price(self,identity,row):
    snap,slot,received_ns,generation=row
    token=str(snap["token"]); pool=str(snap["meteora"]["address"])
    for size in c12.SIZES:
        for fn in (c7._reverse_only,c7._forward_only):
            if self.newer_waiting(identity,generation):
                WATCH["superseded_holds"]+=1; self.scan_replaced+=1; return
            try:
                op=fn(snap,size)
            except RuntimeError as exc:
                if str(exc)=="DLMM_PARTIAL": continue
                raise
            WATCH["quotes"]+=1; self.processed+=1
            if int(op["local_net"])<=0: continue
            WATCH["gross_positive"]+=1
            if op["direction"]!="METEORA_TO_PUMP": continue
            if self.newer_waiting(identity,generation):
                WATCH["superseded_holds"]+=1; self.scan_replaced+=1; return
            age=max(0.0,(time.perf_counter_ns()-received_ns)/1e6)
            if age>MAX_EVENT_AGE_MS:
                WATCH["stale_holds"]+=1
                print("[CHECKPOINT14_STALE_HOLD] pair=%s size=%.3f age_ms=%.3f"%(identity[:28],size,age),flush=True)
                continue
            try:
                proof=c13._compile_reverse(USER,snap,op)
            except Exception as exc:
                print("[CHECKPOINT14_PROOF_ERROR] pair=%s size=%.3f %s:%s"%(identity[:28],size,type(exc).__name__,str(exc)[:220]),flush=True)
                continue
            if not proof.get("ok"): continue
            if proof["after_fee"]<=0:
                print("[CHECKPOINT14_FEE_HOLD] pair=%s size=%.3f gross=%+d fee=%d after_fee=%+d"%(identity[:28],size,proof["gross"],proof["fee"],proof["after_fee"]),flush=True)
                continue
            WATCH["fee_positive"]+=1
            row2=dict(op); row2.update({"pair_key":identity,"meteora_pool":pool,"fee":proof["fee"],"after_fee":proof["after_fee"],"bytes":proof["compiled"]["bytes"]})
            if WATCH["best_after_fee"] is None or int(row2["after_fee"])>int(WATCH["best_after_fee"]["after_fee"]):
                WATCH["best_after_fee"]=row2
            if self.newer_waiting(identity,generation):
                WATCH["superseded_holds"]+=1; self.scan_replaced+=1; return
            age=max(0.0,(time.perf_counter_ns()-received_ns)/1e6)
            if age>MAX_EVENT_AGE_MS:
                WATCH["stale_holds"]+=1
                print("[CHECKPOINT14_PRE_SIM_STALE] pair=%s size=%.3f age_ms=%.3f"%(identity[:28],size,age),flush=True)
                continue
            WATCH["sim_attempts"]+=1
            try:
                sim=_signed_simulation(proof["compiled"])
            except Exception as exc:
                WATCH["sim_fail"]+=1
                print("[CHECKPOINT14_SIM_ERROR] pair=%s size=%.3f %s:%s"%(identity[:28],size,type(exc).__name__,str(exc)[:220]),flush=True)
                continue
            if sim["err"] is None:
                WATCH["sim_pass"]+=1
                print("[CHECKPOINT14_SIGNED_SIM_PASS] pair=%s token=%s pool=%s slot=%s size=%.3f gross=%+d fee=%d after_fee=%+d bps=%+.2f bytes=%d units=%s age_ms=%.3f"%(identity[:28],token[:10],pool[:12],slot,size,proof["gross"],proof["fee"],proof["after_fee"],float(op["local_bps"]),int(proof["compiled"]["bytes"]),str(sim["units"]),age),flush=True)
            else:
                WATCH["sim_fail"]+=1
                print("[CHECKPOINT14_SIGNED_SIM_FAIL] pair=%s size=%.3f after_fee=%+d err=%s units=%s age_ms=%.3f"%(identity[:28],size,proof["after_fee"],str(sim["err"]),str(sim["units"]),age),flush=True)
                for line in sim["logs"][-8:]:
                    print("[CHECKPOINT14_SIM_LOG] "+str(line),flush=True)

def main():
    global SIGNER,USER
    old_process=r.process_event; old_price=r.canonical_price; old_ready=set(r.READY_TOKENS)
    lane=None
    try:
        state,registry,failures=c12._expanded_state()
        r.q25.install_hot_math_and_prewarm(state); r.q18.install_exact_hot_math()
        seen=set()
        for pair in state["pairs"]:
            pump=str(pair.pump_pool)
            if pump in seen: continue
            seen.add(pump); r.q18.worker().warm(pump)
        SIGNER,USER=r.q87.c.sim_identity()
        if SIGNER is None or not USER: raise RuntimeError("CHECKPOINT14_SIGNER_UNAVAILABLE")
        r.BLOCKHASH.start()
        r.READY_TOKENS={c12.pair_key(pair) for pair in state["pairs"]}
        r.process_event=c12._process_event; r.canonical_price=_price
        lane=r.q20.LatestStateLane(); lane._price=_price.__get__(lane,r.q20.LatestStateLane); lane.start()
        print("[CHECKPOINT14_START] seconds=90 fee_positive_to_signed_sim=True max_event_age_ms=1500 sigVerify=True broadcast=False",flush=True)
        print("[CHECKPOINT14_UNIVERSE] registry_pairs=%d live_pairs=%d hydrate_failures=%d accounts=%d"%(int(registry.get("ready_pair_count") or len(registry.get("rows") or [])),len(state["pairs"]),len(failures),len(state["addresses"])),flush=True)
        print("[CHECKPOINT14_SIZES] 0.001,0.010,0.025,0.050,0.100,0.180,0.280,0.500,1.000,1.400",flush=True)
        print("[CHECKPOINT14_GATES] gross_positive -> real_fee_positive -> not_superseded -> age<=1500ms -> signed_simulation",flush=True)
        print("[BROADCAST] disabled",flush=True)
        asyncio.run(r.serve_canonical(state,SECONDS,lane))
        print("[CHECKPOINT14_SUMMARY] quotes=%d gross_positive=%d fee_positive=%d sim_attempts=%d sim_pass=%d sim_fail=%d stale_holds=%d superseded_holds=%d"%(WATCH["quotes"],WATCH["gross_positive"],WATCH["fee_positive"],WATCH["sim_attempts"],WATCH["sim_pass"],WATCH["sim_fail"],WATCH["stale_holds"],WATCH["superseded_holds"]),flush=True)
        best=WATCH["best_after_fee"]
        if best is not None:
            print("[CHECKPOINT14_BEST_AFTER_FEE] pair=%s token=%s pool=%s dir=%s size=%.3f gross=%+d fee=%d after_fee=%+d bps=%+.2f bytes=%d"%(best["pair_key"][:28],best["token"][:10],best["meteora_pool"][:12],best["direction"],best["size_sol"],int(best["local_net"]),int(best["fee"]),int(best["after_fee"]),float(best["local_bps"]),int(best["bytes"])),flush=True)
        print("[CHECKPOINT14_GATE] status=%s"%("SIGNED_SIMULATION_PASS_OBSERVED" if WATCH["sim_pass"]>0 else "NO_SIGNED_SIMULATION_PASS_IN_90S"),flush=True)
        return 0
    finally:
        r.process_event=old_process; r.canonical_price=old_price; r.READY_TOKENS=old_ready
        try: r.BLOCKHASH.close()
        except Exception: pass
        if lane is not None: lane.close()
        if getattr(r.q18,"_worker",None) is not None:
            r.q18._worker.close(); r.q18._worker=None
        try: r.q25.q23.worker().close()
        except Exception: pass

if __name__=="__main__":
    raise SystemExit(main())
