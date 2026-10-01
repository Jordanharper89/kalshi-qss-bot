from __future__ import annotations
import json,struct,hashlib,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_052a6_damm_graph_ready_live_adapter as damm

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_AGE_MS=750.0
WSOL=getattr(c,"WSOL","So11111111111111111111111111111111111111112")
CLMM_SRC=Path("runtime_state/qseries/qarb_clean_bot/qarb_052b5_clmm_exact_descriptor_pavement.json")
ORCA_SRC=Path("runtime_state/qseries/qarb_clean_bot/qarb_052c6_orca_exact_descriptor_repair.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_055_unified_clamm_native_decoder_and_damm_cutover.json")

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
    if not p.is_file():raise RuntimeError("MISSING_ARTIFACT:"+str(p))
    return json.loads(p.read_text(encoding="utf-8"))

def _addr(x):
    if isinstance(x,str):return x
    if isinstance(x,dict):
        for k in ("pubkey","address","account","key"):
            v=x.get(k)
            if isinstance(v,str) and v:return v
    return None

def _account(addr,tries=3):
    last=None
    for i in range(tries):
        try:return c.account(addr)
        except Exception as e:
            last=e;time.sleep(.3*(i+1))
    raise last

def decode_raydium_pool(raw):
    if len(raw)<273:raise RuntimeError("RAYDIUM_POOL_SHORT")
    return {
      "token_mint_0":b58e(raw[73:105]),
      "token_mint_1":b58e(raw[105:137]),
      "token_vault_0":b58e(raw[137:169]),
      "token_vault_1":b58e(raw[169:201]),
      "observation_key":b58e(raw[201:233]),
      "mint_decimals_0":raw[233],
      "mint_decimals_1":raw[234],
      "tick_spacing":struct.unpack_from("<H",raw,235)[0],
      "liquidity":int.from_bytes(raw[237:253],"little"),
      "sqrt_price_x64":int.from_bytes(raw[253:269],"little"),
      "tick_current":struct.unpack_from("<i",raw,269)[0],
    }

def decode_raydium_tick_array(raw,pool):
    pb=b58d(pool)
    if len(raw)<44 or raw[8:40]!=pb:return None
    return {"start_tick_index":struct.unpack_from("<i",raw,40)[0],"bytes":len(raw)}

def decode_orca_pool(raw):
    if len(raw)<261:raise RuntimeError("ORCA_POOL_SHORT")
    disc=bytes.fromhex("3f95d10ce1806309")
    if raw[:8]!=disc:raise RuntimeError("ORCA_WHIRLPOOL_DISCRIMINATOR")
    return {
      "tick_spacing":struct.unpack_from("<H",raw,41)[0],
      "fee_rate":struct.unpack_from("<H",raw,45)[0],
      "protocol_fee_rate":struct.unpack_from("<H",raw,47)[0],
      "liquidity":int.from_bytes(raw[49:65],"little"),
      "sqrt_price_x64":int.from_bytes(raw[65:81],"little"),
      "tick_current_index":struct.unpack_from("<i",raw,81)[0],
      "token_mint_a":b58e(raw[101:133]),
      "token_vault_a":b58e(raw[133:165]),
      "token_mint_b":b58e(raw[181:213]),
      "token_vault_b":b58e(raw[213:245]),
    }

def runtime_accounts_for_pool(root,pool):
    out=[]
    for p in (Path(root)/"runtime_state").rglob("*.json"):
        try:o=json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
        stack=[o]
        while stack:
            x=stack.pop()
            if isinstance(x,dict):
                if x.get("pool")==pool and isinstance(x.get("accounts"),list):
                    for a in x["accounts"]:
                        aa=_addr(a)
                        if aa and aa not in out:out.append(aa)
                stack.extend(x.values())
            elif isinstance(x,list):stack.extend(x)
    return out

def _damm(root):
    states,reg=damm.prepare(root)
    edges=[];checks=[]
    for i,(d,s) in enumerate(states):
        for src,dst in ((d.token_a,d.token_b),(d.token_b,d.token_a)):
            edges.append({"venue":"METEORA_DAMM_V2","pool":d.pool,"src":src,"dst":dst})
            try:
                q=damm.quote_edge((d,s),src,100000)
                checks.append({"pool":d.pool,"src":src,"dst":dst,"ok":isinstance(q,int) and q>=0})
            except Exception as e:
                checks.append({"pool":d.pool,"src":src,"dst":dst,"ok":False,"error":type(e).__name__+":"+str(e)})
    return {"live_states":len(states),"watched_accounts":len(reg),"edges":edges,
            "quote_checks":checks,"priced_live":bool(checks and all(x["ok"] for x in checks))}

def _clmm(root):
    descs=list(_load(Path(root)/CLMM_SRC).get("descriptors") or [])
    rows=[]
    for d in descs:
        pool=d["pool"];expected={d["token_a"],d["token_b"]}
        row={"pool":pool,"descriptor_tokens":sorted(expected),"pool_decoded":False,
             "descriptor_match":False,"tick_arrays":[],"errors":[]}
        try:
            raw,slot=_account(pool)
            dec=decode_raydium_pool(raw);row["pool_decoded"]=True;row["slot"]=slot;row["state"]=dec
            row["descriptor_match"]={dec["token_mint_0"],dec["token_mint_1"]}==expected
        except Exception as e:row["errors"].append("pool:"+type(e).__name__+":"+str(e))
        for a0 in d.get("watched_accounts") or []:
            a=_addr(a0)
            if not a or a==pool:continue
            try:
                raw,slot=_account(a,2);ta=decode_raydium_tick_array(raw,pool)
                if ta:ta.update({"address":a,"slot":slot});row["tick_arrays"].append(ta)
            except Exception:pass
        rows.append(row)
    ready=[r for r in rows if r["pool_decoded"] and r["descriptor_match"] and r["tick_arrays"]]
    return {"descriptors":len(rows),"native_pool_decoded":sum(1 for r in rows if r["pool_decoded"]),
            "descriptor_matches":sum(1 for r in rows if r["descriptor_match"]),
            "tick_array_ready":len(ready),"rows":rows,"priced_live":False,
            "next":"LOCAL_CLMM_SWAP_MATH_ON_NATIVE_DECODED_POOL_AND_TICK_ARRAYS"}

def _orca(root):
    descs=list(_load(Path(root)/ORCA_SRC).get("descriptors") or [])
    rows=[]
    for d in descs:
        pool=d["pool"];expected={d["token_a"],d["token_b"]}
        row={"pool":pool,"descriptor_tokens":sorted(expected),"pool_decoded":False,
             "descriptor_match":False,"role_match":False,"candidate_tick_accounts":[],"errors":[]}
        try:
            raw,slot=_account(pool);dec=decode_orca_pool(raw);row["pool_decoded"]=True;row["slot"]=slot;row["state"]=dec
            row["descriptor_match"]={dec["token_mint_a"],dec["token_mint_b"]}==expected
            row["role_match"]={dec["token_vault_a"],dec["token_vault_b"]}=={d["vault_a"],d["vault_b"]}
        except Exception as e:row["errors"].append("pool:"+type(e).__name__+":"+str(e))
        candidates=runtime_accounts_for_pool(root,pool)
        for a in candidates:
            if a in (pool,d.get("vault_a"),d.get("vault_b")):continue
            try:
                raw,slot=_account(a,2)
                # Keep only program-state-sized accounts that are not SPL token accounts.
                if len(raw)>500:
                    row["candidate_tick_accounts"].append({"address":a,"bytes":len(raw),"slot":slot,
                                                          "discriminator":raw[:8].hex()})
            except Exception:pass
        rows.append(row)
    ready=[r for r in rows if r["pool_decoded"] and r["descriptor_match"] and r["role_match"]]
    return {"descriptors":len(rows),"native_pool_decoded":sum(1 for r in rows if r["pool_decoded"]),
            "descriptor_matches":sum(1 for r in rows if r["descriptor_match"]),
            "role_matches":sum(1 for r in rows if r["role_match"]),
            "pool_state_ready":len(ready),"rows":rows,"priced_live":False,
            "next":"CLASSIFY_ORCA_FIXED_OR_DYNAMIC_TICK_ARRAYS_THEN_BIND_LOCAL_SWAP_MATH"}

def build(root):
    root=Path(root)
    d=_damm(root);cl=_clmm(root);oc=_orca(root)
    payload={"revision":"QARB_055","purpose":"unified_clamm_native_decoder_and_damm_cutover",
             "max_age_ms":MAX_AGE_MS,
             "venues":{"METEORA_DAMM_V2":d,"RAYDIUM_CLMM":cl,"ORCA_WHIRLPOOL":oc},
             "capability":{
               "METEORA_DAMM_V2":{"state_ready":bool(d["live_states"]),"priced_live":d["priced_live"],
                                  "graph_edges_ready":bool(d["edges"])},
               "RAYDIUM_CLMM":{"state_ready":cl["tick_array_ready"]>0,"priced_live":False,
                               "native_decoder_ready":cl["tick_array_ready"]>0},
               "ORCA_WHIRLPOOL":{"state_ready":oc["pool_state_ready"]>0,"priced_live":False,
                                 "native_decoder_ready":oc["pool_state_ready"]>0},
             },
             "next_boundary":{
               "METEORA_DAMM_V2":"MERGE_READY_EDGES_WITH_EXISTING_051D_GRAPH",
               "RAYDIUM_CLMM":cl["next"],
               "ORCA_WHIRLPOOL":oc["next"],
             },
             "execution_authority":False,"paper_only":True}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    p=build(Path.cwd());d=p["venues"]["METEORA_DAMM_V2"];cl=p["venues"]["RAYDIUM_CLMM"];oc=p["venues"]["ORCA_WHIRLPOOL"]
    print("[QARB-055] UNIFIED CLAMM NATIVE DECODER + DAMM CUTOVER")
    print("[DAMM] states=%d edges=%d priced_live=%s"%(d["live_states"],len(d["edges"]),d["priced_live"]))
    print("[CLMM] descriptors=%d pool_decoded=%d descriptor_matches=%d tick_array_ready=%d priced_live=%s"%(
        cl["descriptors"],cl["native_pool_decoded"],cl["descriptor_matches"],cl["tick_array_ready"],cl["priced_live"]))
    for r in cl["rows"]:
        st=r.get("state") or {}
        print("[CLMM_NATIVE] %s decoded=%s match=%s tick_arrays=%d tick=%s spacing=%s liq=%s"%(
            r["pool"][:12],r["pool_decoded"],r["descriptor_match"],len(r["tick_arrays"]),
            st.get("tick_current"),st.get("tick_spacing"),st.get("liquidity")))
    print("[ORCA] descriptors=%d pool_decoded=%d descriptor_matches=%d role_matches=%d pool_state_ready=%d priced_live=%s"%(
        oc["descriptors"],oc["native_pool_decoded"],oc["descriptor_matches"],oc["role_matches"],oc["pool_state_ready"],oc["priced_live"]))
    for r in oc["rows"]:
        st=r.get("state") or {}
        print("[ORCA_NATIVE] %s decoded=%s mint_match=%s role_match=%s tick_candidates=%d tick=%s spacing=%s fee=%s liq=%s"%(
            r["pool"][:12],r["pool_decoded"],r["descriptor_match"],r["role_match"],len(r["candidate_tick_accounts"]),
            st.get("tick_current_index"),st.get("tick_spacing"),st.get("fee_rate"),st.get("liquidity")))
    print("[CAPABILITY] "+json.dumps(p["capability"],sort_keys=True))
    print("[NEXT] "+json.dumps(p["next_boundary"],sort_keys=True))
    print("[REPORT]",OUT)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE")

if __name__=="__main__":main()
