"""MTR-165 capture-only observer of canonical production pricing.

Does not modify the scanner or production runtime modules. Public wallet only.
The isolated run delegates to existing warm state and WebSocket event plumbing,
but replaces the price lane attack callback with an evidence-only callback.
"""
import argparse, copy, json, time, types
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
from .mtr_164_live_route_capture import verify, HandoffHold

def forbidden(*args,**kwargs):
    raise RuntimeError("MTR165_EXECUTION_DISABLED")

def route_capture_cb(public_user,output_dir,counter):
    def capture(lane,token,snap,opportunity,slot,received_ns,generation):
        counter["positive_seen"]+=1
        if lane.newer_waiting(token,generation):
            counter["superseded"]+=1
            return
        if opportunity.get("direction")!="PUMP_TO_METEORA":
            counter["wrong_direction"]+=1
            return
        if int(opportunity.get("start",0))!=10000000:
            counter["wrong_size"]+=1
            return
        try:
            route=rt.same_snapshot_route(public_user,snap,opportunity)
            evidence=verify(route)
        except (Exception,) as exc:
            counter["route_holds"]+=1
            print("[MTR165_ROUTE_HOLD]",type(exc).__name__,str(exc)[:90],flush=True)
            return
        # Canonical snapshot captures lack proof of on-chain executable profit.
        record={"route":route,"observation_slot":int(slot),
                "captured_wall_time":time.time(),
                "event_age_ms":max(0,(time.perf_counter_ns()-received_ns)/1e6),
                "evidence":evidence,"protected_bounds_verified":False,
                "simulation_passed":False,"profit_certified":False,
                "broadcast_authorized":False}
        directory=Path(output_dir)
        directory.mkdir(parents=True,exist_ok=True)
        target=directory/"mtr_165_live_route_observation.json"
        target.write_text(json.dumps(record,indent=2,default=str)+"\n",encoding="utf-8")
        counter["captured"]+=1
        print("[MTR165_CAPTURED]",target,"slot=",slot,flush=True)
    return capture

def capture_only(seconds,public_user,output_dir):
    if not 5<=seconds<=300:
        raise RuntimeError("SECONDS_OUT_OF_BOUNDS")
    if not isinstance(public_user,str) or len(public_user)<32 or len(public_user)>44:
        raise RuntimeError("PUBLIC_WALLET_REQUIRED")
    rt.q87.c.b58d(public_user)
    counter={"positive_seen":0,"captured":0,"wrong_direction":0,
             "wrong_size":0,"route_holds":0,"superseded":0}
    callback=route_capture_cb(public_user,output_dir,counter)
    # No module-global monkeypatch. Both functions receive isolated globals.
    price_globals=rt.canonical_price.__globals__.copy()
    price_globals["attack"]=callback
    price_globals["compile_current"]=forbidden
    price_globals["simulate_current"]=forbidden
    price_globals["_execute_route_once"]=forbidden
    safe_price=types.FunctionType(rt.canonical_price.__code__,price_globals,
                                  rt.canonical_price.__name__)
    # q87.c.sim_identity in original run may read a private key; replace it
    # only in the function-local cloned namespace with public identity.
    core_proxy=types.SimpleNamespace(**{
        name:getattr(rt.q87.c,name) for name in ("WSOL",) if hasattr(rt.q87.c,name)})
    core_proxy.sim_identity=lambda: (None,public_user)
    q87_proxy=types.SimpleNamespace(**{
        name:getattr(rt.q87,name) for name in
        ("repaired_candidates","compile_candidate") if hasattr(rt.q87,name)})
    q87_proxy.c=core_proxy
    globals_run=rt.run.__globals__.copy()
    globals_run["q87"]=q87_proxy
    globals_run["canonical_price"]=safe_price
    globals_run["attack"]=callback
    globals_run["compile_current"]=forbidden
    globals_run["simulate_current"]=forbidden
    globals_run["_execute_route_once"]=forbidden
    globals_run["BLOCKHASH"]=types.SimpleNamespace(start=lambda:None,close=lambda:None)
    # Original run() invokes existing warmup and WS; it does not call a signer.
    original=rt.run
    if any(x in original.__code__.co_names for x in
           ("signed_tx","send","keypair","simulate_current","compile_current")):
        raise RuntimeError("CANONICAL_RUN_SAFETY_CONTRACT_CHANGED")
    safe_run=types.FunctionType(original.__code__,globals_run,original.__name__)
    print("[MTR165_MODE] CAPTURE_ONLY_WS_PRICING",flush=True)
    print("[MTR165_WALLET] PUBLIC_ADDRESS_ONLY",flush=True)
    try:
        safe_run(float(seconds))
    finally:
        print("[MTR165_COUNTS]",json.dumps(counter,sort_keys=True),flush=True)
        print("[SIGNING] FALSE",flush=True)
        print("[BROADCAST] FALSE",flush=True)
    return counter

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=float,default=30)
    p.add_argument("--public-wallet",type=str)
    p.add_argument("--output-dir",type=Path,default=Path.cwd()/
                   "runtime_state/oracle/oracle_live_execution")
    args=p.parse_args(argv)
    if not args.public_wallet:
        print("[MTR165] CAPTURE_ONLY_RUNNER_READY")
        print("[MTR165_RUN] HOLD_PUBLIC_WALLET_REQUIRED")
        print("[PRIVATE_KEY] NOT_USED")
        print("[SIGNING] FALSE")
        print("[BROADCAST] FALSE")
        return
    capture_only(args.seconds,args.public_wallet,args.output_dir)
if __name__=="__main__":main()
