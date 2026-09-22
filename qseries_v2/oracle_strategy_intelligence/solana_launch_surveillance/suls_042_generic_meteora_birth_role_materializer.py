from __future__ import annotations
import json,hashlib
WSOL="So11111111111111111111111111111111111111112"
DAMM="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"

def _damm_pool_identity(b, trade_mint):
    e=b.get("envelope") or {}
    raw=e.get("raw_transaction") or {}
    msg=(raw.get("transaction") or {}).get("message") or {}
    meta=raw.get("meta") or {}
    keys=msg.get("accountKeys") or []
    def key(x):
        if isinstance(x,str): return x
        if isinstance(x,int) and 0 <= x < len(keys):
            v=keys[x]
            return v.get("pubkey") if isinstance(v,dict) else v
        return None
    for grp in meta.get("innerInstructions") or []:
        for ix in grp.get("instructions") or []:
            if not isinstance(ix,dict): continue
            program=ix.get("programId") or key(ix.get("programIdIndex"))
            if program != DAMM: continue
            a=[key(x) for x in (ix.get("accounts") or [])]
            if len(a) < 21: continue
            pool,mint_a,mint_b,vault_a,vault_b=a[7],a[9],a[10],a[11],a[12]
            if trade_mint not in (mint_a,mint_b) or WSOL not in (mint_a,mint_b): continue
            if mint_a == trade_mint:
                return {"pair_address":pool,"token_address":trade_mint,
                        "token_vault":vault_a,"quote_vault":vault_b}
            return {"pair_address":pool,"token_address":trade_mint,
                    "token_vault":vault_b,"quote_vault":vault_a}
    return None


def _materialize(b):
 e=b.get("envelope") or {};raw=e.get("raw_transaction") or {};meta=raw.get("meta") or {}
 position=set();transfers=[];created={}
 for grp in meta.get("innerInstructions") or []:
  for ix in grp.get("instructions") or []:
   if not isinstance(ix,dict):continue
   p=ix.get("parsed") or {};info=p.get("info") or {};typ=p.get("type")
   if typ=="initializeTokenMetadata" and info.get("name")=="Meteora Position NFT" and info.get("mint"):
    position.add(info["mint"])
   if typ=="createAccount" and info.get("newAccount"):
    created[info["newAccount"]]={"owner_program":info.get("owner"),"space":info.get("space")}
   if typ=="transferChecked":
    amt=(info.get("tokenAmount") or {}).get("uiAmountString")
    if info.get("mint") and info.get("destination") and amt is not None:
     transfers.append({"mint":info["mint"],"destination":info["destination"],"amount":amt})
 mints={x["mint"] for x in transfers}
 trade=sorted(m for m in mints if m!=WSOL and m not in position)
 if len(trade)!=1 or WSOL not in mints:return None
 t=trade[0]
 tv=next((x for x in transfers if x["mint"]==t),None)
 qv=next((x for x in transfers if x["mint"]==WSOL),None)
 if not tv or not qv:return None
 ident=_damm_pool_identity(b,t)
 if not ident:return None
 rawid=f'{b["signature"]}|{t}|{WSOL}|{DAMM}'
 return {"event_id":"suls-birth-"+hashlib.sha256(rawid.encode()).hexdigest(),
  "state":"DISCOVERED","signature":b["signature"],"slot":b["slot"],"block_time":b["block_time"],
  "observed_unix":b.get("observed_unix"),"launcher_family":"METEORA_DAMM_V2","program_id":DAMM,
  "token_mint":t,"token_address":ident["token_address"],"pair_address":ident["pair_address"],"quote_mint":WSOL,"token_vault":ident["token_vault"],"quote_vault":ident["quote_vault"],
  "initial_token_amount":tv["amount"],"initial_quote_amount":qv["amount"],
  "position_nft_mints":sorted(position),"execution_authority":False}

def run(root):
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 inp=json.loads((base/"continuous_native_birth_inbox.json").read_text(encoding="utf-8"))
 oldp=base/"continuous_tradeable_birth_events.json"
 old=json.loads(oldp.read_text(encoding="utf-8")) if oldp.exists() else {"events":[]}
 events=list(old.get("events") or []);seen={x["signature"] for x in events};new=[]
 for b in inp.get("births",[]):
  if b.get("signature") in seen:continue
  x=_materialize(b)
  if x:events.append(x);new.append(x);seen.add(x["signature"])
 out={"revision":"SULS_042","event_count":len(events),"new_events":len(new),"events":events,
  "execution_authority":False,"read_only":True}
 oldp.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out
