from __future__ import annotations
import base64, json, os, time
from urllib.request import Request, urlopen

from solders.hash import Hash
from solders.pubkey import Pubkey

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    qarb_024_existing_python_atomic_source_bridge as bridge,
)

TOKEN = "GavQxkBXLg9Qwvxgni8SLJAnxLL592j55jVS2fnFpump"
PUMP_POOL = "7wJSkAxZbKUEGcZPRUxBiQzwkPdmsepRvsvcJuyBWGwU"
METEORA_POOL = "2Tua3TMvtZtWqQmut5NGYXYxARo297W3JHdnFBCTQEmn"
START_SOL = float(os.getenv("QARB_025_START_SOL", "0.05"))
RPC_URL = os.getenv("QARB_SOLANA_RPC", os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"))
execution_authority = False

def rpc(method, params):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req = Request(RPC_URL, data=body, headers={"Content-Type":"application/json"})
    with urlopen(req, timeout=20) as r:
        j = json.loads(r.read().decode())
    if j.get("error"):
        raise RuntimeError("RPC_ERROR:"+json.dumps(j["error"], sort_keys=True))
    return j.get("result")

def _pubkey(value):
    if isinstance(value, Pubkey):
        return value
    return Pubkey.from_string(str(value))

def resolve_sim_user(qsb):
    env = os.getenv("QSB_SOLANA_WALLET") or os.getenv("QARB_SIM_PAYER")
    if env:
        return _pubkey(env)
    for name in ("SIM_ONLY_PUBLIC_KEY","DEFAULT_SIM_PAYER","MRIYA_WALLET","SIM_PAYER"):
        value = getattr(qsb, name, None)
        if value:
            try:
                return _pubkey(value)
            except Exception:
                pass
    raise RuntimeError("SIM_PAYER_NOT_FOUND_SET_QSB_SOLANA_WALLET")

def blockhash():
    r = rpc("getLatestBlockhash", [{"commitment":"confirmed"}])
    return Hash.from_string(r["value"]["blockhash"])

def balance(pubkey):
    r = rpc("getBalance", [str(pubkey), {"commitment":"confirmed"}])
    return int(r["value"])

def simulate(tx, payer):
    raw = bytes(tx)
    if len(raw) > 1232:
        return {"ok":False,"stage":"PACKET","reason":"ATOMIC_TX_TOO_LARGE","tx_bytes":len(raw)}
    b64 = base64.b64encode(raw).decode()
    before = balance(payer)
    t0 = time.perf_counter()
    r = rpc("simulateTransaction", [
        b64,
        {
            "encoding":"base64",
            "sigVerify":False,
            "commitment":"confirmed",
            "accounts":{"encoding":"base64","addresses":[str(payer)]},
        }
    ])
    latency_ms = (time.perf_counter()-t0)*1000.0
    v = r.get("value") or {}
    accounts = v.get("accounts") or []
    after = None
    if accounts and accounts[0]:
        after = int(accounts[0].get("lamports"))
    err = v.get("err")
    net_lamports = None if after is None else after-before
    return {
        "ok": err is None,
        "stage":"SIMULATION",
        "err":err,
        "logs":v.get("logs") or [],
        "units_consumed":v.get("unitsConsumed"),
        "tx_bytes":len(raw),
        "latency_ms":latency_ms,
        "before_lamports":before,
        "after_lamports":after,
        "net_lamports":net_lamports,
        "net_sol":None if net_lamports is None else net_lamports/1e9,
    }

def run():
    print("[QARB-025] REAL ATOMIC SIMULATION", flush=True)
    print("[ROUTE] WSOL -> PumpSwap -> token -> Meteora DLMM -> WSOL", flush=True)
    print("[CASE] token=%s pump=%s meteora=%s size=%.6f"%(TOKEN,PUMP_POOL,METEORA_POOL,START_SOL), flush=True)
    print("[MODE] real simulateTransaction only execution_authority=FALSE", flush=True)

    qsb = bridge.load_source()
    user = resolve_sim_user(qsb)
    print("[SIM_PAYER] %s"%user, flush=True)

    try:
        route = bridge.compose_exact_candidates(user, TOKEN, PUMP_POOL, METEORA_POOL, START_SOL)
    except Exception as exc:
        print("[REAL_SIM_BLOCKED] stage=COMPOSE reason=%s:%s"%(type(exc).__name__,exc), flush=True)
        return {"ok":False,"stage":"COMPOSE","reason":str(exc)}

    rows = bridge.candidate_instruction_sets(route)
    print("[COMPOSED] candidates=%d"%len(rows), flush=True)
    if not rows:
        print("[REAL_SIM_BLOCKED] stage=COMPOSE reason=NO_EXACT_ATOMIC_INSTRUCTION_CANDIDATES", flush=True)
        return {"ok":False,"stage":"COMPOSE","reason":"NO_EXACT_ATOMIC_INSTRUCTION_CANDIDATES"}

    try:
        bh = blockhash()
    except Exception as exc:
        print("[REAL_SIM_BLOCKED] stage=BLOCKHASH reason=%s:%s"%(type(exc).__name__,exc), flush=True)
        return {"ok":False,"stage":"BLOCKHASH","reason":str(exc)}

    selected = None
    attempts = []
    for label, ixs, alts in rows:
        result = bridge.packet.compile_best_v0(
            payer=user,
            recent_blockhash=bh,
            instructions=ixs,
            lookup_tables=alts,
        )
        size = None if result.best is None else result.best.size_bytes
        attempts.append((label,size,result.status))
        print("[ATOMIC_CANDIDATE] label=%s bytes=%s status=%s"%(label,size,result.status), flush=True)
        if result.ok:
            selected = (label,result.best.tx)
            break

    if selected is None:
        best_sizes = [x[1] for x in attempts if isinstance(x[1], int)]
        best = min(best_sizes) if best_sizes else None
        print("[REAL_SIM_BLOCKED] stage=PACKET reason=NO_PACKET_FIT best_bytes=%s limit=1232"%best, flush=True)
        return {"ok":False,"stage":"PACKET","best_bytes":best,"attempts":attempts}

    label, tx = selected
    print("[ATOMIC_TX] label=%s bytes=%d <=1232=True"%(label,len(bytes(tx))), flush=True)

    try:
        sim = simulate(tx,user)
    except Exception as exc:
        print("[REAL_SIM_ERROR] %s:%s"%(type(exc).__name__,exc), flush=True)
        return {"ok":False,"stage":"SIMULATION_RPC","reason":str(exc)}

    print("[REAL_SIMULATION] err=%s units_consumed=%s tx_bytes=%s latency_ms=%.2f"%(
        sim["err"],sim["units_consumed"],sim["tx_bytes"],sim["latency_ms"]), flush=True)
    print("[SIM_BALANCE] before=%s after=%s net_sol=%s"%(
        sim["before_lamports"],sim["after_lamports"],sim["net_sol"]), flush=True)
    print("[SIM_PROFITABLE] %s"%(sim["ok"] and sim["net_sol"] is not None and sim["net_sol"]>0), flush=True)
    print("[REALIZED_PNL] 0", flush=True)
    print("[EXECUTION_AUTHORITY] FALSE", flush=True)
    return sim
