from __future__ import annotations
import base64, json, os, time
from pathlib import Path
from urllib.request import Request, urlopen

from solders.hash import Hash
from solders.pubkey import Pubkey

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    qarb_024_existing_python_atomic_source_bridge as bridge,
)

RPC_URL=os.getenv("QARB_SOLANA_RPC",os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com"))
SIZES=tuple(float(x) for x in os.getenv("QARB_025E_SIZES_SOL","0.5").split(",") if x.strip())
MAX_PAIRS=int(os.getenv("QARB_025B_MAX_PAIRS","12"))
execution_authority=False

def rpc(method,params):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=Request(RPC_URL,data=body,headers={"Content-Type":"application/json"})
    with urlopen(req,timeout=20) as r:
        j=json.loads(r.read().decode())
    if j.get("error"):
        raise RuntimeError("RPC_ERROR:"+json.dumps(j["error"],sort_keys=True))
    return j.get("result")

def current_blockhash():
    r=rpc("getLatestBlockhash",[{"commitment":"confirmed"}])
    return Hash.from_string(r["value"]["blockhash"])

def resolve_sim_user(qsb):
    for raw in (
        os.getenv("QSB_SOLANA_WALLET"),
        os.getenv("QARB_SIM_PAYER"),
        getattr(qsb,"SIM_ONLY_PUBLIC_KEY",None),
        getattr(qsb,"DEFAULT_SIM_PAYER",None),
        getattr(qsb,"MRIYA_WALLET",None),
        getattr(qsb,"SIM_PAYER",None),
    ):
        if raw:
            try:return raw if isinstance(raw,Pubkey) else Pubkey.from_string(str(raw))
            except Exception:pass
    raise RuntimeError("SIM_PAYER_NOT_FOUND")

def meteora_pool_from_row(row):
    for k in ("meteora_pool","dlmm_pool","lb_pair","pool"):
        v=row.get(k)
        if v:return str(v)
    meta=row.get("meteora_meta")
    if isinstance(meta,dict):
        for k in ("pool","pool_address","lb_pair","address","pair"):
            v=meta.get(k)
            if v:return str(v)
    for name in ("pool","pool_address","lb_pair","address"):
        v=getattr(meta,name,None)
        if v:return str(v)
    return None

def live_cases(root):
    rows=engine.candidate_universe(Path(root))
    out=[]
    for row in rows:
        token=row.get("token")
        pump=row.get("pump_pool")
        meteora=meteora_pool_from_row(row)
        if token and pump and meteora:
            out.append((str(token),str(pump),str(meteora)))
        if len(out)>=MAX_PAIRS:break
    return out

def simulate(tx,payer):
    raw=bytes(tx)
    if len(raw)>1232:
        return {"ok":False,"stage":"PACKET","reason":"ATOMIC_TX_TOO_LARGE","tx_bytes":len(raw)}
    before=rpc("getBalance",[str(payer),{"commitment":"confirmed"}])["value"]
    b64=base64.b64encode(raw).decode()
    t0=time.perf_counter()
    r=rpc("simulateTransaction",[b64,{
        "encoding":"base64","sigVerify":False,"commitment":"confirmed",
        "accounts":{"encoding":"base64","addresses":[str(payer)]},
    }])
    dt=(time.perf_counter()-t0)*1000.0
    v=r.get("value") or {}
    acc=v.get("accounts") or []
    after=int(acc[0]["lamports"]) if acc and acc[0] and acc[0].get("lamports") is not None else None
    net=None if after is None else (after-int(before))/1e9
    return {"ok":v.get("err") is None,"err":v.get("err"),"logs":v.get("logs") or [],
            "units_consumed":v.get("unitsConsumed"),"tx_bytes":len(raw),
            "latency_ms":dt,"before":int(before),"after":after,"net_sol":net}

def run(root=None):
    root=Path(root or Path.cwd())
    print("[QARB-025E] AST EXACT CANDIDATE REPAIR",flush=True)
    print("[SOURCE] current qarb_clean_bot.engine.candidate_universe",flush=True)
    print("[FIX] AST bridge delegation -> exact qsb059 candidate ladder; one-size default",flush=True)
    print("[MODE] real simulateTransaction only execution_authority=FALSE",flush=True)

    qsb=bridge.load_source()
    user=resolve_sim_user(qsb)
    print("[SIM_PAYER] %s"%user,flush=True)

    try: cases=live_cases(root)
    except Exception as exc:
        print("[REAL_SIM_BLOCKED] stage=LIVE_DISCOVERY reason=%s:%s"%(type(exc).__name__,exc),flush=True);return

    print("[LIVE_BINDINGS] count=%d"%len(cases),flush=True)
    if not cases:
        print("[REAL_SIM_BLOCKED] stage=LIVE_DISCOVERY reason=NO_CURRENT_PUMPSWAP_METEORA_BINDINGS",flush=True);return

    try: bh=current_blockhash()
    except Exception as exc:
        print("[REAL_SIM_BLOCKED] stage=BLOCKHASH reason=%s:%s"%(type(exc).__name__,exc),flush=True);return

    compose_fail=packet_fail=0
    for i,(token,pump,meteora) in enumerate(cases,1):
        print("[LIVE_PAIR %d/%d] token=%s pump=%s meteora=%s"%(i,len(cases),token,pump,meteora),flush=True)
        for size in SIZES:
            try:
                route=bridge.compose_exact_candidates(str(user),token,pump,meteora,size)
            except Exception as exc:
                compose_fail+=1
                print("[COMPOSE_REJECT] token=%s size=%.6f reason=%s:%s"%(token,size,type(exc).__name__,exc),flush=True)
                continue

            rows=bridge.candidate_instruction_sets(route)
            if not rows:
                print("[COMPOSE_REJECT] token=%s size=%.6f reason=NO_INSTRUCTION_CANDIDATES"%(token,size),flush=True)
                continue

            for label,ixs,alts in rows:
                res=bridge.packet.compile_best_v0(
                    payer=user,recent_blockhash=bh,instructions=ixs,lookup_tables=alts)
                sz=None if res.best is None else res.best.size_bytes
                print("[ATOMIC_CANDIDATE] token=%s size=%.6f label=%s bytes=%s status=%s"%(
                    token,size,label,sz,res.status),flush=True)
                if not res.ok:
                    packet_fail+=1
                    continue

                tx=res.best.tx
                print("[ATOMIC_TX] token=%s size=%.6f label=%s bytes=%d <=1232=True"%(
                    token,size,label,len(bytes(tx))),flush=True)
                try: sim=simulate(tx,user)
                except Exception as exc:
                    print("[REAL_SIM_ERROR] token=%s size=%.6f %s:%s"%(
                        token,size,type(exc).__name__,exc),flush=True)
                    continue

                print("[REAL_SIMULATION] token=%s size=%.6f err=%s units_consumed=%s tx_bytes=%d latency_ms=%.2f"%(
                    token,size,sim["err"],sim["units_consumed"],sim["tx_bytes"],sim["latency_ms"]),flush=True)
                print("[SIM_BALANCE] before=%s after=%s net_sol=%s"%(
                    sim["before"],sim["after"],sim["net_sol"]),flush=True)
                profitable=bool(sim["ok"] and sim["net_sol"] is not None and sim["net_sol"]>0)
                print("[SIM_PROFITABLE] %s"%profitable,flush=True)
                print("[REALIZED_PNL] 0",flush=True)
                print("[EXECUTION_AUTHORITY] FALSE",flush=True)
                return

    print("[REAL_SIM_BLOCKED] stage=EXHAUSTED live_pairs=%d compose_failures=%d packet_failures=%d"%(
        len(cases),compose_fail,packet_fail),flush=True)
