from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import meteora_damm_v2_live as live

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_AGE_MS=750.0
SRC=Path("runtime_state/qseries/qarb_clean_bot/qarb_052a5_damm_source_certified_bridge.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_052a6_damm_graph_ready_adapter.json")

def descriptors(root):
    p=Path(root)/SRC
    if not p.is_file(): raise RuntimeError("QARB_052A5_ARTIFACT_MISSING")
    o=json.loads(p.read_text(encoding="utf-8"))
    rows=o.get("hydrated") or o.get("descriptors") or []
    out=[]
    for r in rows:
        vals=[r.get(k) for k in ("pool","token_a","token_b","vault_a","vault_b")]
        if not all(isinstance(x,str) and x for x in vals): continue
        out.append(live.LivePool(r["pool"],r["token_a"],r["token_b"],r["vault_a"],r["vault_b"],
                                 int(r.get("fee_numerator") or 25),int(r.get("fee_denominator") or 10000)))
    return out

def prepare(root):
    states=[];registry={}
    for d in descriptors(root):
        try:
            s=live.hydrate(d,c.account)
            i=len(states);states.append((d,s))
            registry[d.vault_a]=(i,d);registry[d.vault_b]=(i,d)
        except Exception as e:
            print("[DAMM_WARM_SKIP] pool=%s %s:%s"%(d.pool[:12],type(e).__name__,e),flush=True)
    return states,registry

def quote_edge(state_desc,input_mint,amount_in,now_ns=None):
    d,s=state_desc
    return live.quote(s,input_mint,int(amount_in),now_ns)

def apply_event(states,registry,address,raw,observed_ns):
    row=registry.get(address)
    if row is None:return False
    i,d=row
    return bool(live.update(states[i][1],d,address,raw,observed_ns))

def main():
    root=Path.cwd();states,reg=prepare(root)
    payload={"descriptors":len(descriptors(root)),"hydrated_states":len(states),
             "watched_accounts":len(reg),"max_age_ms":MAX_AGE_MS,
             "execution_authority":False}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    print("[QARB-052A6] DAMM GRAPH-READY LIVE ADAPTER")
    print("[DAMM_DESCRIPTORS]",payload["descriptors"])
    print("[DAMM_HYDRATED_STATES]",payload["hydrated_states"])
    print("[DAMM_WATCHED_ACCOUNTS]",payload["watched_accounts"])
    for d,_ in states: print("[DAMM_READY]",d.pool[:12],d.token_a[:12],d.token_b[:12])
    if states: print("[PASS] DAMM now exposes graph-ready hydrate/update/local-quote state")
    else: print("[HOLD] no DAMM state hydrated")
    print("[REPORT]",OUT)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
