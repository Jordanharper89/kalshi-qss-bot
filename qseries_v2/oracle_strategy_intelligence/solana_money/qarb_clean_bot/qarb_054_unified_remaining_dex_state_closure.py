from __future__ import annotations
import base64,json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_052a6_damm_graph_ready_live_adapter as damm

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_AGE_MS=750.0
WSOL=getattr(c,"WSOL","So11111111111111111111111111111111111111112")
CLMM_SRC=Path("runtime_state/qseries/qarb_clean_bot/qarb_052b5_clmm_exact_descriptor_pavement.json")
ORCA_SRC=Path("runtime_state/qseries/qarb_clean_bot/qarb_052c6_orca_exact_descriptor_repair.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_054_unified_remaining_dex_state_closure.json")

def _load(p):
    if not p.is_file(): raise RuntimeError("MISSING_ARTIFACT:"+str(p))
    return json.loads(p.read_text(encoding="utf-8"))

def _addr(x):
    if isinstance(x,str): return x
    if isinstance(x,dict):
        for k in ("pubkey","address","account","key"):
            v=x.get(k)
            if isinstance(v,str) and v:return v
    return None

def _read(addr,tries=3):
    last=None
    for i in range(tries):
        try:
            raw,slot=c.account(addr)
            return {"address":addr,"slot":slot,"bytes":len(raw),
                    "raw_b64":base64.b64encode(raw).decode("ascii"),
                    "attempt":i+1}
        except Exception as e:
            last=e
            time.sleep(.35*(i+1))
    raise last

def _damm(root):
    states,reg=damm.prepare(root)
    edges=[];quote_checks=[]
    for i,(d,s) in enumerate(states):
        edges.append({"venue":"METEORA_DAMM_V2","pool":d.pool,"src":d.token_a,"dst":d.token_b})
        edges.append({"venue":"METEORA_DAMM_V2","pool":d.pool,"src":d.token_b,"dst":d.token_a})
        probe_in=100000
        for mint in (d.token_a,d.token_b):
            try:
                out=damm.quote_edge((d,s),mint,probe_in)
                quote_checks.append({"pool":d.pool,"input_mint":mint,"amount_in":probe_in,
                                     "amount_out":int(out),"ok":int(out)>=0})
            except Exception as e:
                quote_checks.append({"pool":d.pool,"input_mint":mint,"amount_in":probe_in,
                                     "ok":False,"error":type(e).__name__+":"+str(e)})
    return {
        "live_states":len(states),"watched_accounts":len(reg),
        "directed_edges":len(edges),"direct_sol_edges":sum(1 for e in edges if WSOL in (e["src"],e["dst"])),
        "quote_checks":quote_checks,
        "quote_passes":sum(1 for q in quote_checks if q.get("ok")),
        "priced_live":bool(states and quote_checks and all(q.get("ok") for q in quote_checks)),
        "edges":edges,
    }

def _clmm(root):
    o=_load(root/CLMM_SRC);rows=[]
    for d in o.get("descriptors") or []:
        expected=[a for a in (_addr(x) for x in (d.get("watched_accounts") or [])) if a]
        live=[];fail=[]
        for a in expected:
            try: live.append(_read(a))
            except Exception as e: fail.append({"address":a,"error":type(e).__name__+":"+str(e)})
            time.sleep(.04)
        rows.append({
            "pool":d.get("pool"),"token_a":d.get("token_a"),"token_b":d.get("token_b"),
            "expected_accounts":len(expected),"live_accounts":len(live),
            "complete":bool(expected and len(live)==len(expected)),
            "accounts":live,"failures":fail[:10]
        })
    return {
        "descriptors":len(rows),
        "live_pools":sum(1 for r in rows if r["live_accounts"]>0),
        "complete_pools":sum(1 for r in rows if r["complete"]),
        "state_ready":any(r["complete"] for r in rows),
        "priced_live":False,
        "next":"LOCAL_CLMM_POOL_TICK_DECODER_AND_QUOTER",
        "rows":rows,
    }

def _orca(root):
    o=_load(root/ORCA_SRC);rows=[]
    for d in o.get("descriptors") or []:
        live={};fail=[]
        for role in ("pool","vault_a","vault_b"):
            a=d.get(role)
            if not isinstance(a,str) or not a: continue
            try: live[role]=_read(a)
            except Exception as e: fail.append({"role":role,"address":a,"error":type(e).__name__+":"+str(e)})
            time.sleep(.08)
        rows.append({
            "pool":d.get("pool"),"token_a":d.get("token_a"),"token_b":d.get("token_b"),
            "vault_a":d.get("vault_a"),"vault_b":d.get("vault_b"),
            "ready_base_state":all(k in live for k in ("pool","vault_a","vault_b")),
            "live":live,"failures":fail
        })
    return {
        "descriptors":len(rows),
        "ready_base_states":sum(1 for r in rows if r["ready_base_state"]),
        "state_ready":any(r["ready_base_state"] for r in rows),
        "priced_live":False,
        "next":"ORCA_WHIRLPOOL_TICK_ARRAY_DECODER_AND_QUOTER",
        "rows":rows,
    }

def build(root):
    root=Path(root)
    d=_damm(root);cl=_clmm(root);oc=_orca(root)
    payload={
        "revision":"QARB_054",
        "purpose":"unified_remaining_dex_state_closure",
        "max_age_ms":MAX_AGE_MS,
        "venues":{
            "METEORA_DAMM_V2":d,
            "RAYDIUM_CLMM":cl,
            "ORCA_WHIRLPOOL":oc,
        },
        "capability":{
            "METEORA_DAMM_V2":{"state_ready":bool(d["live_states"]),"priced_live":d["priced_live"]},
            "RAYDIUM_CLMM":{"state_ready":cl["state_ready"],"priced_live":False},
            "ORCA_WHIRLPOOL":{"state_ready":oc["state_ready"],"priced_live":False},
        },
        "next_boundary":{
            "METEORA_DAMM_V2":"CUT_GRAPH_EDGES_INTO_EXISTING_MULTIBASE_HUNTER",
            "RAYDIUM_CLMM":"LOCAL_CLMM_POOL_TICK_DECODER_AND_QUOTER",
            "ORCA_WHIRLPOOL":"ORCA_WHIRLPOOL_TICK_ARRAY_DECODER_AND_QUOTER",
        },
        "execution_authority":False,
        "paper_only":True,
    }
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    p=build(Path.cwd())
    d=p["venues"]["METEORA_DAMM_V2"];cl=p["venues"]["RAYDIUM_CLMM"];oc=p["venues"]["ORCA_WHIRLPOOL"]
    print("[QARB-054] UNIFIED REMAINING DEX STATE CLOSURE")
    print("[DAMM] states=%d edges=%d direct_sol=%d quote_passes=%d/%d priced_live=%s"%(
        d["live_states"],d["directed_edges"],d["direct_sol_edges"],d["quote_passes"],len(d["quote_checks"]),d["priced_live"]))
    print("[CLMM] descriptors=%d live_pools=%d complete_pools=%d priced_live=%s"%(
        cl["descriptors"],cl["live_pools"],cl["complete_pools"],cl["priced_live"]))
    for r in cl["rows"]:
        print("[CLMM_POOL] %s accounts=%d/%d complete=%s"%(
            str(r["pool"])[:12],r["live_accounts"],r["expected_accounts"],r["complete"]))
    print("[ORCA] descriptors=%d ready_base_states=%d priced_live=%s"%(
        oc["descriptors"],oc["ready_base_states"],oc["priced_live"]))
    for r in oc["rows"]:
        print("[ORCA_POOL] %s ready_base_state=%s"%(str(r["pool"])[:12],r["ready_base_state"]))
    print("[CAPABILITY] "+json.dumps(p["capability"],sort_keys=True))
    print("[NEXT] "+json.dumps(p["next_boundary"],sort_keys=True))
    print("[REPORT]",OUT)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE")

if __name__=="__main__": main()
