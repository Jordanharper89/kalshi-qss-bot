from __future__ import annotations
import base64,json,os,struct,time,urllib.request,urllib.error
from pathlib import Path

WSOL="So11111111111111111111111111111111111111112"
MRIYA_WALLET="MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"
PUMP_FUN="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT="Es9vMFrzaCERmJfrF4H2FYD8gLtAZ57XqHq9P8rNw8w"
DLMM="LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"
PUMP="pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
TOKEN="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN22="TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
ATA="ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
MEMO="MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
SYSTEM="11111111111111111111111111111111"
RPC=os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com")
PUMP_API="https://fun-block.pump.fun/agents/swap"
START_SOL=float(os.getenv("QSB_052_START_SOL","0.025"))
MIN_NET_BPS=float(os.getenv("QSB_052_MIN_NET_BPS","20"))
SLIPPAGE_BPS=int(os.getenv("QSB_052_SLIPPAGE_BPS","20"))
MAX_TOKENS=int(os.getenv("QSB_054_MAX_TOKENS","64"))
PUMP_FEE_BPS=int(os.getenv("QSB_052_PUMP_FEE_BPS","120"))
SIZES_SOL=tuple(float(x) for x in os.getenv("QSB_057_SIZES_SOL","0.005,0.01,0.025,0.05,0.1,0.15,0.25,0.5,0.6,1.0,1.25,1.75").split(",") if x.strip())
LIVE_ARM=os.getenv("QSB_LIVE_ARM","").upper()=="YES"
TAPE="runtime_state/solana_opportunities/universal_trade_tape/multidex_universal_economic_tape.json"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_DLMM_CACHE={}

def b58d(s):
    n=0
    for ch in s:n=n*58+ALPH.index(ch)
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    out=b"\0"*(len(s)-len(s.lstrip("1")))+raw
    if len(out)!=32:raise ValueError("bad pubkey "+s)
    return out
def b58e(b):
    n=int.from_bytes(b,"big");s=""
    while n:n,r=divmod(n,58);s=ALPH[r]+s
    return "1"*(len(b)-len(b.lstrip(b"\0")))+(s or "")
def shortvec(n):
    o=bytearray()
    while True:
        x=n&127;n>>=7
        if n:x|=128
        o.append(x)
        if not n:return bytes(o)

def http(url,method="GET",body=None,timeout=15):
    dat=None if body is None else json.dumps(body,separators=(",",":")).encode()
    h={"accept":"application/json","user-agent":"qseries-qsb052/1.0"}
    if dat is not None:h["content-type"]="application/json"
    with urllib.request.urlopen(urllib.request.Request(url,data=dat,headers=h,method=method),timeout=timeout) as r:
        return json.loads(r.read().decode())

def rpc(method,params):
    j=http(RPC,"POST",{"jsonrpc":"2.0","id":1,"method":method,"params":params},15)
    if j.get("error"):raise RuntimeError("RPC "+json.dumps(j["error"]))
    return j.get("result")

def pda(seeds,program):
    from solders.pubkey import Pubkey
    pk,_=Pubkey.find_program_address([x if isinstance(x,bytes) else b58d(x) for x in seeds],Pubkey.from_string(program))
    return str(pk)

def ata(owner,mint,token_program):
    return pda([b58d(owner),b58d(token_program),b58d(mint)],ATA)

def account(addr):
    x=rpc("getAccountInfo",[addr,{"encoding":"base64","commitment":"processed"}])
    if not x or not x.get("value"):raise RuntimeError("ACCOUNT_NOT_FOUND:"+addr)
    v=x["value"];return base64.b64decode(v["data"][0]),v["owner"]

def token_amount(addr):
    d,_=account(addr)
    if len(d)<72:raise RuntimeError("TOKEN_ACCOUNT_SHORT")
    return struct.unpack_from("<Q",d,64)[0]

def decode_pump_pool(d):
    o=8+1+2
    creator=b58e(d[o:o+32]);o+=32
    base=b58e(d[o:o+32]);o+=32
    quote=b58e(d[o:o+32]);o+=32
    o+=32
    bv=b58e(d[o:o+32]);o+=32
    qv=b58e(d[o:o+32]);o+=32
    return {"creator":creator,"base_mint":base,"quote_mint":quote,"base_vault":bv,"quote_vault":qv}

def tape_candidates(root):
    p=Path(root)/TAPE
    if not p.exists():return []
    j=json.loads(p.read_text(encoding="utf-8"))
    rows=j.get("exact_rows") or j.get("rows") or []
    z={}
    for r in rows:
        if r.get("venue")!="PUMP_SWAP" or r.get("quote_mint")!=WSOL:continue
        t=r.get("token_address");pool=r.get("market_address")
        if not t or not pool:continue
        s=int(r.get("slot") or 0)
        if t not in z or s>z[t][0]:z[t]=(s,pool)
    return [(k,v[1]) for k,v in sorted(z.items(),key=lambda q:q[1][0],reverse=True)[:MAX_TOKENS]]

def discover_dlmm(token):
    if token in _DLMM_CACHE:
        v=_DLMM_CACHE[token]
        if isinstance(v,Exception):
            raise v
        return v

    url="https://dlmm.datapi.meteora.ag/pools?page=1&page_size=100&query="+token
    last=None
    for attempt in range(4):
        try:
            j=http(url)
            rows=j.get("data") if isinstance(j,dict) else j
            best=None
            for x in rows or []:
                tx=x.get("token_x") or x.get("tokenX") or {}
                ty=x.get("token_y") or x.get("tokenY") or {}
                def mint(v):
                    if isinstance(v,str): return v
                    return v.get("address") or v.get("mint") or v.get("token_address")
                mx,my=mint(tx),mint(ty)
                if {mx,my}!={WSOL,token}: continue
                a=x.get("address") or x.get("pool_address") or x.get("pubkey")
                if not a: continue
                tvl=float(x.get("tvl") or x.get("liquidity") or x.get("liquidity_usd") or 0)
                dx=int(tx.get("decimals",9)) if isinstance(tx,dict) else 9
                dy=int(ty.get("decimals",6)) if isinstance(ty,dict) else 6
                row={"address":str(a),"token_x":mx,"token_y":my,"decimals_x":dx,"decimals_y":dy}
                if best is None or tvl>best[0]:
                    best=(tvl,row)
            if not best:
                err=RuntimeError("NO_DLMM_PAIR")
                _DLMM_CACHE[token]=err
                raise err
            _DLMM_CACHE[token]=best[1]
            return best[1]
        except urllib.error.HTTPError as e:
            last=e
            if getattr(e,"code",None)!=429 or attempt==3:
                raise
            delay=0.35*(2**attempt)
            print("[RATE_LIMIT] token=%s retry=%d sleep=%.2fs"%(token[:10],attempt+1,delay),flush=True)
            time.sleep(delay)
    raise last if last else RuntimeError("DLMM_DISCOVERY_FAILED")

def dlmm_arrays(pool):
    rows=rpc("getProgramAccounts",[DLMM,{"encoding":"base64","commitment":"processed",
        "filters":[{"memcmp":{"offset":24,"bytes":pool}}]}]) or []
    out=[]
    for x in rows:
        d=base64.b64decode(x["account"]["data"][0])
        if len(d)>=16:out.append((struct.unpack_from("<q",d,8)[0],x["pubkey"],d))
    out.sort()
    if not out:raise RuntimeError("NO_DLMM_BIN_ARRAYS")
    return out

def dlmm_quote(meta,amount_raw,input_mint):
    from meteora_dlmm import PoolState,quote
    lb,_=account(meta["address"]);arr=dlmm_arrays(meta["address"])
    p=PoolState.from_accounts(lb,[x[2] for x in arr],decimals_x=meta["decimals_x"],
        decimals_y=meta["decimals_y"],lb_pair_key=b58d(meta["address"]),exhaustive=True)
    if input_mint==meta["token_x"]:swap_for_y=True
    elif input_mint==meta["token_y"]:swap_for_y=False
    else:raise RuntimeError("DLMM_DIRECTION")
    q=quote(p,amount_in=int(amount_raw),swap_for_y=swap_for_y,strict=True)
    if not getattr(q,"complete",False) or int(getattr(q,"remaining_in",0) or 0):raise RuntimeError("DLMM_PARTIAL")
    return {"raw_out":int(q.amount_out),"bins_crossed":max(1,int(getattr(q,"bins_crossed",1) or 1)),
            "swap_for_y":swap_for_y,"arrays":arr}

def pump_sell_local(pool,amount):
    d,_=account(pool);p=decode_pump_pool(d)
    if p["quote_mint"]!=WSOL:raise RuntimeError("PUMP_NOT_SOL")
    br=token_amount(p["base_vault"]);qr=token_amount(p["quote_vault"])
    net=amount*(10000-PUMP_FEE_BPS)//10000
    out=qr*net//(br+net)
    return {"raw_out":out,"pool":p}

def opportunity(token,pump_pool):
    meta=discover_dlmm(token)
    start=int(START_SOL*1e9)
    mq=dlmm_quote(meta,start,WSOL)
    pq=pump_sell_local(pump_pool,mq["raw_out"])
    net=pq["raw_out"]-start
    bps=net/start*10000
    return {"token":token,"pump_pool":pump_pool,"meteora":meta,"mq":mq,
            "start":start,"local_end":pq["raw_out"],"local_net":net,"local_bps":bps}


def pump_buy_local(pool,amount):
    d,_=account(pool);p=decode_pump_pool(d)
    if p["quote_mint"]!=WSOL:raise RuntimeError("PUMP_NOT_SOL")
    br=token_amount(p["base_vault"]);qr=token_amount(p["quote_vault"])
    net=amount*(10000-PUMP_FEE_BPS)//10000
    out=br*net//(qr+net)
    return {"raw_out":out,"pool":p}

def pump_tx(user,input_mint,output_mint,amount):
    j=http(PUMP_API,"POST",{"inputMint":input_mint,"outputMint":output_mint,"amount":str(int(amount)),
        "user":user,"feePayer":user,"slippagePct":SLIPPAGE_BPS/100.0,
        "frontRunningProtection":False,"tipAmount":0,"encoding":"base64"},20)
    if not j.get("transaction"):raise RuntimeError("PUMP_TX_MISSING")
    info=j.get("pumpMintInfo") or {}
    return j["transaction"],int(info.get("expectedOutAmount") or 0)



def build_token_snapshot(token,pump_pool):
    from meteora_dlmm import PoolState
    meta=discover_dlmm(token)
    lb,_=account(meta["address"])
    arr=dlmm_arrays(meta["address"])
    state=PoolState.from_accounts(
        lb,[x[2] for x in arr],
        decimals_x=meta["decimals_x"],
        decimals_y=meta["decimals_y"],
        lb_pair_key=b58d(meta["address"]),
        exhaustive=True
    )
    pd,_=account(pump_pool)
    pp=decode_pump_pool(pd)
    if pp["quote_mint"]!=WSOL:
        raise RuntimeError("PUMP_NOT_SOL")
    return {
        "token":token,
        "pump_pool":pump_pool,
        "meteora":meta,
        "dlmm_state":state,
        "pump_base_reserve":token_amount(pp["base_vault"]),
        "pump_quote_reserve":token_amount(pp["quote_vault"]),
    }

def dlmm_quote_snapshot(snap,amount_raw,input_mint):
    from meteora_dlmm import quote
    meta=snap["meteora"]
    if input_mint==meta["token_x"]:
        swap_for_y=True
    elif input_mint==meta["token_y"]:
        swap_for_y=False
    else:
        raise RuntimeError("DLMM_DIRECTION")
    q=quote(snap["dlmm_state"],amount_in=int(amount_raw),swap_for_y=swap_for_y,strict=True)
    if not getattr(q,"complete",False) or int(getattr(q,"remaining_in",0) or 0):
        raise RuntimeError("DLMM_PARTIAL")
    return {
        "raw_out":int(q.amount_out),
        "bins_crossed":max(1,int(getattr(q,"bins_crossed",1) or 1)),
        "swap_for_y":swap_for_y,
        "arrays":[],
    }

def pump_sell_snapshot(snap,amount):
    br=snap["pump_base_reserve"];qr=snap["pump_quote_reserve"]
    net=int(amount)*(10000-PUMP_FEE_BPS)//10000
    return qr*net//(br+net)

def pump_buy_snapshot(snap,amount):
    br=snap["pump_base_reserve"];qr=snap["pump_quote_reserve"]
    net=int(amount)*(10000-PUMP_FEE_BPS)//10000
    return br*net//(qr+net)

def sized_snapshot_opportunities(snap,size_sol):
    token=snap["token"]
    start=int(float(size_sol)*1e9)

    mb=dlmm_quote_snapshot(snap,start,WSOL)
    ps=pump_sell_snapshot(snap,mb["raw_out"])
    net1=ps-start
    a={
        "token":token,"pump_pool":snap["pump_pool"],"meteora":snap["meteora"],
        "start":start,"size_sol":float(size_sol),"direction":"METEORA_TO_PUMP",
        "mq":mb,"local_end":ps,"local_net":net1,"local_bps":net1/start*10000.0
    }

    pb=pump_buy_snapshot(snap,start)
    ms=dlmm_quote_snapshot(snap,pb,token)
    net2=ms["raw_out"]-start
    b={
        "token":token,"pump_pool":snap["pump_pool"],"meteora":snap["meteora"],
        "start":start,"size_sol":float(size_sol),"direction":"PUMP_TO_METEORA",
        "mq":ms,"local_end":ms["raw_out"],"local_net":net2,"local_bps":net2/start*10000.0
    }
    return sorted([a,b],key=lambda x:x["local_net"],reverse=True)

def sized_bidirectional_opportunities(token,pump_pool,size_sol,meta=None):
    meta=meta or discover_dlmm(token)
    start=int(float(size_sol)*1e9)

    m_buy=dlmm_quote(meta,start,WSOL)
    p_sell=pump_sell_local(pump_pool,m_buy["raw_out"])
    net1=p_sell["raw_out"]-start
    a={"token":token,"pump_pool":pump_pool,"meteora":meta,"start":start,"size_sol":float(size_sol),
       "direction":"METEORA_TO_PUMP","mq":m_buy,"local_end":p_sell["raw_out"],
       "local_net":net1,"local_bps":net1/start*10000.0}

    p_buy=pump_buy_local(pump_pool,start)
    m_sell=dlmm_quote(meta,p_buy["raw_out"],token)
    net2=m_sell["raw_out"]-start
    b={"token":token,"pump_pool":pump_pool,"meteora":meta,"start":start,"size_sol":float(size_sol),
       "direction":"PUMP_TO_METEORA","mq":m_sell,"local_end":m_sell["raw_out"],
       "local_net":net2,"local_bps":net2/start*10000.0}

    return sorted([a,b],key=lambda x:x["local_net"],reverse=True)

def bidirectional_opportunities(token,pump_pool):
    meta=discover_dlmm(token)
    start=int(START_SOL*1e9)

    # Meteora low -> Pump high
    m_buy=dlmm_quote(meta,start,WSOL)
    p_sell=pump_sell_local(pump_pool,m_buy["raw_out"])
    a=dict(token=token,pump_pool=pump_pool,meteora=meta,start=start,
           direction="METEORA_TO_PUMP",first_out=m_buy["raw_out"],
           local_end=p_sell["raw_out"],local_net=p_sell["raw_out"]-start)
    a["local_bps"]=a["local_net"]/start*10000.0

    # Pump low -> Meteora high
    p_buy=pump_buy_local(pump_pool,start)
    m_sell=dlmm_quote(meta,p_buy["raw_out"],token)
    b=dict(token=token,pump_pool=pump_pool,meteora=meta,start=start,
           direction="PUMP_TO_METEORA",first_out=p_buy["raw_out"],
           local_end=m_sell["raw_out"],local_net=m_sell["raw_out"]-start)
    b["local_bps"]=b["local_net"]/start*10000.0
    return sorted([a,b],key=lambda x:x["local_bps"],reverse=True)
def pump_sell_tx(user,token,amount):
    j=http(PUMP_API,"POST",{"inputMint":token,"outputMint":WSOL,"amount":str(int(amount)),
        "user":user,"feePayer":user,"slippagePct":SLIPPAGE_BPS/100.0,
        "frontRunningProtection":False,"tipAmount":0,"encoding":"base64"},20)
    if not j.get("transaction"):raise RuntimeError("PUMP_TX_MISSING")
    info=j.get("pumpMintInfo") or {}
    return j["transaction"],int(info.get("expectedOutAmount") or 0)

def resolve_pump_instructions(tx64):
    from solders.transaction import VersionedTransaction
    tx=VersionedTransaction.from_bytes(base64.b64decode(tx64));m=tx.message
    static=list(m.account_keys);keys=list(static)
    lookups=list(getattr(m,"address_table_lookups",[]) or [])
    if lookups:
        vals=rpc("getMultipleAccounts",[[str(x.account_key) for x in lookups],{"encoding":"base64","commitment":"processed"}])["value"]
        warr=[];rarr=[]
        for lk,v in zip(lookups,vals):
            d=base64.b64decode(v["data"][0]);addrs=[d[i:i+32] for i in range(56,len(d),32)]
            warr += [type(static[0]).from_bytes(addrs[i]) for i in lk.writable_indexes]
            rarr += [type(static[0]).from_bytes(addrs[i]) for i in lk.readonly_indexes]
        keys += warr+rarr
    h=m.header;ns=h.num_required_signatures;rs=h.num_readonly_signed_accounts;ru=h.num_readonly_unsigned_accounts
    sw=ns-rs;uw=len(static)-ru
    def flags(i):
        if i<len(static):
            return i<ns,(i<sw if i<ns else i<uw)
        loaded=i-len(static);return False,loaded < (len(keys)-len(static)-sum(len(x.readonly_indexes) for x in lookups))
    out=[]
    for ix in m.instructions:
        pi=int(ix.program_id_index);acs=[]
        for ai in ix.accounts:
            i=int(ai);s,w=flags(i);acs.append({"pubkey":str(keys[i]),"isSigner":s,"isWritable":w})
        out.append({"programId":str(keys[pi]),"accounts":acs,"data":base64.b64encode(bytes(ix.data)).decode()})
    return out,[str(x.account_key) for x in lookups]

def dlmm_ix(user,op):
    meta=op["meteora"];token=op["token"];q=op["mq"];pool=meta["address"]
    tx_prog=account(meta["token_x"])[1];ty_prog=account(meta["token_y"])[1]
    ux=ata(user,meta["token_x"],tx_prog);uy=ata(user,meta["token_y"],ty_prog)
    rx=pda([b58d(pool),b58d(meta["token_x"])],DLMM)
    ry=pda([b58d(pool),b58d(meta["token_y"])],DLMM)
    oracle=pda([b"oracle",b58d(pool)],DLMM)
    bitmap=pda([b"bitmap",b58d(pool)],DLMM)
    try:account(bitmap);bitmap_key=bitmap
    except Exception:bitmap_key=DLMM
    ev=pda([b"__event_authority"],DLMM)
    ac=[
      (pool,False,True),(bitmap_key,False,True),(rx,False,True),(ry,False,True),
      (ux if meta["token_x"]==WSOL else uy,False,True),
      (uy if meta["token_x"]==WSOL else ux,False,True),
      (meta["token_x"],False,False),(meta["token_y"],False,False),(oracle,False,True),
      (DLMM,False,True),(user,True,False),(tx_prog,False,False),(ty_prog,False,False),
      (ev,False,False),(DLMM,False,False)]
    arr=q["arrays"]
    # Send the active neighborhood only; quote's bins_crossed controls width.
    n=min(len(arr),max(3,q["bins_crossed"]+2))
    chosen=arr[:n] if q["swap_for_y"] else list(reversed(arr))[:n]
    ac += [(x[1],False,True) for x in chosen]
    min_out=q["raw_out"]*(10000-SLIPPAGE_BPS)//10000
    data=bytes([248,198,158,145,225,117,135,200])+struct.pack("<QQ",op["start"],min_out)
    return {"programId":DLMM,"accounts":[{"pubkey":p,"isSigner":s,"isWritable":w} for p,s,w in ac],
            "data":base64.b64encode(data).decode()}

def merge_native(user,op,pump64):
    p_ixs,alts=resolve_pump_instructions(pump64)
    m_ix=dlmm_ix(user,op)
    out=[];inserted=False
    for ix in p_ixs:
        if ix["programId"]==PUMP and not inserted:
            out.append(m_ix);inserted=True
        out.append(ix)
    if not inserted:raise RuntimeError("PUMP_PROGRAM_IX_NOT_FOUND")
    return out,alts

def alt_accounts(addrs):
    if not addrs:return {}
    vals=rpc("getMultipleAccounts",[addrs,{"encoding":"base64","commitment":"processed"}])["value"]
    o={}
    for k,v in zip(addrs,vals):
        if v:
            d=base64.b64decode(v["data"][0]);o[k]=[d[i:i+32] for i in range(56,len(d),32)]
    return o

def compile_v0(payer,ixs,alt_keys,blockhash):
    pb=b58d(payer);order=[];meta={}
    def touch(pk,s=False,w=False,program=False):
        b=b58d(pk)
        if b not in meta:order.append(b);meta[b]={"s":s,"w":w,"p":program}
        else:meta[b]["s"]|=s;meta[b]["w"]|=w;meta[b]["p"]|=program
    touch(payer,True,True)
    for ix in ixs:
        touch(ix["programId"],program=True)
        for a in ix["accounts"]:touch(a["pubkey"],a["isSigner"],a["isWritable"])
    if any(v["s"] and k!=pb for k,v in meta.items()):raise RuntimeError("EXTRA_SIGNER")
    tabs=alt_accounts(alt_keys);chosen={};lks=[]
    for tk in alt_keys:
        arr=tabs.get(tk,[]);pos={b:i for i,b in enumerate(arr)};wr=[];ro=[]
        for b in order:
            m=meta[b]
            if b==pb or m["s"] or m["p"] or b in chosen or b not in pos:continue
            i=pos[b]
            if i>255:continue
            chosen[b]=(tk,i,m["w"]);(wr if m["w"] else ro).append(i)
        if wr or ro:lks.append((tk,wr,ro,arr))
    st=[b for b in order if b not in chosen]
    sw=[b for b in st if meta[b]["s"] and meta[b]["w"] and b!=pb];sr=[b for b in st if meta[b]["s"] and not meta[b]["w"]]
    uw=[b for b in st if not meta[b]["s"] and meta[b]["w"]];ur=[b for b in st if not meta[b]["s"] and not meta[b]["w"]]
    st=[pb]+sw+sr+uw+ur;lw=[];lr=[]
    for _,wr,ro,a in lks:lw += [a[i] for i in wr]
    for _,wr,ro,a in lks:lr += [a[i] for i in ro]
    keys=st+lw+lr;idx={b:i for i,b in enumerate(keys)}
    msg=bytearray(b"\x80"+bytes([1,0,len(ur)])+shortvec(len(st))+b"".join(st)+b58d(blockhash)+shortvec(len(ixs)))
    for ix in ixs:
        ac=[idx[b58d(a["pubkey"])] for a in ix["accounts"]];dat=base64.b64decode(ix["data"])
        msg += bytes([idx[b58d(ix["programId"])]])+shortvec(len(ac))+bytes(ac)+shortvec(len(dat))+dat
    msg+=shortvec(len(lks))
    for tk,wr,ro,_ in lks:msg+=b58d(tk)+shortvec(len(wr))+bytes(wr)+shortvec(len(ro))+bytes(ro)
    raw=shortvec(1)+b"\0"*64+bytes(msg)
    if len(raw)>1232:raise RuntimeError("ATOMIC_TX_TOO_LARGE:%d"%len(raw))
    return bytes(msg),raw

def keypair():
    from solders.keypair import Keypair
    s=os.getenv("QSB_SOLANA_PRIVATE_KEY","").strip()
    if not s:raise RuntimeError("QSB_SOLANA_PRIVATE_KEY_MISSING")
    try:
        if s.startswith("["):return Keypair.from_bytes(bytes(json.loads(s)))
        return Keypair.from_base58_string(s)
    except Exception as e:raise RuntimeError("PRIVATE_KEY_FORMAT:"+str(e))

def signed_tx(msg,kp):
    sig=bytes(kp.sign_message(msg));return shortvec(1)+sig+msg

def simulate(raw,user,sigverify=True):
    pre=rpc("getBalance",[user,{"commitment":"processed"}])["value"]
    v=rpc("simulateTransaction",[base64.b64encode(raw).decode(),{"encoding":"base64","sigVerify":bool(sigverify),
        "commitment":"processed","accounts":{"encoding":"base64","addresses":[user]}}])
    post=None
    if v.get("accounts") and v["accounts"][0]:post=v["accounts"][0]["lamports"]
    pnl=None if post is None else post-pre
    return {"err":v.get("err"),"units":v.get("unitsConsumed"),"pnl":pnl,"logs":v.get("logs") or []}

def send(raw):
    return rpc("sendTransaction",[base64.b64encode(raw).decode(),{"encoding":"base64","skipPreflight":False,"preflightCommitment":"processed","maxRetries":2}])

def sim_identity():
    sec=os.getenv("QSB_SOLANA_PRIVATE_KEY","").strip()
    if sec:
        kp=keypair()
        return kp,str(kp.pubkey())
    return None,os.getenv("QSB_SOLANA_WALLET","").strip() or "MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"




def _hot_token_mints_from_tx(tx):
    if not isinstance(tx,dict):
        return []
    meta=tx.get("meta") or {}
    out=[];seen=set()
    for key in ("preTokenBalances","postTokenBalances"):
        for row in meta.get(key) or []:
            mint=row.get("mint")
            if not mint or mint in (WSOL,USDC,USDT) or mint in seen:
                continue
            seen.add(mint);out.append(mint)
    return out

def mriya_hot_tokens(limit_signatures=24,max_transactions=12):
    sigs=rpc("getSignaturesForAddress",[MRIYA_WALLET,{"limit":int(limit_signatures),"commitment":"processed"}]) or []
    ranked={}
    now=time.time()
    for rank,row in enumerate(sigs[:max_transactions]):
        sig=row.get("signature")
        if not sig or row.get("err") is not None:
            continue
        try:
            tx=rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"processed","maxSupportedTransactionVersion":0}])
        except Exception:
            continue
        bt=float((tx or {}).get("blockTime") or 0)
        age=max(0.0,now-bt) if bt else 999999.0
        recency=max(0.0,120.0-age)
        for mint in _hot_token_mints_from_tx(tx):
            score=recency*1000.0+(max_transactions-rank)
            if mint not in ranked or score>ranked[mint]["score"]:
                ranked[mint]={"mint":mint,"score":score,"age":age,"signature":sig}
    return sorted(ranked.values(),key=lambda x:x["score"],reverse=True)

def canonical_pump_pool(token):
    from solders.pubkey import Pubkey
    base=Pubkey.from_string(token)
    quote=Pubkey.from_string(WSOL)
    pump=Pubkey.from_string(PUMP_FUN)
    amm=Pubkey.from_string(PUMP)
    creator,_=Pubkey.find_program_address([b"pool-authority",bytes(base)],pump)
    pool,_=Pubkey.find_program_address([b"pool",(0).to_bytes(2,"little"),bytes(creator),bytes(base),bytes(quote)],amm)
    addr=str(pool)
    try:
        d,_=account(addr)
        p=decode_pump_pool(d)
        if p.get("base_mint")==token and p.get("quote_mint")==WSOL:
            return addr
    except Exception:
        return None
    return None

def mriya_first_candidates(root):
    fallback=tape_candidates(root)
    by_token={t:p for t,p in fallback}
    out=[];seen=set()
    for h in mriya_hot_tokens():
        token=h["mint"]
        pool=by_token.get(token) or canonical_pump_pool(token)
        if not pool or token in seen:
            continue
        seen.add(token);out.append((token,pool))
        print("[MRIYA_HOT] token=%s age=%.2fs pool=%s"%(token[:10],h["age"],pool[:10]),flush=True)
    for token,pool in fallback:
        if token not in seen:
            seen.add(token);out.append((token,pool))
    return out[:MAX_TOKENS]

def run(root):
    print("[QSB-057] MRIYA-HOTSET SNAPSHOT ARBITRAGE ENGINE",flush=True)
    print("[PATH] MRIYA-HOT TOKENS FIRST -> SAME TOKEN BUY LOW / SELL HIGH | JUPITER=NONE",flush=True)
    print("[SEARCH] tokens<=%d sizes=%s"%(MAX_TOKENS,",".join(str(x) for x in SIZES_SOL)),flush=True)

    ranked=[]
    tokens=mriya_first_candidates(root)
    print("[TOKENS] %d"%len(tokens),flush=True)

    for token,pool in tokens:
        try:
            snap=build_token_snapshot(token,pool)
            print("[SNAPSHOT] token=%s hydrated_once=True"%(token[:10]),flush=True)
        except Exception as e:
            print("[SKIP_TOKEN] token=%s %s: %s"%(token[:10],type(e).__name__,e),flush=True)
            continue

        for size_sol in SIZES_SOL:
            try:
                for op in sized_snapshot_opportunities(snap,size_sol):
                    ranked.append(op)
                    if op["local_bps"]>=MIN_NET_BPS:
                        print("[POSITIVE] token=%s size=%.3f direction=%s net=%+.9f SOL bps=%+.2f"%(
                            token[:10],size_sol,op["direction"],op["local_net"]/1e9,op["local_bps"]),flush=True)
            except RuntimeError as e:
                if str(e)=="DLMM_PARTIAL":
                    print("[SIZE_SKIP] token=%s size=%.3f DLMM_PARTIAL"%(token[:10],size_sol),flush=True)
                    continue
                print("[SIZE_SKIP] token=%s size=%.3f %s: %s"%(token[:10],size_sol,type(e).__name__,e),flush=True)
            except Exception as e:
                print("[SIZE_SKIP] token=%s size=%.3f %s: %s"%(token[:10],size_sol,type(e).__name__,e),flush=True)

    ranked.sort(key=lambda x:x["local_net"],reverse=True)
    positives=[x for x in ranked if x["local_bps"]>=MIN_NET_BPS]
    print("[RANKED] candidates=%d positive=%d"%(len(ranked),len(positives)),flush=True)

    if positives:
        top=positives[0]
        print("[BEST_PNL] token=%s size=%.3f direction=%s net=%+.9f SOL bps=%+.2f PROFITABLE=True"%(
            top["token"][:10],top["size_sol"],top["direction"],top["local_net"]/1e9,top["local_bps"]),flush=True)
    elif ranked:
        top=ranked[0]
        print("[BEST_PNL] token=%s size=%.3f direction=%s net=%+.9f SOL bps=%+.2f PROFITABLE=False"%(
            top["token"][:10],top["size_sol"],top["direction"],top["local_net"]/1e9,top["local_bps"]),flush=True)
    else:
        print("[BEST_PNL] NONE",flush=True)

    print("[MONEY] %s"%("POSITIVE_SPREAD_FOUND" if positives else "NO_POSITIVE_SPREAD"),flush=True)
    return positives[0] if positives else None

