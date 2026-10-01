from __future__ import annotations
import asyncio,json,os,time
from pathlib import Path
from time import perf_counter_ns

from meteora_dlmm import quote as dlmm_quote_live
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as q59

MIN_SIM_BPS=float(os.getenv("QARB_ATOMIC_SIM_MIN_BPS","20"))
MAX_SIGNAL_AGE_MS=float(os.getenv("QARB_ATOMIC_SIM_MAX_SIGNAL_AGE_MS","750"))
DEBOUNCE_SECONDS=float(os.getenv("QARB_ATOMIC_SIM_DEBOUNCE_SECONDS","2.0"))
QUEUE_MAX=int(os.getenv("QARB_ATOMIC_SIM_QUEUE_MAX","64"))
JOURNAL=Path("runtime_state/qseries/qarb_clean_bot/live_atomic_simulations.jsonl")

def _append(root,row):
    p=Path(root)/JOURNAL
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f:
        f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")

def _find_pair(state,signal):
    token=signal["token"];pump=signal["buy_pool"];meteora=signal["sell_pool"]
    for p in state["pairs"]:
        if p.token==token and p.pump_pool==pump and p.meteora_pool==meteora:
            return p
    raise RuntimeError("LIVE_PAIR_BINDING_NOT_FOUND")

def _bound_meta(pair):
    return {
      "address":pair.meteora_pool,
      "token_x":pair.token_x,
      "token_y":pair.token_y,
      "decimals_x":pair.decimals_x,
      "decimals_y":pair.decimals_y,
    }

def _live_dlmm_quote(pair,amount_in,input_mint):
    if input_mint==pair.token_x: swap_for_y=True
    elif input_mint==pair.token_y: swap_for_y=False
    else: raise RuntimeError("DLMM_DIRECTION")
    q=dlmm_quote_live(pair.dlmm_state,amount_in=int(amount_in),swap_for_y=swap_for_y,strict=True)
    if not getattr(q,"complete",False) or int(getattr(q,"remaining_in",0) or 0):
        raise RuntimeError("DLMM_PARTIAL")
    return {
      "raw_out":int(q.amount_out),
      "bins_crossed":max(1,int(getattr(q,"bins_crossed",1) or 1)),
      "swap_for_y":swap_for_y,
    }

def compose_bound(user,pair,start_sol):
    start=int(round(float(start_sol)*1e9))
    p_ixs,alts,pump_token_out=q59.api_pump_route(user,pair.token,start)
    pump_bound=any(
        a.get("pubkey")==pair.pump_pool
        for ix in p_ixs
        for a in (ix.get("accounts") or [])
    )
    if not pump_bound:
        raise RuntimeError("PUMP_BINDING_DRIFT")
    mq=_live_dlmm_quote(pair,pump_token_out,pair.token)
    end=int(mq["raw_out"])
    meta=_bound_meta(pair)
    m_ix=q59.dlmm_reverse_ix(user,meta,pump_token_out,mq)
    return {
      "start_lamports":start,
      "pump_token_out_raw":pump_token_out,
      "meteora_end_lamports":end,
      "pre_sim_net_lamports":end-start,
      "pre_sim_bps":(end-start)/start*10000.0,
      "alts":alts,
      "candidates":q59.candidate_instruction_sets(p_ixs,m_ix),
    }

def simulate_signal(root,state,signal):
    if signal["buy_venue"]!="PUMPSWAP" or signal["sell_venue"]!="METEORA_DLMM":
        return {"status":"UNSUPPORTED_DIRECTION","execution_authority":False}
    if float(signal.get("event_to_decision_ms") or 0)>MAX_SIGNAL_AGE_MS:
        return {"status":"STALE_SIGNAL","execution_authority":False}
    if float(signal.get("net_bps") or 0)<MIN_SIM_BPS:
        return {"status":"BELOW_SIM_GATE","execution_authority":False}

    pair=_find_pair(state,signal)
    kp,user=c.sim_identity()
    route=compose_bound(user,pair,float(signal["size_sol"]))
    bh=c.rpc("getLatestBlockhash",[{"commitment":"processed"}])["value"]["blockhash"]
    winner,attempts=q59.attempt_candidate_simulations(user,kp,route,bh)
    row={
      "ts":time.time(),
      "token":signal["token"],
      "pump_pool":signal["buy_pool"],
      "meteora_pool":signal["sell_pool"],
      "size_sol":signal["size_sol"],
      "local_net_sol":signal["net_sol"],
      "local_bps":signal["net_bps"],
      "pre_sim_net_sol":route["pre_sim_net_lamports"]/1e9,
      "pre_sim_bps":route["pre_sim_bps"],
      "winner":winner,
      "attempts":attempts,
      "profitable_simulation":bool(winner and winner.get("profitable")),
      "sim_pnl_sol":None if not winner or winner.get("sim_pnl_lamports") is None else winner["sim_pnl_lamports"]/1e9,
      "sim_bps":None if not winner else winner.get("sim_bps"),
      "execution_authority":False,
      "real_money_moved":False,
    }
    _append(root,row)
    return row

class SimulationLane:
    def __init__(self,root,state):
        self.root=Path(root);self.state=state
        self.q=asyncio.Queue(maxsize=QUEUE_MAX)
        self.last={}
        self.attempts=0;self.profitable=0;self.failures=0;self.drops=0;self.best=None

    def submit(self,signal):
        if signal["buy_venue"]!="PUMPSWAP" or signal["sell_venue"]!="METEORA_DLMM":
            return False
        now=time.monotonic()
        key=(signal["token"],signal["buy_pool"],signal["sell_pool"],round(float(signal["size_sol"]),9))
        if now-self.last.get(key,0.0)<DEBOUNCE_SECONDS:
            return False
        self.last[key]=now
        try:self.q.put_nowait(dict(signal))
        except asyncio.QueueFull:
            self.drops+=1;return False
        return True

    async def worker(self,stop):
        while not stop.is_set():
            try:sig=await asyncio.wait_for(self.q.get(),timeout=.5)
            except asyncio.TimeoutError:continue
            self.attempts+=1
            try:
                row=await asyncio.to_thread(simulate_signal,self.root,self.state,sig)
                if row.get("profitable_simulation"):
                    self.profitable+=1
                    if self.best is None or float(row.get("sim_pnl_sol") or -1e99)>float(self.best.get("sim_pnl_sol") or -1e99):
                        self.best=row
                    print("[ATOMIC_SIM_PROFIT] token=%s size=%.6f local=%+.9f_SOL sim=%+.9f_SOL sim_bps=%+.2f"%(
                        row["token"][:10],row["size_sol"],row["local_net_sol"],
                        row["sim_pnl_sol"],row["sim_bps"]),flush=True)
                else:
                    print("[ATOMIC_SIM_REJECT] token=%s size=%.6f local=%+.9f_SOL status=NO_PROFITABLE_SIM"%(
                        sig["token"][:10],sig["size_sol"],sig["net_sol"]),flush=True)
            except Exception as exc:
                self.failures+=1
                print("[ATOMIC_SIM_ERROR] token=%s %s:%s"%(
                    sig["token"][:10],type(exc).__name__,exc),flush=True)
