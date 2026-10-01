from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_052a6_damm_graph_ready_live_adapter as damm

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_AGE_MS=750.0
WSOL=getattr(c,"WSOL","So11111111111111111111111111111111111111112")

CLMM_SRC=Path("runtime_state/qseries/qarb_clean_bot/qarb_052b5_clmm_exact_descriptor_pavement.json")
ORCA_SRC=Path("runtime_state/qseries/qarb_clean_bot/qarb_052c6_orca_exact_descriptor_repair.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_053_remaining_dex_parity_foundation.json")

def _load(path):
    if not path.is_file(): raise RuntimeError("MISSING_ARTIFACT:"+str(path))
    return json.loads(path.read_text(encoding="utf-8"))

def _addr(x):
    if isinstance(x,str): return x
    if isinstance(x,dict):
        for k in ("pubkey","address","account","key"):
            v=x.get(k)
            if isinstance(v,str) and v:return v
    return None

def _account(addr):
    raw,slot=c.account(addr)
    return {"address":addr,"bytes":len(raw),"slot":slot}

def _damm(root):
    states,reg=damm.prepare(root)
    edges=[]
    for i,(d,s) in enumerate(states):
        edges.append({"venue":"METEORA_DAMM_V2","pool":d.pool,"src":d.token_a,"dst":d.token_b,"state_index":i})
        edges.append({"venue":"METEORA_DAMM_V2","pool":d.pool,"src":d.token_b,"dst":d.token_a,"state_index":i})
    return {
        "descriptors":len(damm.descriptors(root)),
        "live_states":len(states),
        "watched_accounts":len(reg),
        "directed_edges":len(edges),
        "direct_sol_edges":sum(1 for e in edges if WSOL in (e["src"],e["dst"])),
        "priced_live":bool(states),
        "state_ready":bool(states),
        "edges":edges,
    }

def _clmm(root):
    o=_load(root/CLMM_SRC);rows=[]
    for d in o.get("descriptors") or []:
        expected=[]
        for a in d.get("watched_accounts") or []:
            x=_addr(a)
            if x: expected.append(x)
        live=[];errors=[]
        for a in expected:
            try: live.append(_account(a))
            except Exception as e: errors.append(type(e).__name__+":"+str(e))
        rows.append({
            "pool":d.get("pool"),"token_a":d.get("token_a"),"token_b":d.get("token_b"),
            "expected_accounts":len(expected),"live_accounts":len(live),
            "complete":bool(expected and len(live)==len(expected)),
            "errors":errors[:5],
        })
    return {
        "descriptors":len(rows),
        "live_pools":sum(1 for r in rows if r["live_accounts"]>0),
        "complete_pools":sum(1 for r in rows if r["complete"]),
        "state_ready":any(r["complete"] for r in rows),
        "priced_live":False,
        "hold_reason":"LOCAL_CLMM_MATH_PROVIDER_PENDING",
        "rows":rows,
    }

def _orca(root):
    o=_load(root/ORCA_SRC);rows=[]
    for d in o.get("descriptors") or []:
        live={};errors=[]
        for role in ("pool","vault_a","vault_b"):
            a=d.get(role)
            if not isinstance(a,str) or not a: continue
            try: live[role]=_account(a)
            except Exception as e: errors.append(role+":"+type(e).__name__+":"+str(e))
        rows.append({
            "pool":d.get("pool"),"token_a":d.get("token_a"),"token_b":d.get("token_b"),
            "vault_a":d.get("vault_a"),"vault_b":d.get("vault_b"),
            "ready_base_state":all(k in live for k in ("pool","vault_a","vault_b")),
            "live":live,"errors":errors[:5],
        })
    return {
        "descriptors":len(rows),
        "ready_base_states":sum(1 for r in rows if r["ready_base_state"]),
        "state_ready":any(r["ready_base_state"] for r in rows),
        "priced_live":False,
        "hold_reason":"ORCA_TICK_ARRAY_LOCAL_QUOTE_PROVIDER_PENDING",
        "rows":rows,
    }

def build(root):
    root=Path(root)
    d=_damm(root);cl=_clmm(root);oc=_orca(root)

    capability={
        "METEORA_DAMM_V2":{
            "observed_live":d["live_states"]>0,
            "state_ready":d["state_ready"],
            "priced_live":d["priced_live"],
        },
        "RAYDIUM_CLMM":{
            "observed_live":cl["live_pools"]>0,
            "state_ready":cl["state_ready"],
            "priced_live":False,
        },
        "ORCA_WHIRLPOOL":{
            "observed_live":oc["ready_base_states"]>0,
            "state_ready":oc["state_ready"],
            "priced_live":False,
        },
    }

    payload={
        "revision":"QARB_053",
        "purpose":"remaining_dex_parity_foundation",
        "max_age_ms":MAX_AGE_MS,
        "damm":d,"raydium_clmm":cl,"orca_whirlpool":oc,
        "capability":capability,
        "next_boundary":{
            "METEORA_DAMM_V2":"WIRE_INTO_EXISTING_MULTIBASE_GRAPH",
            "RAYDIUM_CLMM":"DECODE_LIVE_POOL_TICK_STATE_AND_BIND_LOCAL_QUOTER",
            "ORCA_WHIRLPOOL":"RESOLVE_TICK_ARRAYS_AND_BIND_LOCAL_QUOTER",
        },
        "execution_authority":False,
        "paper_only":True,
    }
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    p=build(Path.cwd())
    print("[QARB-053] REMAINING DEX PARITY FOUNDATION")
    print("[DAMM] descriptors=%d live_states=%d edges=%d direct_sol=%d priced_live=%s"%(
        p["damm"]["descriptors"],p["damm"]["live_states"],p["damm"]["directed_edges"],
        p["damm"]["direct_sol_edges"],p["damm"]["priced_live"]))
    print("[CLMM] descriptors=%d live_pools=%d complete_pools=%d priced_live=%s"%(
        p["raydium_clmm"]["descriptors"],p["raydium_clmm"]["live_pools"],
        p["raydium_clmm"]["complete_pools"],p["raydium_clmm"]["priced_live"]))
    for r in p["raydium_clmm"]["rows"]:
        print("[CLMM_POOL] %s accounts=%d/%d complete=%s"%(
            str(r["pool"])[:12],r["live_accounts"],r["expected_accounts"],r["complete"]))
    print("[ORCA] descriptors=%d ready_base_states=%d priced_live=%s"%(
        p["orca_whirlpool"]["descriptors"],p["orca_whirlpool"]["ready_base_states"],
        p["orca_whirlpool"]["priced_live"]))
    for r in p["orca_whirlpool"]["rows"]:
        print("[ORCA_POOL] %s ready_base_state=%s"%(str(r["pool"])[:12],r["ready_base_state"]))
    print("[CAPABILITY] "+json.dumps(p["capability"],sort_keys=True))
    print("[NEXT] "+json.dumps(p["next_boundary"],sort_keys=True))
    print("[REPORT]",OUT)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE")

if __name__=="__main__": main()
