from __future__ import annotations
import base64,json,math,os,subprocess,sys,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

WSOL="So11111111111111111111111111111111111111112"
TOKEN="CbyTNf7UPzvewHh4Zp6umogM2RWahhmGRJWLJnPwpump"
WALLET="MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"
DLMM_PROGRAM="LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"
METEORA_API="https://dlmm.datapi.meteora.ag"
PUMP_SWAP_API="https://fun-block.pump.fun/agents/swap"
DEFAULT_RPC="https://api.mainnet-beta.solana.com"
MIN_NET_BPS=10.0
MAX_SLOT_SPREAD=4

def http_json(url,method="GET",body=None,timeout=15):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    headers={"accept":"application/json","user-agent":"qseries-qsb038/1.0"}
    if data is not None:headers["content-type"]="application/json"
    req=Request(url,data=data,headers=headers,method=method)
    with urlopen(req,timeout=timeout) as r:
        return json.loads(r.read().decode())

def rpc(url,method,params,timeout=15):
    return http_json(url,"POST",{"jsonrpc":"2.0","id":1,"method":method,"params":params},timeout).get("result")

def ensure_meteora_math():
    try:
        import meteora_dlmm
        return {"ok":True,"installed_now":False,"version":getattr(meteora_dlmm,"__version__","unknown")}
    except Exception:
        p=subprocess.run([sys.executable,"-m","pip","install","--disable-pip-version-check","--quiet","meteora-dlmm==0.3.0"],
                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)
        if p.returncode!=0:return {"ok":False,"reason":"PIP_INSTALL_FAILED","output":p.stdout[-2500:]}
        try:
            import meteora_dlmm
            return {"ok":True,"installed_now":True,"version":getattr(meteora_dlmm,"__version__","unknown")}
        except Exception as e:return {"ok":False,"reason":"IMPORT_AFTER_INSTALL_FAILED","error":repr(e)}

def report(root):
    p=Path(root)/"runtime_state/qseries/qsb035_mriya_strategy_fingerprint/report.json"
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return {}

def clean_sizes(root):
    xs=[]
    for r in report(root).get("records") or []:
        if r.get("failed") or tuple(r.get("venue_chain") or ())!=("METEORA_DLMM","PUMP_SWAP"):continue
        c=r.get("chain") or {};bps=float(c.get("gross_bps") or 0)
        if not (c.get("closed") and c.get("contiguous") and 0<bps<=500):continue
        legs=c.get("legs") or []
        if len(legs)!=2:continue
        if (legs[0].get("input_asset"),legs[0].get("output_asset"),legs[1].get("output_asset"))!=(WSOL,TOKEN,WSOL):continue
        s=float(c.get("start_amount") or 0)
        if s>0:xs.append(s)
    return sorted(xs)

def _mint(o):
    if isinstance(o,str):return o
    if not isinstance(o,dict):return ""
    for k in ("address","mint","token_address"):
        if isinstance(o.get(k),str):return o[k]
    return ""

def _dec(o):
    if not isinstance(o,dict):return None
    for k in ("decimals","decimal"):
        try:return int(o[k])
        except Exception:pass
    return None

def _tvl(o):
    for k in ("tvl","liquidity","liquidity_usd"):
        try:return float(o.get(k) or 0)
        except Exception:pass
    return 0.0

def discover_meteora_pool(http=http_json):
    j=http(f"{METEORA_API}/pools?page=1&page_size=100&query={TOKEN}")
    rows=j.get("data") if isinstance(j,dict) else j
    cand=[]
    for x in rows or []:
        tx=x.get("token_x") or x.get("tokenX") or {}
        ty=x.get("token_y") or x.get("tokenY") or {}
        mx,my=_mint(tx),_mint(ty)
        if {mx,my}!={WSOL,TOKEN}:continue
        addr=x.get("address") or x.get("pool_address") or x.get("pubkey")
        if not addr:continue
        cand.append((_tvl(x),{"address":str(addr),"token_x":mx,"token_y":my,
                              "decimals_x":_dec(tx),"decimals_y":_dec(ty),"raw":x}))
    if not cand:raise RuntimeError("NO_METEORA_WS0L_TARGET_POOL")
    cand.sort(key=lambda z:z[0],reverse=True)
    return cand[0][1]

def fetch_account_bytes(rpc_url,address):
    x=rpc(rpc_url,"getAccountInfo",[address,{"encoding":"base64","commitment":"processed"}])
    if not x or not x.get("value"):raise RuntimeError("ACCOUNT_NOT_FOUND:"+address)
    d=x["value"].get("data")
    if not (isinstance(d,list) and d):raise RuntimeError("ACCOUNT_DATA_MISSING:"+address)
    return base64.b64decode(d[0])

def fetch_bin_arrays(rpc_url,pool):
    rows=rpc(rpc_url,"getProgramAccounts",[DLMM_PROGRAM,{"encoding":"base64","commitment":"processed",
             "filters":[{"memcmp":{"offset":24,"bytes":pool}}]}])
    out=[]
    for x in rows or []:
        d=((x.get("account") or {}).get("data"))
        if isinstance(d,list) and d:
            try:out.append(base64.b64decode(d[0]))
            except Exception:pass
    if not out:raise RuntimeError("NO_DLMM_BIN_ARRAYS")
    return out

def meteora_quote(rpc_url,pool_meta,start_sol):
    from meteora_dlmm import PoolState,quote
    dx=pool_meta.get("decimals_x");dy=pool_meta.get("decimals_y")
    if dx is None or dy is None:raise RuntimeError("METEORA_DECIMALS_MISSING")
    lb=fetch_account_bytes(rpc_url,pool_meta["address"])
    bins=fetch_bin_arrays(rpc_url,pool_meta["address"])
    p=PoolState.from_accounts(lb,bins,decimals_x=int(dx),decimals_y=int(dy),
                              exhaustive=True)
    if pool_meta["token_x"]==WSOL:
        swap_for_y=True;in_dec=int(dx);out_dec=int(dy)
    elif pool_meta["token_y"]==WSOL:
        swap_for_y=False;in_dec=int(dy);out_dec=int(dx)
    else:raise RuntimeError("METEORA_POOL_DIRECTION_INVALID")
    raw_in=int(round(float(start_sol)*(10**in_dec)))
    q=quote(p,amount_in=raw_in,swap_for_y=swap_for_y,strict=True)
    if not getattr(q,"complete",False) or int(getattr(q,"remaining_in",0) or 0)!=0:
        raise RuntimeError("METEORA_PARTIAL_QUOTE")
    raw_out=int(q.amount_out)
    return {"exact":True,"raw_in":raw_in,"raw_out":raw_out,"out_ui":raw_out/(10**out_dec),
            "out_decimals":out_dec,"bins_crossed":int(getattr(q,"bins_crossed",0) or 0)}

def pump_quote(raw_token_in,http=http_json):
    body={"inputMint":TOKEN,"outputMint":WSOL,"amount":str(int(raw_token_in)),
          "user":WALLET,"slippagePct":0,"frontRunningProtection":False,"tipAmount":0,"encoding":"base64"}
    j=http(PUMP_SWAP_API,"POST",body,20)
    info=j.get("pumpMintInfo") if isinstance(j,dict) else None
    if not isinstance(info,dict):raise RuntimeError("PUMP_RESPONSE_NO_MINT_INFO")
    val=info.get("expectedOutAmount")
    if val is None:raise RuntimeError("PUMP_RESPONSE_NO_EXPECTED_OUT")
    raw=int(val)
    if raw<=0:raise RuntimeError("PUMP_EXPECTED_OUT_NONPOSITIVE")
    return {"exact":True,"raw_in":int(raw_token_in),"raw_out":raw,"sol_out":raw/1e9,
            "graduated":info.get("hasGraduated"),"pump_mint_info":info}

def pnl(start_sol,sol_out,tx_cost_sol):
    net=float(sol_out)-float(start_sol)-float(tx_cost_sol)
    bps=net/float(start_sol)*10000
    return {"start_sol":float(start_sol),"gross_end_sol":float(sol_out),"tx_cost_sol":float(tx_cost_sol),
            "net_sol":net,"net_bps":bps,"qualified":bps>=MIN_NET_BPS}

def one_quote(root,start_sol,http=http_json,rpc_fn=rpc):
    rpc_url=os.getenv("SOLANA_RPC_URL",DEFAULT_RPC)
    # slot calls are deliberately external to rpc_fn helpers so tests can patch global rpc.
    slot0=rpc_fn(rpc_url,"getSlot",[{"commitment":"processed"}])
    pool=discover_meteora_pool(http)
    mq=meteora_quote(rpc_url,pool,start_sol)
    pq=pump_quote(mq["raw_out"],http)
    slot1=rpc_fn(rpc_url,"getSlot",[{"commitment":"processed"}])
    spread=abs(int(slot1)-int(slot0))
    # Conservative fixed paper buffer; actual tx-cost model gets replaced only by measured simulation.
    tx_cost=max(0.0001,5_520/1e9)
    x=pnl(start_sol,pq["sol_out"],tx_cost)
    x.update({"slot_start":int(slot0),"slot_end":int(slot1),"slot_spread":spread,
              "fresh":spread<=MAX_SLOT_SPREAD,"meteora":mq,"pump":pq,"pool":pool["address"]})
    x["paper_trade"]=bool(x["qualified"] and x["fresh"])
    return x
