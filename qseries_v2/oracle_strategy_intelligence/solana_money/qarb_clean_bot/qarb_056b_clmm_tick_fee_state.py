from __future__ import annotations
import json,struct,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_AGE_MS=750.0
SRC=Path("runtime_state/qseries/qarb_clean_bot/qarb_052b5_clmm_exact_descriptor_pavement.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_056b_clmm_tick_fee_state.json")
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

def decode_pool(raw):
    if len(raw)<273: raise RuntimeError("RAYDIUM_POOL_SHORT")
    return {"amm_config":b58e(raw[9:41]),"token_mint_0":b58e(raw[73:105]),"token_mint_1":b58e(raw[105:137]),
            "token_vault_0":b58e(raw[137:169]),"token_vault_1":b58e(raw[169:201]),
            "tick_spacing":struct.unpack_from("<H",raw,235)[0],"liquidity":int.from_bytes(raw[237:253],"little"),
            "sqrt_price_x64":int.from_bytes(raw[253:269],"little"),"tick_current":struct.unpack_from("<i",raw,269)[0]}

def decode_config(raw):
    if len(raw)<57: raise RuntimeError("RAYDIUM_CONFIG_SHORT")
    return {"protocol_fee_rate":struct.unpack_from("<I",raw,43)[0],"trade_fee_rate":struct.unpack_from("<I",raw,47)[0],
            "tick_spacing":struct.unpack_from("<H",raw,51)[0],"fund_fee_rate":struct.unpack_from("<I",raw,53)[0],
            "fee_denominator":1000000}

def decode_tick_array(raw,pool):
    pb=b58d(pool)
    if len(raw)<44 or raw[8:40]!=pb:return None
    return {"start_tick_index":struct.unpack_from("<i",raw,40)[0],"bytes":len(raw)}

def build(root):
    root=Path(root);rows=[]
    for d in _load(root/SRC).get("descriptors") or []:
        r={"pool":d["pool"],"decoded":False,"descriptor_match":False,"config_decoded":False,"tick_arrays":[],"errors":[]}
        try:
            raw,slot=_read(d["pool"]);st=decode_pool(raw);r["decoded"]=True;r["slot"]=slot;r["state"]=st
            r["descriptor_match"]={st["token_mint_0"],st["token_mint_1"]}=={d["token_a"],d["token_b"]}
            try:
                cr,cslot=_read(st["amm_config"]);r["config"]=decode_config(cr);r["config_slot"]=cslot;r["config_decoded"]=True
            except Exception as e:r["errors"].append("config:"+type(e).__name__+":"+str(e))
        except Exception as e:r["errors"].append("pool:"+type(e).__name__+":"+str(e))
        for a0 in d.get("watched_accounts") or []:
            a=_addr(a0)
            if not a or a==d["pool"]:continue
            try:
                raw,slot=_read(a,2);ta=decode_tick_array(raw,d["pool"])
                if ta:ta.update({"address":a,"slot":slot});r["tick_arrays"].append(ta)
            except Exception:pass
        rows.append(r)
    payload={"revision":"QARB_056B","rows":rows,"descriptors":len(rows),
             "pool_decoded":sum(1 for r in rows if r["decoded"]),
             "descriptor_matches":sum(1 for r in rows if r["descriptor_match"]),
             "fee_state_ready":sum(1 for r in rows if r["config_decoded"]),
             "tick_array_ready":sum(1 for r in rows if r["tick_arrays"]),
             "priced_live":False,
             "next":"BOUND_LOCAL_CLMM_SWAP_MATH_USING_DECODED_FEE_AND_TICK_STATE",
             "execution_authority":False,"paper_only":True}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    p=build(Path.cwd())
    print("[QARB-056B] RAYDIUM CLMM TICK/FEE STATE")
    print("[CLMM] descriptors=%d pool_decoded=%d matches=%d fee_ready=%d tick_array_ready=%d priced_live=%s"%(
        p["descriptors"],p["pool_decoded"],p["descriptor_matches"],p["fee_state_ready"],p["tick_array_ready"],p["priced_live"]))
    for r in p["rows"]:
        st=r.get("state") or {};cfg=r.get("config") or {}
        print("[CLMM_STATE] %s decoded=%s match=%s fee=%s arrays=%d tick=%s spacing=%s"%(
            r["pool"][:12],r["decoded"],r["descriptor_match"],cfg.get("trade_fee_rate"),len(r["tick_arrays"]),
            st.get("tick_current"),st.get("tick_spacing")))
    print("[NEXT]",p["next"])
    print("[REPORT]",OUT)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE")

if __name__=="__main__": main()
