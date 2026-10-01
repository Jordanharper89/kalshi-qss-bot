from __future__ import annotations
import argparse,asyncio,json,time
from pathlib import Path
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_052a6_damm_graph_ready_live_adapter as damm
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import meteora_damm_v2_live as damm_live
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_056b_clmm_tick_fee_state as q56b
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_056c_orca_tick_fee_state as q56c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_057a2_clmm_directional_tick_array_resolver as q57a
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_057b_orca_tick_array_pda_resolver as q57b
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_058a_clmm_local_swap_math as q58a
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_058b_orca_local_swap_math as q58b

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
WSOL=getattr(c,"WSOL","So11111111111111111111111111111111111111112")
MAX_AGE_MS=750.0
CLMM_STATE=Path("runtime_state/qseries/qarb_clean_bot/qarb_056b_clmm_tick_fee_state.json")
CLMM_ARRAYS=Path("runtime_state/qseries/qarb_clean_bot/qarb_057a2_clmm_directional_tick_array_resolver.json")
ORCA_STATE=Path("runtime_state/qseries/qarb_clean_bot/qarb_056c_orca_tick_fee_state.json")
ORCA_ARRAYS=Path("runtime_state/qseries/qarb_clean_bot/qarb_057b_orca_tick_array_pda_resolver.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_060b_existing_runtime_multidex_cutover.json")

_ORIG_PREPARE=m.prepare
_ORIG_CAPABILITY=m.capability
_ORIG_PROCESS=p._process_event

def _load(root,path):
    q=Path(root)/path
    if not q.is_file():raise RuntimeError("MISSING:"+str(path))
    return json.loads(q.read_text(encoding="utf-8"))

def _fresh(rec):
    return (perf_counter_ns()-int(rec.get("observed_ns") or 0))/1e6<=MAX_AGE_MS

def _endpoint(venue,token,pool,buy,sell):
    return m.Endpoint(venue,token,pool,buy,sell)

def _add_direct_endpoint(state,venue,pool,a,b,quote_fn):
    if WSOL not in (a,b):return False
    token=b if a==WSOL else a
    state["eps"][token].append(_endpoint(
        venue,token,pool,
        lambda x,q=quote_fn:q(WSOL,int(x)),
        lambda x,q=quote_fn,t=token:q(t,int(x))))
    return True

def _warm_damm(root,state):
    states,reg=damm.prepare(root);rows=[];newreg=state.setdefault("xreg",{})
    state["damm_states"]=states
    for i,(d,s) in enumerate(states):
        for a in (d.vault_a,d.vault_b):newreg[a]=("DAMM",i,d)
        def q(inp,amt,d=d,s=s):
            return int(damm.quote_edge((d,s),inp,int(amt)))
        direct=_add_direct_endpoint(state,"METEORA_DAMM_V2",d.pool,d.token_a,d.token_b,q)
        rows.append({"pool":d.pool,"direct_wsol":direct,"watched":[d.vault_a,d.vault_b]})
    return rows

def _warm_clmm(root,state):
    src=_load(root,CLMM_STATE);arr=_load(root,CLMM_ARRAYS);aby={r["pool"]:r for r in arr["rows"]}
    rows=[];records=[];newreg=state.setdefault("xreg",{})
    for r in src.get("rows") or []:
        if not r.get("decoded") or not r.get("config_decoded"):continue
        st=dict(r.get("state") or {});cfg=dict(r.get("config") or {})
        pool=r["pool"];raws={}
        for seq in (aby.get(pool,{}).get("sequences") or {}).values():
            for x in seq:
                a=x.get("address")
                if not a or a in raws:continue
                try:raw,_=c.account(a);raws[a]=raw
                except Exception:pass
        if not raws:continue
        rec={"pool":pool,"state":st,"config":cfg,"arrays":raws,"observed_ns":perf_counter_ns()}
        i=len(records);records.append(rec);newreg[pool]=("CLMM",i,None)
        for a in raws:newreg[a]=("CLMM",i,None)
        def q(inp,amt,rec=rec):
            if not _fresh(rec):raise RuntimeError("STALE_RAYDIUM_CLMM_PROVISIONAL")
            s=rec["state"];zero=(inp==s["token_mint_0"])
            if inp not in (s["token_mint_0"],s["token_mint_1"]):raise RuntimeError("MINT_NOT_IN_POOL")
            ticks={}
            for rr in rec["arrays"].values():
                for t in q58a.decode_ticks(rr):ticks[t["tick"]]=t
            if not ticks:raise RuntimeError("NO_CLMM_TICKS")
            return int(q58a.quote_steps(s["sqrt_price_x64"],s["liquidity"],rec["config"]["trade_fee_rate"],
                                        int(amt),list(ticks.values()),zero)["amount_out"])
        direct=_add_direct_endpoint(state,"RAYDIUM_CLMM",pool,st["token_mint_0"],st["token_mint_1"],q)
        rows.append({"pool":pool,"direct_wsol":direct,"arrays":len(raws)})
    state["clmm_records"]=records
    return rows

def _warm_orca(root,state):
    src=_load(root,ORCA_STATE);arr=_load(root,ORCA_ARRAYS);aby={r["pool"]:r for r in arr["rows"]}
    rows=[];records=[];newreg=state.setdefault("xreg",{})
    for r in src.get("rows") or []:
        if not r.get("decoded"):continue
        st=dict(r.get("state") or {});pool=r["pool"];raws={}
        for seq in (aby.get(pool,{}).get("sequences") or {}).values():
            for x in seq:
                a=x.get("address")
                if not a or a in raws or not x.get("exists"):continue
                try:raw,_=c.account(a);raws[a]=raw
                except Exception:pass
        if not raws:continue
        rec={"pool":pool,"state":st,"arrays":raws,"observed_ns":perf_counter_ns()}
        i=len(records);records.append(rec);newreg[pool]=("ORCA",i,None)
        for a in raws:newreg[a]=("ORCA",i,None)
        def q(inp,amt,rec=rec):
            if not _fresh(rec):raise RuntimeError("STALE_ORCA_PROVISIONAL")
            s=rec["state"];zero=(inp==s["token_mint_a"])
            if inp not in (s["token_mint_a"],s["token_mint_b"]):raise RuntimeError("MINT_NOT_IN_POOL")
            ticks={}
            for rr in rec["arrays"].values():
                if rr[:8]!=q58b.tick_disc():continue
                start=int.from_bytes(rr[8:12],"little",signed=True)
                for t in q58b.decode_fixed(rr,start,s["tick_spacing"]):ticks[t["tick"]]=t
            if not ticks:raise RuntimeError("NO_ORCA_TICKS")
            return int(q58b.quote_steps(s["sqrt_price_x64"],s["liquidity"],s["fee_rate"],
                                        int(amt),list(ticks.values()),zero)["amount_out"])
        direct=_add_direct_endpoint(state,"ORCA_WHIRLPOOL",pool,st["token_mint_a"],st["token_mint_b"],q)
        rows.append({"pool":pool,"direct_wsol":direct,"arrays":len(raws)})
    state["orca_records"]=records
    return rows

def extended_prepare(root):
    state=_ORIG_PREPARE(root)
    state["xreg"]={}
    report={"METEORA_DAMM_V2":[],"RAYDIUM_CLMM":[],"ORCA_WHIRLPOOL":[]}
    errors=[]
    for name,fn in (("METEORA_DAMM_V2",_warm_damm),("RAYDIUM_CLMM",_warm_clmm),("ORCA_WHIRLPOOL",_warm_orca)):
        try:report[name]=fn(root,state)
        except Exception as e:errors.append(name+":"+type(e).__name__+":"+str(e))
    addrs=[]
    for a in list(state["preg"])+list(state["creg"])+list(state["xreg"])+list(state["observed"]):
        if a not in addrs:addrs.append(a)
    state["addresses"]=addrs[:m.MAX_ACCOUNTS]
    state["cutover_report"]=report;state["cutover_errors"]=errors
    return state

def extended_capability(state):
    cap=_ORIG_CAPABILITY(state)
    rep=state.get("cutover_report") or {}
    cap["METEORA_DAMM_V2"]={"priced_live":bool(rep.get("METEORA_DAMM_V2")),
                            "paper_only":True,"validation":"QARB_056A_PRICED"}
    cap["RAYDIUM_CLMM"]={"priced_live":any(x.get("direct_wsol") for x in rep.get("RAYDIUM_CLMM") or []),
                         "paper_only":True,"validation":"PROVISIONAL_SHADOW_PENDING"}
    cap["ORCA_WHIRLPOOL"]={"priced_live":any(x.get("direct_wsol") for x in rep.get("ORCA_WHIRLPOOL") or []),
                           "paper_only":True,"validation":"PROVISIONAL_SHADOW_PENDING"}
    return cap

def _tokens_for_new_event(state,a,raw,received_ns):
    item=state.get("xreg",{}).get(a)
    if not item:return set(),False
    kind,i,d=item;tokens=set();priced=False
    if kind=="DAMM":
        dd,st=state["damm_states"][i]
        if damm_live.update(st,dd,a,raw,received_ns):
            if WSOL in (dd.token_a,dd.token_b):
                tokens.add(dd.token_b if dd.token_a==WSOL else dd.token_a);priced=True
    elif kind=="CLMM":
        rec=state["clmm_records"][i]
        if a==rec["pool"]:rec["state"]=q56b.decode_pool(raw)
        else:rec["arrays"][a]=raw
        rec["observed_ns"]=int(received_ns);s=rec["state"]
        if WSOL in (s["token_mint_0"],s["token_mint_1"]):
            tokens.add(s["token_mint_1"] if s["token_mint_0"]==WSOL else s["token_mint_0"]);priced=True
    elif kind=="ORCA":
        rec=state["orca_records"][i]
        if a==rec["pool"]:rec["state"]=q56c.decode_pool(raw)
        else:rec["arrays"][a]=raw
        rec["observed_ns"]=int(received_ns);s=rec["state"]
        if WSOL in (s["token_mint_a"],s["token_mint_b"]):
            tokens.add(s["token_mint_b"] if s["token_mint_a"]==WSOL else s["token_mint_a"]);priced=True
    return tokens,priced

def extended_process(state,ev,counters,sim_lane):
    _ORIG_PROCESS(state,ev,counters,sim_lane)
    a=ev["address"]
    if a not in state.get("xreg",{}):return
    try:tokens,priced=_tokens_for_new_event(state,a,ev["raw"],ev["received_ns"])
    except Exception:
        counters["event_errors"]+=1;return
    if not priced:return
    counters["priced_events"]+=1
    for token in tokens:
        r=m.evaluate_token(token,state["eps"].get(token,()),state["landing"],ev["received_ns"])
        if not r:continue
        counters["lat"].append(float(r["event_to_decision_ms"]))
        if counters["best"] is None or r["net_sol"]>counters["best"]["net_sol"]:counters["best"]=r
        if r["qualified"]:
            counters["signals"]+=1
            print("[PAPER_HOT_SIGNAL] token=%s buy=%s sell=%s size=%.6f net=%+.9f SOL bps=%+.2f age_ms=%.3f validation=PROVISIONAL"%(
                token[:10],r["buy_venue"],r["sell_venue"],r["size_sol"],r["net_sol"],r["net_bps"],r["event_to_decision_ms"]),flush=True)
            # New-venue routes are observation-only until shadow validation; never submit to simulation/execution lane.

def install():
    m.prepare=extended_prepare
    m.capability=extended_capability
    p._process_event=extended_process
    return p

def inspect_cutover(root):
    runtime=install();state=m.prepare(Path(root));cap=m.capability(state)
    rep={"revision":"QARB_060B","accounts":len(state["addresses"]),"priced_tokens":len(state["eps"]),
         "extension_registry":len(state.get("xreg",{})),"capability":cap,
         "cutover_report":state.get("cutover_report"),"errors":state.get("cutover_errors"),
         "execution_authority":False,"paper_only":True}
    q=Path(root)/OUT;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(rep,indent=2,sort_keys=True),encoding="utf-8")
    return rep

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=20.0);a=ap.parse_args(argv)
    rep=inspect_cutover(Path.cwd())
    print("[QARB-060B] EXISTING PERSISTENT RUNTIME MULTIDEX CUTOVER",flush=True)
    print("[CUTOVER] accounts=%d priced_tokens=%d extension_registry=%d"%(rep["accounts"],rep["priced_tokens"],rep["extension_registry"]),flush=True)
    print("[CAPABILITY] "+json.dumps(rep["capability"],sort_keys=True),flush=True)
    if rep["errors"]:print("[WARM_ERRORS] "+json.dumps(rep["errors"]),flush=True)
    print("[RUNNER] persistent_profit_runtime.serve | no parallel runtime",flush=True)
    print("[NEW_VENUES] DAMM=paper-live CLMM/ORCA=paper-live provisional-shadow-pending",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE",flush=True)
    return asyncio.run(p.serve(Path.cwd(),a.seconds))

if __name__=="__main__":main()
