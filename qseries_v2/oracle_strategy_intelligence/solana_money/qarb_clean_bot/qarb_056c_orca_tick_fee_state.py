from __future__ import annotations
import hashlib,json,struct,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_AGE_MS=750.0
SRC=Path("runtime_state/qseries/qarb_clean_bot/qarb_052c6_orca_exact_descriptor_repair.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_056c_orca_tick_fee_state.json")
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58d(s):
    n=0
    for ch in s:n=n*58+ALPH.index(ch)
    h=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    z=0
    for ch in s:
        if ch=="1":z+=1
        else:break
    return b"\0"*z+h

def b58e(b):
    n=int.from_bytes(b,"big");out=""
    while n:
        n,r=divmod(n,58);out=ALPH[r]+out
    z=0
    for x in b:
        if x==0:z+=1
        else:break
    return "1"*z+(out or "")

def _load(p):
    if not p.is_file(): raise RuntimeError("MISSING_ARTIFACT:"+str(p))
    return json.loads(p.read_text(encoding="utf-8"))

def _addr(x):
    if isinstance(x,str): return x
    if isinstance(x,dict):
        for k in ("pubkey","address","account","key"):
            v=x.get(k)
            if isinstance(v,str) and v:return v

def _read(a,tries=3):
    last=None
    for i in range(tries):
        try:return c.account(a)
        except Exception as e:
            last=e;time.sleep(.3*(i+1))
    raise last

def _walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from _walk(v)
    elif isinstance(x,list):
        for v in x:yield from _walk(v)

def runtime_accounts(root,pool):
    out=[]
    for p in (Path(root)/"runtime_state").rglob("*.json"):
        try:o=json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
        for d in _walk(o):
            if d.get("pool")!=pool:continue
            a=d.get("accounts")
            if isinstance(a,list):
                for x in a:
                    aa=_addr(x)
                    if aa and aa not in out:out.append(aa)
            elif isinstance(a,dict):
                for x in a.values():
                    aa=_addr(x)
                    if aa and aa not in out:out.append(aa)
    return out

def decode_pool(raw):
    if len(raw)<261: raise RuntimeError("ORCA_POOL_SHORT")
    if raw[:8]!=bytes.fromhex("3f95d10ce1806309"): raise RuntimeError("ORCA_WHIRLPOOL_DISCRIMINATOR")
    return {"tick_spacing":struct.unpack_from("<H",raw,41)[0],"fee_rate":struct.unpack_from("<H",raw,45)[0],
            "protocol_fee_rate":struct.unpack_from("<H",raw,47)[0],"liquidity":int.from_bytes(raw[49:65],"little"),
            "sqrt_price_x64":int.from_bytes(raw[65:81],"little"),"tick_current":struct.unpack_from("<i",raw,81)[0],
            "token_mint_a":b58e(raw[101:133]),"token_vault_a":b58e(raw[133:165]),
            "token_mint_b":b58e(raw[181:213]),"token_vault_b":b58e(raw[213:245]),"fee_denominator":1000000}

def disc(name): return hashlib.sha256(("account:"+name).encode()).digest()[:8]

def classify_tick_array(raw,pool):
    if raw[:8] not in (disc("TickArray"),disc("DynamicTickArray")): return None
    if b58d(pool) not in raw:return None
    return {"kind":"FIXED" if raw[:8]==disc("TickArray") else "DYNAMIC",
            "start_tick_index":struct.unpack_from("<i",raw,8)[0] if len(raw)>=12 else None,
            "bytes":len(raw)}

def build(root):
    root=Path(root);rows=[]
    for d in _load(root/SRC).get("descriptors") or []:
        r={"pool":d["pool"],"decoded":False,"mint_match":False,"role_match":False,"tick_arrays":[],"errors":[]}
        try:
            raw,slot=_read(d["pool"]);st=decode_pool(raw);r["decoded"]=True;r["slot"]=slot;r["state"]=st
            r["mint_match"]={st["token_mint_a"],st["token_mint_b"]}=={d["token_a"],d["token_b"]}
            r["role_match"]={st["token_vault_a"],st["token_vault_b"]}=={d["vault_a"],d["vault_b"]}
        except Exception as e:r["errors"].append("pool:"+type(e).__name__+":"+str(e))
        for a in runtime_accounts(root,d["pool"]):
            if a in (d["pool"],d["vault_a"],d["vault_b"]):continue
            try:
                raw,slot=_read(a,2);ta=classify_tick_array(raw,d["pool"])
                if ta:ta.update({"address":a,"slot":slot});r["tick_arrays"].append(ta)
            except Exception:pass
        rows.append(r)
    payload={"revision":"QARB_056C","rows":rows,"descriptors":len(rows),
             "pool_decoded":sum(1 for r in rows if r["decoded"]),
             "mint_matches":sum(1 for r in rows if r["mint_match"]),
             "role_matches":sum(1 for r in rows if r["role_match"]),
             "fee_state_ready":sum(1 for r in rows if r["decoded"]),
             "tick_array_ready":sum(1 for r in rows if r["tick_arrays"]),
             "priced_live":False,
             "next":"BOUND_LOCAL_ORCA_SWAP_MATH_USING_DECODED_FEE_AND_TICK_STATE",
             "execution_authority":False,"paper_only":True}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    p=build(Path.cwd())
    print("[QARB-056C] ORCA WHIRLPOOL TICK/FEE STATE")
    print("[ORCA] descriptors=%d pool_decoded=%d mint_matches=%d role_matches=%d fee_ready=%d tick_array_ready=%d priced_live=%s"%(
        p["descriptors"],p["pool_decoded"],p["mint_matches"],p["role_matches"],p["fee_state_ready"],p["tick_array_ready"],p["priced_live"]))
    for r in p["rows"]:
        st=r.get("state") or {}
        print("[ORCA_STATE] %s decoded=%s mint_match=%s role_match=%s fee=%s arrays=%d tick=%s spacing=%s"%(
            r["pool"][:12],r["decoded"],r["mint_match"],r["role_match"],st.get("fee_rate"),len(r["tick_arrays"]),
            st.get("tick_current"),st.get("tick_spacing")))
    print("[NEXT]",p["next"])
    print("[REPORT]",OUT)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE")

if __name__=="__main__": main()
