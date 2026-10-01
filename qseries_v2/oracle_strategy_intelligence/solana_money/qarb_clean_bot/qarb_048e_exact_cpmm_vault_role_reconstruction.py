from __future__ import annotations
import json
from pathlib import Path

ROLES = Path("runtime_state/solana_opportunities/universal_trade_tape/raydium_exact_instruction_pool_roles.json")
ORIENT = Path("runtime_state/solana_opportunities/universal_trade_tape/raydium_exact_pair_orientation.json")
OUT = Path("runtime_state/qseries/qarb_clean_bot/raydium_cpmm_canonical_live_descriptors.json")
EXECUTION_AUTHORITY = False
READ_ONLY = True

def _rows(obj):
    if isinstance(obj, list): return obj
    if isinstance(obj, dict):
        for k in ("rows","swaps","records"):
            if isinstance(obj.get(k), list): return obj[k]
    return []

def _pk(x):
    if isinstance(x, str): return x
    if isinstance(x, dict):
        return x.get("pubkey") or x.get("address") or x.get("key")
    return None

def _account_keys(tx):
    msg = (((tx or {}).get("transaction") or {}).get("message") or {})
    return [_pk(x) for x in (msg.get("accountKeys") or [])]

def _token_balances(tx):
    meta = (tx or {}).get("meta") or {}
    merged = {}
    for side in ("preTokenBalances","postTokenBalances"):
        for b in meta.get(side) or []:
            try: idx = int(b["accountIndex"])
            except Exception: continue
            r = merged.setdefault(idx, {"mints":set(),"pre":None,"post":None})
            if b.get("mint"): r["mints"].add(b["mint"])
            amt = (((b.get("uiTokenAmount") or {}).get("amount")))
            if amt is not None:
                try: amt = int(amt)
                except Exception: amt = None
            if side.startswith("pre"): r["pre"] = amt
            else: r["post"] = amt
    return merged

def _orientation(rows):
    out = {}
    for r in rows:
        if str(r.get("venue","")).upper() != "RAYDIUM_CPMM": continue
        pool=r.get("pool"); sig=r.get("signature")
        a=r.get("input_mint"); b=r.get("output_mint")
        if pool and a and b and a != b:
            out[(pool,sig)] = (a,b,r)
            out.setdefault((pool,None),(a,b,r))
    return out

def reconstruct(role, orient):
    pool=role.get("pool"); sig=role.get("signature")
    pair=orient.get((pool,sig)) or orient.get((pool,None))
    if not pair: return None,"NO_EXACT_PAIR_ORIENTATION"
    mint_a,mint_b,orow=pair
    tx=role.get("transaction") or {}
    keys=_account_keys(tx); balances=_token_balances(tx)
    if not keys or not balances: return None,"NO_TRANSACTION_TOKEN_BALANCE_MAP"
    ix={k:i for i,k in enumerate(keys) if k}
    inst=[_pk(x) for x in (role.get("accounts") or [])]
    inst={x for x in inst if x}
    excluded={role.get("user_source_token_account"),role.get("user_destination_token_account")}
    excluded.discard(None)

    def candidates(mint):
        c=[]
        for addr in inst:
            i=ix.get(addr)
            if i is None or addr in excluded: continue
            b=balances.get(i)
            if not b or mint not in b["mints"]: continue
            changed=(b["pre"] is not None and b["post"] is not None and b["pre"] != b["post"])
            c.append((addr,changed,i,b["pre"],b["post"]))
        c.sort(key=lambda x:(not x[1],x[2]))
        return c

    ca,cb=candidates(mint_a),candidates(mint_b)
    if len(ca)!=1 or len(cb)!=1:
        return None,"AMBIGUOUS_VAULTS:%d:%d"%(len(ca),len(cb))
    va,vb=ca[0][0],cb[0][0]
    if va==vb: return None,"SAME_VAULT"
    return {
        "venue":"RAYDIUM_CPMM","pool":pool,
        "token_a":mint_a,"token_b":mint_b,
        "vault_a":va,"vault_b":vb,
        "fee_numerator":25,"fee_denominator":10000,
        "source_signature":sig,
        "source_pool_role_state":role.get("pool_role_state"),
        "source_decoder_state":orow.get("decoder_state"),
        "vault_role_method":"EXACT_INSTRUCTION_ACCOUNT_X_TRANSACTION_TOKEN_BALANCE",
        "execution_authority":False
    },None

def build(root=Path.cwd()):
    roles_path=root/ROLES; orient_path=root/ORIENT
    if not roles_path.is_file(): raise RuntimeError("MISSING:"+str(ROLES))
    if not orient_path.is_file(): raise RuntimeError("MISSING:"+str(ORIENT))
    roles=_rows(json.loads(roles_path.read_text(encoding="utf-8")))
    ors=_rows(json.loads(orient_path.read_text(encoding="utf-8")))
    oi=_orientation(ors); found={}; failures=[]
    for r in roles:
        if str(r.get("venue","")).upper()!="RAYDIUM_CPMM": continue
        if str(r.get("pool_role_state","")).upper()!="EXACT": continue
        row,err=reconstruct(r,oi)
        if row: found[row["pool"]]=row
        else: failures.append({"pool":r.get("pool"),"signature":r.get("signature"),"reason":err})
    payload={"revision":"QARB_048E","rows":list(found.values()),"failures":failures,
             "descriptor_count":len(found),"failure_count":len(failures),
             "read_only":True,"execution_authority":False}
    path=root/OUT;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    print("[QARB-048E] EXACT CPMM VAULT-ROLE RECONSTRUCTION")
    p=build(Path.cwd())
    print("[DESCRIPTOR_COUNT]",p["descriptor_count"])
    print("[FAILURE_COUNT]",p["failure_count"])
    for r in p["rows"]:
        print("[CPMM_DESCRIPTOR] pool=%s token_a=%s token_b=%s vault_a=%s vault_b=%s"%(
            r["pool"][:12],r["token_a"][:12],r["token_b"][:12],r["vault_a"][:12],r["vault_b"][:12]))
    for f in p["failures"][:20]:
        print("[CPMM_HOLD] pool=%s reason=%s"%(str(f.get("pool"))[:12],f["reason"]))
    print("[REPORT]",OUT)
    print("[MODE] READ_ONLY=True execution_authority=FALSE")

if __name__=="__main__": main()
