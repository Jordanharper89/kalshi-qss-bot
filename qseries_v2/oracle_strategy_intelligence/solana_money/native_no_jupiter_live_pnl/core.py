from __future__ import annotations
import base64,json,os,struct,time
from pathlib import Path
from urllib.request import Request,urlopen

WSOL="So11111111111111111111111111111111111111112"
PUMP_PID="pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
DLMM_PID="LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"
RPC=os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com")
START_SOL=float(os.getenv("QSB_051_START_SOL","0.025"))
PUMP_FEE_BPS=int(os.getenv("QSB_051_PUMP_FEE_BPS","100"))
MAX_TOKENS=int(os.getenv("QSB_051_MAX_TOKENS","4"))
MIN_NET_BPS=float(os.getenv("QSB_051_MIN_NET_BPS","10"))
TAPE="runtime_state/solana_opportunities/universal_trade_tape/multidex_universal_economic_tape.json"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58e(b):
    n=int.from_bytes(b,"big");s=""
    while n:
        n,r=divmod(n,58);s=ALPH[r]+s
    z=len(b)-len(b.lstrip(b"\0"))
    return "1"*z+(s or "")

def http_json(url,method="GET",body=None,timeout=15):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    h={"accept":"application/json","user-agent":"qseries-qsb051/1.0"}
    if data is not None:h["content-type"]="application/json"
    with urlopen(Request(url,data=data,headers=h,method=method),timeout=timeout) as r:
        return json.loads(r.read().decode())

def rpc(method,params):
    j=http_json(RPC,"POST",{"jsonrpc":"2.0","id":1,"method":method,"params":params},15)
    if j.get("error"):raise RuntimeError("RPC:"+json.dumps(j["error"]))
    return j.get("result")

def account_bytes(addr):
    x=rpc("getAccountInfo",[addr,{"encoding":"base64","commitment":"processed"}])
    if not x or not x.get("value"):raise RuntimeError("ACCOUNT_NOT_FOUND:"+addr)
    d=x["value"].get("data")
    return base64.b64decode(d[0])

def token_amount(addr):
    d=account_bytes(addr)
    if len(d)<72:raise RuntimeError("TOKEN_ACCOUNT_SHORT")
    return struct.unpack_from("<Q",d,64)[0]

def mint_decimals(addr):
    d=account_bytes(addr)
    if len(d)<45:raise RuntimeError("MINT_SHORT")
    return d[44]

def decode_pump_pool(d):
    if len(d)<8+1+2+32*6+8:raise RuntimeError("PUMP_POOL_SHORT")
    o=8
    bump=d[o];o+=1
    index=struct.unpack_from("<H",d,o)[0];o+=2
    creator=b58e(d[o:o+32]);o+=32
    base=b58e(d[o:o+32]);o+=32
    quote=b58e(d[o:o+32]);o+=32
    lp=b58e(d[o:o+32]);o+=32
    base_vault=b58e(d[o:o+32]);o+=32
    quote_vault=b58e(d[o:o+32]);o+=32
    lp_supply=struct.unpack_from("<Q",d,o)[0];o+=8
    coin_creator=b58e(d[o:o+32]) if len(d)>=o+32 else "11111111111111111111111111111111";o+=32
    mayhem=bool(d[o]) if len(d)>o else False;o+=1
    cashback=bool(d[o]) if len(d)>o else False;o+=1
    virtual_quote=int.from_bytes(d[o:o+16],"little",signed=True) if len(d)>=o+16 else 0
    return {"index":index,"creator":creator,"base_mint":base,"quote_mint":quote,
            "base_vault":base_vault,"quote_vault":quote_vault,"lp_supply":lp_supply,
            "coin_creator":coin_creator,"mayhem":mayhem,"cashback":cashback,
            "virtual_quote_reserves":virtual_quote}

def pump_sell_quote(pool_addr,token_in_raw):
    p=decode_pump_pool(account_bytes(pool_addr))
    if p["quote_mint"]!=WSOL:raise RuntimeError("PUMP_NOT_WSOL_PAIR")
    br=token_amount(p["base_vault"]);qr=token_amount(p["quote_vault"])+p["virtual_quote_reserves"]
    if br<=0 or qr<=0:raise RuntimeError("PUMP_ZERO_RESERVE")
    # Conservative local CPMM: charge configurable total input fee before invariant math.
    net_in=token_in_raw*(10000-PUMP_FEE_BPS)//10000
    out=qr*net_in//(br+net_in)
    return {"raw_out":int(out),"base_reserve":br,"quote_reserve":qr,"fee_bps":PUMP_FEE_BPS,"pool":p}

def rows(root):
    p=Path(root)/TAPE
    if not p.exists():return []
    d=json.loads(p.read_text(encoding="utf-8"))
    return d.get("exact_rows") or d.get("rows") or []

def candidates(root):
    best={}
    for x in rows(root):
        if x.get("venue")!="PUMP_SWAP":continue
        if x.get("quote_mint")!=WSOL:continue
        tok=x.get("token_address");pool=x.get("market_address")
        if not tok or not pool:continue
        slot=int(x.get("slot") or 0)
        if tok not in best or slot>best[tok][0]:best[tok]=(slot,pool)
    return [(t,v[1]) for t,v in sorted(best.items(),key=lambda z:z[1][0],reverse=True)[:MAX_TOKENS]]

def discover_dlmm(token):
    q=f"https://dlmm.datapi.meteora.ag/pools?page=1&page_size=100&query={token}"
    j=http_json(q);arr=j.get("data") if isinstance(j,dict) else j
    found=[]
    for x in arr or []:
        tx=x.get("token_x") or x.get("tokenX") or {};ty=x.get("token_y") or x.get("tokenY") or {}
        mx=(tx.get("address") or tx.get("mint") or tx.get("token_address")) if isinstance(tx,dict) else tx
        my=(ty.get("address") or ty.get("mint") or ty.get("token_address")) if isinstance(ty,dict) else ty
        if {mx,my}!={WSOL,token}:continue
        addr=x.get("address") or x.get("pool_address") or x.get("pubkey")
        if not addr:continue
        tvl=float(x.get("tvl") or x.get("liquidity") or x.get("liquidity_usd") or 0)
        dx=int(tx.get("decimals",9)) if isinstance(tx,dict) else 9
        dy=int(ty.get("decimals",9)) if isinstance(ty,dict) else 9
        found.append((tvl,{"address":addr,"token_x":mx,"token_y":my,"decimals_x":dx,"decimals_y":dy}))
    if not found:raise RuntimeError("NO_DLMM_PAIR")
    found.sort(reverse=True,key=lambda z:z[0]);return found[0][1]

def dlmm_quote(meta,start_sol):
    from meteora_dlmm import PoolState,quote
    lb=account_bytes(meta["address"])
    arr=rpc("getProgramAccounts",[DLMM_PID,{"encoding":"base64","commitment":"processed",
        "filters":[{"memcmp":{"offset":24,"bytes":meta["address"]}}]}]) or []
    bins=[]
    for x in arr:
        dat=((x.get("account") or {}).get("data") or [])
        if isinstance(dat,list) and dat:bins.append(base64.b64decode(dat[0]))
    if not bins:raise RuntimeError("NO_BIN_ARRAYS")
    p=PoolState.from_accounts(lb,bins,decimals_x=meta["decimals_x"],decimals_y=meta["decimals_y"],
                              lb_pair_key=meta["address"],exhaustive=True)
    if meta["token_x"]==WSOL:swap_for_y=True;indec=meta["decimals_x"]
    else:swap_for_y=False;indec=meta["decimals_y"]
    raw=int(round(start_sol*(10**indec)))
    q=quote(p,amount_in=raw,swap_for_y=swap_for_y,strict=True)
    if not q.complete or int(q.remaining_in or 0)!=0:raise RuntimeError("DLMM_PARTIAL")
    return {"raw_out":int(q.amount_out),"bins_crossed":int(q.bins_crossed or 0)}

def run(root):
    print("[QSB-051] NATIVE NO-JUPITER LIVE PNL",flush=True)
    print("[HOT_MATH] Meteora raw accounts+bins -> local DLMM math; PumpSwap raw vault balances -> local CPMM math",flush=True)
    print("[JUPITER] NONE",flush=True)
    cs=candidates(root);print("[TOKENS] %d"%len(cs),flush=True)
    best=None
    for token,pump_pool in cs:
        t=time.perf_counter()
        try:
            dm=discover_dlmm(token);mq=dlmm_quote(dm,START_SOL)
            pq=pump_sell_quote(pump_pool,mq["raw_out"])
            net=pq["raw_out"]/1e9-START_SOL
            bps=net/START_SOL*10000
            row={"token":token,"meteora_pool":dm["address"],"pump_pool":pump_pool,
                 "start_sol":START_SOL,"token_out_raw":mq["raw_out"],"end_sol":pq["raw_out"]/1e9,
                 "net_sol":net,"net_bps":bps,"latency_ms":(time.perf_counter()-t)*1000,
                 "profitable":bps>=MIN_NET_BPS}
            print("[PNL] token=%s net=%+.9f SOL bps=%+.2f latency_ms=%.1f PROFITABLE=%s"%(
                token[:10],net,bps,row["latency_ms"],row["profitable"]),flush=True)
            if best is None or bps>best["net_bps"]:best=row
        except Exception as e:
            print("[SKIP] token=%s %s"%(token[:10],e),flush=True)
    out={"revision":"QSB_051","jupiter":False,"execution_authority":False,"sent":False,"best":best}
    p=Path(root)/"runtime_state/qseries/qsb051_native_no_jupiter_live_pnl/report.json"
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2),encoding="utf-8")
    if best:print("[BEST_PNL] net=%+.9f SOL bps=%+.2f PROFITABLE=%s"%(best["net_sol"],best["net_bps"],best["profitable"]),flush=True)
    else:print("[BEST_PNL] NONE",flush=True)
    return out
