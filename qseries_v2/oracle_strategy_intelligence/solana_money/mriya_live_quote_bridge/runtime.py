from __future__ import annotations
import json,os,shutil,subprocess,time
from pathlib import Path

WSOL="So11111111111111111111111111111111111111112"
TARGET_TOKEN="CbyTNf7UPzvewHh4Zp6umogM2RWahhmGRJWLJnPwpump"
TARGET_WALLET="MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"

def _report(root):
    p=Path(root)/"runtime_state/qseries/qsb035_mriya_strategy_fingerprint/report.json"
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return {}

def _template(root):
    rows=(_report(root).get("records") or [])
    good=[]
    for r in rows:
        if r.get("failed"):continue
        if tuple(r.get("venue_chain") or ())!=("METEORA_DLMM","PUMP_SWAP"):continue
        c=r.get("chain") or {}
        if not c.get("closed") or not c.get("contiguous"):continue
        b=float(c.get("gross_bps") or 0)
        if not (0<b<=500):continue
        legs=c.get("legs") or []
        if len(legs)!=2:continue
        path=(legs[0].get("input_asset"),legs[0].get("output_asset"),legs[1].get("output_asset"))
        if path!=(WSOL,TARGET_TOKEN,WSOL):continue
        good.append(r)
    if len(good)<2:return None
    sizes=sorted(float((r.get("chain") or {}).get("start_amount") or 0) for r in good)
    fees=[float(r.get("fee_sol") or 0) for r in good]
    return {"wins":len(good),"sizes":sizes,"historical_avg_fee_sol":sum(fees)/len(fees),
            "historical_avg_gross_bps":sum(float((r.get("chain") or {}).get("gross_bps")) for r in good)/len(good)}

def _bridge_dir(root):
    return Path(root)/"qseries_v2/oracle_strategy_intelligence/solana_money/mriya_live_quote_bridge/node_bridge"

def ensure_node_dependencies(root):
    b=_bridge_dir(root)
    if shutil.which("node") is None:return {"ok":False,"reason":"NODE_NOT_FOUND"}
    if shutil.which("npm") is None:return {"ok":False,"reason":"NPM_NOT_FOUND"}
    marker=b/"node_modules/@pump-fun/pump-swap-sdk/package.json"
    marker2=b/"node_modules/@meteora-ag/dlmm/package.json"
    if marker.is_file() and marker2.is_file():return {"ok":True,"installed_now":False}
    print("[NODE] installing official Meteora + PumpSwap SDK dependencies once...",flush=True)
    p=subprocess.run(["npm","install","--silent","--no-audit","--no-fund"],cwd=b,text=True,
                     stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240)
    if p.returncode!=0:return {"ok":False,"reason":"NPM_INSTALL_FAILED","output":p.stdout[-3000:]}
    return {"ok":marker.is_file() and marker2.is_file(),"installed_now":True,
            "reason":None if marker.is_file() and marker2.is_file() else "SDK_MARKER_MISSING"}

def run_bridge(root,start_amount,tx_cost_sol):
    b=_bridge_dir(root)
    req={"rpc":os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com"),
         "targetWallet":TARGET_WALLET,"token":TARGET_TOKEN,"wsol":WSOL,
         "startSol":float(start_amount),"txCostSol":float(tx_cost_sol)}
    p=subprocess.run(["node","quote_bridge.mjs"],cwd=b,input=json.dumps(req),text=True,
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
    if p.returncode!=0:
        return {"ok":False,"reason":"NODE_BRIDGE_FAILED","stderr":p.stderr[-4000:],"stdout":p.stdout[-4000:]}
    try:return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:return {"ok":False,"reason":"BAD_NODE_JSON","stdout":p.stdout[-4000:],"stderr":p.stderr[-4000:]}

def main():
    root=Path.cwd()
    print("[QSB-037] MRIYA LIVE PRE-TRADE QUOTE BRIDGE",flush=True)
    print("[ROUTE] WSOL -> METEORA_DLMM -> CbyTNf...pump -> PUMP_SWAP -> WSOL",flush=True)
    print("[SOURCE] official Meteora DLMM SDK + official PumpSwap SDK; current RPC state",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    t=_template(root)
    if not t:
        print("[HOLD] clean repeated QSB-035 template missing",flush=True);return
    print("[TEMPLATE]",t,flush=True)
    dep=ensure_node_dependencies(root)
    print("[DEPENDENCIES]",dep,flush=True)
    if not dep.get("ok"):
        print("[HOLD] "+str(dep.get("reason")),flush=True);return
    sizes=[t["sizes"][0],sum(t["sizes"])/len(t["sizes"]),t["sizes"][-1]]
    # Historical base fee is measured; extra 0.0001 SOL is conservative landing/priority buffer for paper admission.
    tx_cost=max(float(t["historical_avg_fee_sol"]),0.0001)
    admitted=0
    for size in sizes:
        q=run_bridge(root,size,tx_cost)
        if not q.get("ok"):
            print("[QUOTE_FAIL] size=%.9f reason=%s detail=%s"%(size,q.get("reason"),q),flush=True);continue
        print("[LIVE_QUOTE] size=%.9f meteora_pool=%s pump_pool=%s token_out=%s sol_out=%s slot_start=%s slot_end=%s elapsed_ms=%s"%(
              size,q.get("meteoraPool"),q.get("pumpPool"),q.get("tokenOutUi"),q.get("solOutUi"),
              q.get("slotStart"),q.get("slotEnd"),q.get("elapsedMs")),flush=True)
        print("[PAPER_PNL] start=%.9f gross_end=%.9f tx_cost=%.9f net=%.9f net_bps=%.2f qualified=%s"%(
              size,float(q["solOutUi"]),tx_cost,float(q["netSol"]),float(q["netBps"]),q["qualified"]),flush=True)
        if q.get("qualified"):admitted+=1
    print("[SUMMARY] sizes_tested=%d paper_admitted=%d execution_authority=FALSE"%(len(sizes),admitted),flush=True)

if __name__=="__main__":main()
