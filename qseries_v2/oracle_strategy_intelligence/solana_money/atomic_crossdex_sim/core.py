from __future__ import annotations
import base64,json,os,struct,time,urllib.parse,urllib.request
from pathlib import Path

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
WSOL="So11111111111111111111111111111111111111112"
TOKEN=os.getenv("QSB_049_TOKEN","CbyTNf7UPzvewHh4Zp6umogM2RWahhmGRJWLJnPwpump")
BUY_DEX=os.getenv("QSB_049_BUY_DEX","Meteora DLMM")
SELL_DEX=os.getenv("QSB_049_SELL_DEX","Pump.fun Amm")
START_SOL=float(os.getenv("QSB_049_START_SOL","0.025"))
SLIPPAGE_BPS=int(os.getenv("QSB_049_SLIPPAGE_BPS","25"))
CU_LIMIT=int(os.getenv("QSB_049_CU_LIMIT","1000000"))
CU_PRICE=int(os.getenv("QSB_049_CU_PRICE_MICROLAMPORTS","25000"))
MIN_SIM_NET_BPS=float(os.getenv("QSB_049_MIN_SIM_NET_BPS","10"))
RPC=os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com")
JUP_KEY=os.getenv("JUPITER_API_KEY","").strip()
JUP_BASE="https://api.jup.ag/swap/v1" if JUP_KEY else "https://lite-api.jup.ag/swap/v1"

def b58decode(s):
    n=0
    for ch in s:
        n=n*58+ALPH.index(ch)
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    pad=len(s)-len(s.lstrip("1"))
    return b"\0"*pad+raw

def shortvec(n):
    out=bytearray()
    while True:
        elem=n&0x7f;n>>=7
        if n: elem|=0x80
        out.append(elem)
        if not n:return bytes(out)

def _http(url,method="GET",body=None,timeout=20):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    h={"accept":"application/json","user-agent":"qseries-qsb049/1.0"}
    if data is not None:h["content-type"]="application/json"
    if JUP_KEY:h["x-api-key"]=JUP_KEY
    req=urllib.request.Request(url,data=data,headers=h,method=method)
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode())

def rpc(method,params,timeout=20):
    j=_http(RPC,"POST",{"jsonrpc":"2.0","id":1,"method":method,"params":params},timeout)
    if j.get("error"):raise RuntimeError("RPC_ERROR:"+json.dumps(j["error"]))
    return j.get("result")

def wallet_pubkey():
    x=os.getenv("QSB_SOLANA_WALLET","").strip()
    if x:return x
    sec=os.getenv("QSB_SOLANA_PRIVATE_KEY","").strip()
    if not sec:return "MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"
    try:
        if sec.startswith("["):
            a=bytes(int(v) for v in json.loads(sec))
        else:a=b58decode(sec)
        if len(a)!=64:raise ValueError("secret must decode to 64 bytes")
        # Standard Solana keypair encoding: final 32 bytes are the public key.
        pub=a[32:]
        n=int.from_bytes(pub,"big");chars=""
        while n:
            n,r=divmod(n,58);chars=ALPH[r]+chars
        z=len(pub)-len(pub.lstrip(b"\0"))
        return "1"*z+(chars or "")
    except Exception as e:raise RuntimeError("PRIVATE_KEY_PUBLIC_DERIVATION_FAILED:"+str(e))

def quote(inp,out,amount,dex):
    q=urllib.parse.urlencode({"inputMint":inp,"outputMint":out,"amount":str(int(amount)),
        "swapMode":"ExactIn","slippageBps":str(SLIPPAGE_BPS),"dexes":dex,"onlyDirectRoutes":"true"})
    j=_http(JUP_BASE+"/quote?"+q)
    rp=j.get("routePlan") or []
    if len(rp)!=1:raise RuntimeError("NO_SINGLE_DIRECT_ROUTE:"+dex)
    label=((rp[0] or {}).get("swapInfo") or {}).get("label")
    if label!=dex:raise RuntimeError("DEX_PIN_MISMATCH:%s!=%s"%(label,dex))
    return j

def swap_ixs(user,qr):
    body={"userPublicKey":user,"payer":user,"quoteResponse":qr,
          "wrapAndUnwrapSol":True,"useSharedAccounts":True,
          "asLegacyTransaction":False,"dynamicComputeUnitLimit":False,
          "skipUserAccountsRpcCalls":False}
    j=_http(JUP_BASE+"/swap-instructions","POST",body)
    if j.get("error"):raise RuntimeError("SWAP_INSTRUCTIONS:"+str(j["error"]))
    if not j.get("swapInstruction"):raise RuntimeError("SWAP_INSTRUCTION_MISSING")
    return j

def _ixkey(x):
    return (x.get("programId"),tuple((a.get("pubkey"),bool(a.get("isSigner")),bool(a.get("isWritable"))) for a in x.get("accounts") or []),x.get("data"))

def compute_ixs():
    return [
      {"programId":"ComputeBudget111111111111111111111111111111","accounts":[],
       "data":base64.b64encode(bytes([2])+struct.pack("<I",CU_LIMIT)).decode()},
      {"programId":"ComputeBudget111111111111111111111111111111","accounts":[],
       "data":base64.b64encode(bytes([3])+struct.pack("<Q",CU_PRICE)).decode()},
    ]

def compose_instruction_json(a,b):
    out=compute_ixs();seen={_ixkey(x) for x in out}
    def add(x):
        if not x:return
        k=_ixkey(x)
        if k not in seen:seen.add(k);out.append(x)
    for x in a.get("setupInstructions") or []:add(x)
    for x in a.get("otherInstructions") or []:add(x)
    add(a["swapInstruction"])
    for x in b.get("setupInstructions") or []:add(x)
    for x in b.get("otherInstructions") or []:add(x)
    add(b["swapInstruction"])
    # Cleanups must happen after both swaps. Dedupe if both legs use same wrapped-SOL account.
    add(b.get("cleanupInstruction"));add(a.get("cleanupInstruction"))
    return out

def _alt_accounts(addrs):
    if not addrs:return {}
    vals=(rpc("getMultipleAccounts",[addrs,{"encoding":"base64","commitment":"processed"}]) or {}).get("value") or []
    out={}
    for key,val in zip(addrs,vals):
        if not val:continue
        dat=base64.b64decode((val.get("data") or [""])[0])
        if len(dat)<56 or (len(dat)-56)%32:raise RuntimeError("ALT_LAYOUT_UNEXPECTED:"+key)
        out[key]=[dat[i:i+32] for i in range(56,len(dat),32)]
    return out

def compile_v0(payer,ixs,alt_keys,blockhash):
    payer_b=b58decode(payer)
    if len(payer_b)!=32:raise RuntimeError("BAD_PAYER")
    order=[];meta={}
    def touch(pk,s=False,w=False,program=False):
        b=b58decode(pk)
        if len(b)!=32:raise RuntimeError("BAD_PUBKEY:"+pk)
        if b not in meta:
            order.append(b);meta[b]={"signer":s,"writable":w,"program":program}
        else:
            meta[b]["signer"]|=s;meta[b]["writable"]|=w;meta[b]["program"]|=program
    touch(payer,True,True)
    for ix in ixs:
        touch(ix["programId"],False,False,True)
        for a in ix.get("accounts") or []:touch(a["pubkey"],bool(a.get("isSigner")),bool(a.get("isWritable")))
    unknown=[b for b,m in meta.items() if m["signer"] and b!=payer_b]
    if unknown:raise RuntimeError("EXTRA_SIGNER_REQUIRED")
    tables=_alt_accounts(alt_keys)
    chosen={};lookups=[]
    for tkey in alt_keys:
        arr=tables.get(tkey) or [];pos={b:i for i,b in enumerate(arr)}
        wr=[];ro=[]
        for b in order:
            m=meta[b]
            if b==payer_b or m["signer"] or m["program"] or b in chosen:continue
            if b in pos:
                idx=pos[b]
                if idx>255:continue
                chosen[b]=(tkey,idx,m["writable"])
                (wr if m["writable"] else ro).append(idx)
        if wr or ro:lookups.append((tkey,wr,ro,arr))
    static=[b for b in order if b not in chosen]
    sw=[b for b in static if meta[b]["signer"] and meta[b]["writable"]]
    sr=[b for b in static if meta[b]["signer"] and not meta[b]["writable"]]
    uw=[b for b in static if not meta[b]["signer"] and meta[b]["writable"]]
    ur=[b for b in static if not meta[b]["signer"] and not meta[b]["writable"]]
    if payer_b in sw:sw.remove(payer_b)
    static=[payer_b]+sw+sr+uw+ur
    loaded_w=[];loaded_r=[]
    for _,wr,ro,arr in lookups:
        loaded_w += [arr[i] for i in wr]
    for _,wr,ro,arr in lookups:
        loaded_r += [arr[i] for i in ro]
    allkeys=static+loaded_w+loaded_r
    index={b:i for i,b in enumerate(allkeys)}
    if len(allkeys)>256:raise RuntimeError("TOO_MANY_ACCOUNTS")
    hdr=bytes([1,0,len(ur)])
    bh=b58decode(blockhash)
    if len(bh)!=32:raise RuntimeError("BAD_BLOCKHASH")
    msg=bytearray(b"\x80"+hdr+shortvec(len(static))+b"".join(static)+bh+shortvec(len(ixs)))
    for ix in ixs:
        pid=b58decode(ix["programId"])
        ac=[index[b58decode(a["pubkey"])] for a in ix.get("accounts") or []]
        dat=base64.b64decode(ix.get("data") or "")
        msg += bytes([index[pid]])+shortvec(len(ac))+bytes(ac)+shortvec(len(dat))+dat
    msg += shortvec(len(lookups))
    for tkey,wr,ro,_ in lookups:
        msg += b58decode(tkey)+shortvec(len(wr))+bytes(wr)+shortvec(len(ro))+bytes(ro)
    tx=shortvec(1)+b"\0"*64+bytes(msg)
    if len(tx)>1232:raise RuntimeError("TX_TOO_LARGE:%d"%len(tx))
    return bytes(msg),tx,{"static":len(static),"loaded_writable":len(loaded_w),"loaded_readonly":len(loaded_r),"tx_bytes":len(tx)}

def simulate(user,tx):
    cfg={"encoding":"base64","commitment":"processed","sigVerify":False,"replaceRecentBlockhash":False,
         "innerInstructions":True}
    v=rpc("simulateTransaction",[base64.b64encode(tx).decode(),cfg])
    if not isinstance(v,dict):raise RuntimeError("SIMULATION_MISSING")
    err=v.get("err");pre=v.get("preBalances") or [];post=v.get("postBalances") or []
    pnl=(int(post[0])-int(pre[0])) if pre and post else None
    return {"err":err,"fee_lamports":v.get("fee"),"units":v.get("unitsConsumed"),
            "pre_lamports":pre[0] if pre else None,"post_lamports":post[0] if post else None,
            "pnl_lamports":pnl,"logs":v.get("logs") or []}

def run(root):
    t0=time.perf_counter()
    user=wallet_pubkey();start=int(round(START_SOL*1e9))
    q1=quote(WSOL,TOKEN,start,BUY_DEX)
    q2=quote(TOKEN,WSOL,int(q1["outAmount"]),SELL_DEX)
    quote_floor=int(q2["otherAmountThreshold"])-start
    print("[QUOTE_PNL] net_floor=%+.9f SOL bps=%+.2f"%(quote_floor/1e9,quote_floor/start*10000),flush=True)
    a=swap_ixs(user,q1);b=swap_ixs(user,q2)
    ixs=compose_instruction_json(a,b)
    alts=[]
    for z in (a,b):
        for k in z.get("addressLookupTableAddresses") or []:
            if k not in alts:alts.append(k)
    bh=(rpc("getLatestBlockhash",[{"commitment":"processed"}]) or {}).get("value",{}).get("blockhash")
    if not bh:raise RuntimeError("BLOCKHASH_MISSING")
    msg,tx,shape=compile_v0(user,ixs,alts,bh)
    sim=simulate(user,tx)
    elapsed=(time.perf_counter()-t0)*1000
    pnl=sim["pnl_lamports"]
    bps=(pnl/start*10000.0) if pnl is not None else None
    passed=bool(sim["err"] is None and pnl is not None and pnl>0 and bps>=MIN_SIM_NET_BPS)
    print("[ATOMIC_SIM] err=%s tx_bytes=%d units=%s fee=%s latency_ms=%.1f"%(
        sim["err"],shape["tx_bytes"],sim["units"],sim["fee_lamports"],elapsed),flush=True)
    print("[SIM_PNL] net=%s SOL bps=%s PROFITABLE=%s"%(
        ("%+.9f"%(pnl/1e9) if pnl is not None else "NA"),
        ("%+.2f"%bps if bps is not None else "NA"),passed),flush=True)
    out={"revision":"QSB_049","route":[BUY_DEX,SELL_DEX],"token":TOKEN,"start_sol":START_SOL,
         "quote_floor_lamports":quote_floor,"shape":shape,"simulation":sim,"latency_ms":elapsed,
         "SIMULATED_PROFITABLE":passed,"execution_authority":False,"sent":False}
    p=Path(root)/"runtime_state/qseries/qsb049_atomic_crossdex_sim/report.json"
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out
