from __future__ import annotations
import argparse,base64,json,os,subprocess,time,urllib.request
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r

STATE=Path("runtime_state/oracle/solana_atomic_executor/canonical_alt.json")
CREATE_ARM_VALUE="CREATE_CANONICAL_ALT"

def rpc(method,params):
    url=os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com")
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(url,data=body,headers={"content-type":"application/json"})
    with urllib.request.urlopen(req,timeout=20) as h:
        j=json.loads(h.read().decode())
    if j.get("error"):
        raise RuntimeError("RPC_%s:%s"%(method,j["error"]))
    return j["result"]

def atomic_write(path,data):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)

def choose_addresses(ixs,user):
    programs={str(x["programId"]) for x in ixs}
    out=[]; seen=set()
    for ix in ixs:
        for a in ix.get("accounts") or []:
            pk=str(a.get("pubkey") or "")
            if not pk or pk==str(user) or pk in programs or a.get("isSigner") or pk in seen:
                continue
            seen.add(pk); out.append(pk)
    if len(out)<4:
        raise RuntimeError("ALT_TOO_FEW_ELIGIBLE_ADDRESSES:%d"%len(out))
    return out[:8]

def build_setup(user,addresses):
    recent_slot=int(rpc("getSlot",[{"commitment":"finalized"}]))
    d=Path.cwd()/"qseries_v2/oracle_strategy_intelligence/solana_money/qsb059d_pump_native"
    req={"user":str(user),"recentSlot":recent_slot,"addresses":addresses}
    p=subprocess.run(["node","build_qarb096_alt_ix.mjs"],cwd=d,input=json.dumps(req),
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30)
    if p.returncode!=0:
        raise RuntimeError("ALT_NODE_FAILED:"+p.stderr[-1500:])
    j=json.loads(p.stdout.strip().splitlines()[-1])
    if not j.get("ok"):
        raise RuntimeError("ALT_BUILD_FAILED:"+str(j.get("reason")))
    return j

def prepare_route():
    state,_=r.q25.prepare_once(Path.cwd())
    r.q25.bind_cached_state(state)
    warmed=r.install_proven_hot_math(state)
    kp=r.q87.c.keypair()
    user=str(kp.pubkey())
    r.USER=user
    r.prebuild_templates(state,user)
    r.prebuild_meteora_templates(state,user,warmed)
    for pair in state.get("pairs") or []:
        token=str(pair.token)
        if token not in r.READY_TOKENS:
            continue
        r.q18.worker().warm(str(pair.pump_pool))
        snap=r.immutable_snapshot(pair)
        try:
            rows=r.q18.exact_snapshot_opportunities(
                snap,
                0.001
            )
        except RuntimeError as exc:
            if str(exc)=="DLMM_PARTIAL":
                print(
                    "[CANONICAL_ALT_PAIR_SKIP] "
                    "token=%s reason=DLMM_PARTIAL"
                    %token[:10],
                    flush=True,
                )
                continue
            raise

        opp=next(
            (
                x for x in rows
                if x["direction"]=="PUMP_TO_METEORA"
            ),
            None
        )

        if opp is None:
            continue
        route=r.same_snapshot_route(user,snap,opp)
        full=next(x for x in r.q87.repaired_candidates(route) if x["name"]=="FULL")
        return kp,user,token,full["instructions"]
    raise RuntimeError("NO_READY_FORWARD_PAIR")

def signed_simulate(raw):
    v=rpc("simulateTransaction",[base64.b64encode(raw).decode(),{
        "encoding":"base64","sigVerify":True,"commitment":"processed",
        "replaceRecentBlockhash":False}])
    return v.get("value") if isinstance(v,dict) else None

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--create",action="store_true")
    a=ap.parse_args(argv)
    kp,user,token,ixs=prepare_route()
    addresses=choose_addresses(ixs,user)
    setup=build_setup(user,addresses)
    bh=rpc("getLatestBlockhash",[{"commitment":"confirmed"}])["value"]["blockhash"]
    msg,unsigned=r.q87.c.compile_v0(user,setup["instructions"],[],bh)
    raw=r.q87.c.signed_tx(msg,kp)
    sim=signed_simulate(raw)
    if not isinstance(sim,dict):
        raise RuntimeError("ALT_SIM_VALUE_MISSING")
    print("[CANONICAL_ALT] token=%s table=%s addresses=%d bytes=%d"%(token[:10],setup["lookupTable"],len(addresses),len(raw)),flush=True)
    print("[CANONICAL_ALT_SIM] err=%s units=%s"%(sim.get("err"),sim.get("unitsConsumed")),flush=True)
    if sim.get("err") is not None:
        for line in sim.get("logs") or []:
            print("[CANONICAL_ALT_LOG] "+str(line),flush=True)
        return 2
    print("[CANONICAL_ALT_SIM_PASS] table=%s"%setup["lookupTable"],flush=True)
    if not a.create:
        print("[BROADCAST] disabled -- rerun with --create only after explicit arm",flush=True)
        return 0
    if os.getenv("ORACLE_CANONICAL_ALT_CREATE","")!=CREATE_ARM_VALUE:
        raise RuntimeError("CANONICAL_ALT_CREATE_NOT_ARMED")
    sig=rpc("sendTransaction",[base64.b64encode(raw).decode(),{
        "encoding":"base64","skipPreflight":False,"preflightCommitment":"processed","maxRetries":0}])
    print("[CANONICAL_ALT_SENT] signature=%s"%sig,flush=True)
    deadline=time.monotonic()+30
    tx=None
    while time.monotonic()<deadline:
        row=rpc("getTransaction",[sig,{"encoding":"json","commitment":"confirmed","maxSupportedTransactionVersion":0}])
        if row is not None:
            tx=row; break
        time.sleep(.5)
    if tx is None:
        raise RuntimeError("CANONICAL_ALT_CONFIRMATION_UNKNOWN")
    err=(tx.get("meta") or {}).get("err")
    if err is not None:
        raise RuntimeError("CANONICAL_ALT_CONFIRMED_ERROR:"+str(err))
    payload={"address":setup["lookupTable"],"addresses":addresses,"signature":sig,"slot":tx.get("slot"),"created_unix":time.time()}
    atomic_write(STATE,payload)
    print("[CANONICAL_ALT_READY] address=%s"%setup["lookupTable"],flush=True)
    print("[STATE] %s"%STATE,flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
