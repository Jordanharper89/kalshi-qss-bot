from __future__ import annotations
import math,time
from collections import defaultdict

def _num(v):
 try:
  x=float(v);return x if math.isfinite(x) else None
 except Exception:return None

def _keys(tx):
 m=((tx or {}).get("transaction") or {}).get("message") or {}
 ks=[x.get("pubkey") if isinstance(x,dict) else x for x in m.get("accountKeys") or []]
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 return ks+(la.get("writable") or [])+(la.get("readonly") or [])

def _all_ix(tx):
 m=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
 for i,ix in enumerate(m.get("instructions") or []):out.append(("top",i,ix))
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  for i,ix in enumerate(g.get("instructions") or []):out.append((f"inner:{g.get('index')}",i,ix))
 return out

def _pid(ix,ks):
 p=ix.get("programId")
 if not p and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(ks):p=ks[ix["programIdIndex"]]
 return p

def _accounts(ix,ks):
 return [ks[a] if isinstance(a,int) and a<len(ks) else a for a in (ix.get("accounts") or [])]

def _token_meta(tx):
 ks=_keys(tx);o={}
 for nm in ("preTokenBalances","postTokenBalances"):
  for x in ((tx or {}).get("meta") or {}).get(nm) or []:
   i=x.get("accountIndex");u=x.get("uiTokenAmount") or {}
   if isinstance(i,int) and i<len(ks) and x.get("mint"):
    o[ks[i]]={"mint":x["mint"],"decimals":int(u.get("decimals") or 0)}
 return o

def _owner_deltas(tx,owner):
 z=defaultdict(lambda:[0,0,None])
 for j,nm in ((0,"preTokenBalances"),(1,"postTokenBalances")):
  for x in ((tx or {}).get("meta") or {}).get(nm) or []:
   if x.get("owner")!=owner or not x.get("mint"):continue
   u=x.get("uiTokenAmount") or {};z[x["mint"]][j]+=int(u.get("amount") or 0);z[x["mint"]][2]=u.get("decimals")
 return {m:(b-a)/(10**int(d)) for m,(a,b,d) in z.items() if d is not None and b!=a}

def _parent(level,ordinal):
 return int(str(level).split(":",1)[1]) if str(level).startswith("inner:") else int(ordinal)

def _transfers(tx,parent):
 tm=_token_meta(tx);out=[]
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  if g.get("index")!=parent:continue
  for ix in g.get("instructions") or []:
   q=ix.get("parsed")
   if not isinstance(q,dict):continue
   i=q.get("info") or {};typ=q.get("type");s=i.get("source");d=i.get("destination")
   if typ not in ("transfer","transferChecked","transferCheckedWithFee") or not s or not d:continue
   if i.get("lamports") is not None:
    out.append({"source":s,"destination":d,"amount":int(i["lamports"])/1e9,"asset":"NATIVE_SOL"});continue
   ta=i.get("tokenAmount");z=tm.get(s) or tm.get(d);amt=None
   if isinstance(ta,dict) and ta.get("amount") is not None:amt=int(ta["amount"])/(10**int(ta.get("decimals") or 0))
   elif i.get("amount") is not None and z:amt=int(i["amount"])/(10**z["decimals"])
   out.append({"source":s,"destination":d,"amount":amt,"asset":(z or {}).get("mint")})
 return out

def _sum(ts,s,d,asset=None):
 vals=[x["amount"] for x in ts if x["source"]==s and x["destination"]==d and x.get("amount") is not None
       and (asset is None or x.get("asset")==asset)]
 return sum(vals) if vals else None

def _row(fam,sig,market,trader,im,ia,om,oa,side,obs,method,extra=None):
 ia=_num(ia);oa=_num(oa)
 if not market or not im or not om or ia is None or oa is None or ia<=0 or oa<=0:return None
 d={"family":fam,"trade_signature":sig,"market_address":market,"trader":trader,
    "input_asset":im,"input_amount":ia,"output_asset":om,"output_amount":oa,
    "effective_output_per_input":oa/ia,"side":side or "UNKNOWN_TRADE_TYPE",
    "observed_unix":float(obs or time.time()),"economics_method":method,
    "strict_live_provenance":True,"execution_authority":False}
 if extra:d.update(extra)
 return d

def _pumpswap(sig,tx,obs):
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_045b_universal_multidex_decoder_framework import decode_pumpswap_program_data
 ev=[]
 for line in ((tx or {}).get("meta") or {}).get("logMessages") or []:
  if line.startswith("Program data: "):
   x=decode_pumpswap_program_data(line.split("Program data: ",1)[1])
   if x:ev.append(x)
 out=[]
 for e in ev:
  d=_owner_deltas(tx,e["user"]);pos=[(m,v) for m,v in d.items() if v>0];neg=[(m,-v) for m,v in d.items() if v<0]
  if len(pos)!=1 or len(neg)!=1:continue
  if e["side"]=="BUY":im,ia=neg[0];om,oa=pos[0]
  else:im,ia=pos[0];om,oa=neg[0]
  r=_row("PUMP_SWAP",sig,e["pool"],e["user"],im,ia,om,oa,e["side"],obs,"PUMPSWAP_EVENT_PLUS_USER_TOKEN_DELTA")
  if r:out.append(r)
 return out

def _raydium(fam,sig,tx,obs):
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_050_raydium_multifamily_swap_registry import PROGRAMS,classify
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_052_raydium_exact_swap_instruction_decoder import b58d
 fam0=fam;pid=PROGRAMS[fam0];ks=_keys(tx);out=[]
 for level,ordinal,ix in _all_ix(tx):
  if _pid(ix,ks)!=pid or not ix.get("data"):continue
  c=classify(fam0,b58d(ix["data"]))
  if not c["is_exact_swap"]:continue
  ac=_accounts(ix,ks);pi=c["pool_account_index"];pool=ac[pi] if pi<len(ac) else None
  signers=[x.get("pubkey") for x in ((((tx or {}).get("transaction") or {}).get("message") or {}).get("accountKeys") or [])
           if isinstance(x,dict) and x.get("signer") and x.get("pubkey")]
  cand=[]
  for s in signers:
   d=_owner_deltas(tx,s);neg=[(m,-v) for m,v in d.items() if v<0];pos=[(m,v) for m,v in d.items() if v>0]
   if len(neg)==1 and len(pos)==1:cand.append((s,neg[0],pos[0]))
  if len(cand)!=1:continue
  trader,(im,ia),(om,oa)=cand[0]
  r=_row(fam,sig,pool,trader,im,ia,om,oa,"UNKNOWN_TRADE_TYPE",obs,"RAYDIUM_EXACT_INSTRUCTION_PLUS_SIGNER_DELTA",
         {"instruction_name":c["instruction_name"]})
  if r:out.append(r)
 return out

def _launchlab(sig,tx,obs):
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_060_launchlab_official_trade_contract import PROGRAM,classify,roles
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_052_raydium_exact_swap_instruction_decoder import b58d
 ks=_keys(tx);out=[]
 for level,ordinal,ix in _all_ix(tx):
  if _pid(ix,ks)!=PROGRAM or not ix.get("data"):continue
  c=classify(b58d(ix["data"]))
  if not c["is_exact_trade"]:continue
  rr=roles(_accounts(ix,ks));payer=rr["payer"];d=_owner_deltas(tx,payer)
  base,quote=rr["base_token_mint"],rr["quote_token_mint"];bd=d.get(base);qd=d.get(quote)
  if bd is None or qd is None or bd<=0 or qd>=0:continue
  r=_row("RAYDIUM_LAUNCHLAB",sig,rr["pool_state"],payer,quote,-qd,base,bd,"BUY",obs,
         "LAUNCHLAB_OFFICIAL_ROLES_PLUS_SIGNER_DELTA",{"instruction_name":c["instruction_name"]})
  if r:out.append(r)
 return out

def _meteora_orca(fam,sig,tx,obs):
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_065_meteora_orca_official_swap_registry import PROGRAMS,classify
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_067_meteora_orca_exact_swap_instruction_census import b58d
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_071_meteora_orca_source_certified_role_decoder import ROLE
 venue="METEORA_DAMM" if fam=="METEORA_DAMM_V2" else fam
 pid=PROGRAMS[venue];ks=_keys(tx);out=[]
 for level,ordinal,ix in _all_ix(tx):
  if _pid(ix,ks)!=pid or not ix.get("data"):continue
  c=classify(venue,b58d(ix["data"]))
  if not c["is_exact_swap"]:continue
  ac=_accounts(ix,ks);spec=ROLE.get((venue,c["instruction_name"]))
  if fam=="METEORA_DBC":spec={"pool":2,"user_in":3,"user_out":4,"vault_a":5,"vault_b":6,"mint_a":7,"mint_b":8,"trader":9}
  if not spec:continue
  rr={k:(ac[i] if i<len(ac) else None) for k,i in spec.items()}
  ts=_transfers(tx,_parent(level,ordinal));e=None
  if fam=="METEORA_DBC":
   ai=_sum(ts,rr["user_in"],rr["vault_a"]);bi=_sum(ts,rr["user_in"],rr["vault_b"])
   ao=_sum(ts,rr["vault_a"],rr["user_out"]);bo=_sum(ts,rr["vault_b"],rr["user_out"])
   if ai and bo:e=(rr["mint_a"],ai,rr["mint_b"],bo)
   elif bi and ao:e=(rr["mint_b"],bi,rr["mint_a"],ao)
  elif fam=="METEORA_DAMM_V2":
   ai=_sum(ts,rr["user_in"],rr["vault_a"]);bi=_sum(ts,rr["user_in"],rr["vault_b"])
   ao=_sum(ts,rr["vault_a"],rr["user_out"]);bo=_sum(ts,rr["vault_b"],rr["user_out"])
   if ai and bo:e=(rr["mint_a"],ai,rr["mint_b"],bo)
   elif bi and ao:e=(rr["mint_b"],bi,rr["mint_a"],ao)
  elif fam=="METEORA_DLMM":
   xi=_sum(ts,rr["user_in"],rr["vault_x"]);yi=_sum(ts,rr["user_in"],rr["vault_y"])
   xo=_sum(ts,rr["vault_x"],rr["user_out"]);yo=_sum(ts,rr["vault_y"],rr["user_out"])
   if xi and yo:e=(rr["mint_x"],xi,rr["mint_y"],yo)
   elif yi and xo:e=(rr["mint_y"],yi,rr["mint_x"],xo)
  elif fam=="ORCA":
   tm=_token_meta(tx);va,vb=rr["vault_a"],rr["vault_b"]
   ai=_sum(ts,rr["user_a"],va);bi=_sum(ts,rr["user_b"],vb);ao=_sum(ts,va,rr["user_a"]);bo=_sum(ts,vb,rr["user_b"])
   ma=(tm.get(va) or {}).get("mint");mb=(tm.get(vb) or {}).get("mint")
   if ai and bo and ma and mb:e=(ma,ai,mb,bo)
   elif bi and ao and ma and mb:e=(mb,bi,ma,ao)
  if not e:continue
  trader=rr.get("trader")
  r=_row(fam,sig,rr.get("pool"),trader,e[0],e[1],e[2],e[3],"UNKNOWN_TRADE_TYPE",obs,
         "SOURCE_CERTIFIED_ROLE_PLUS_EXACT_TRANSFER_RECONCILIATION",{"instruction_name":c["instruction_name"]})
  if r:out.append(r)
 return out

def _remaining(fam,sig,tx,obs):
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_086_remaining_venue_program_contract import PROGRAMS
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_090_remaining_venue_source_semantic_registry import SEMANTICS
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_091_remaining_venue_exact_trade_census import b58d
 ks=_keys(tx);pid=PROGRAMS[fam];out=[]
 for level,ordinal,ix in _all_ix(tx):
  if _pid(ix,ks)!=pid or not ix.get("data"):continue
  raw=b58d(ix["data"]);disc=raw[:8].hex() if len(raw)>=8 else raw.hex();sem=SEMANTICS.get(fam,{}).get(disc)
  if not sem:continue
  ac=_accounts(ix,ks);rr={k:(ac[i] if i<len(ac) else None) for i,k in enumerate(sem["roles"])}
  if not all(rr.values()):continue
  ts=_transfers(tx,_parent(level,ordinal));side=sem["side"];e=None;market=trader=None
  if fam=="BOOP_FUN":
   market=rr["bonding_curve"]
   if side=="BUY":
    ia=_sum(ts,rr["buyer"],rr["bonding_curve_sol_vault"],"NATIVE_SOL");oa=_sum(ts,rr["bonding_curve_vault"],rr["recipient_token_account"])
    e=("NATIVE_SOL",ia,rr["mint"],oa);trader=rr["buyer"]
   else:
    ia=_sum(ts,rr["seller_token_account"],rr["bonding_curve_vault"]);oa=_sum(ts,rr["bonding_curve_sol_vault"],rr["recipient"],"NATIVE_SOL")
    e=(rr["mint"],ia,"NATIVE_SOL",oa);trader=rr["seller"]
  elif fam=="HEAVEN":
   market=rr["liquidity_pool_state"];trader=rr["user"]
   if side=="BUY":
    ia=_sum(ts,rr["user_token_b_vault"],rr["token_b_vault"]);oa=_sum(ts,rr["token_a_vault"],rr["user_token_a_vault"])
    e=(rr["token_b_mint"],ia,rr["token_a_mint"],oa)
   else:
    ia=_sum(ts,rr["user_token_a_vault"],rr["token_a_vault"]);oa=_sum(ts,rr["token_b_vault"],rr["user_token_b_vault"])
    e=(rr["token_a_mint"],ia,rr["token_b_mint"],oa)
  elif fam=="MOONIT":
   from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_095e_moonit_curve_fee_delta_exact_economics import lamport_delta
   market=rr["curve_account"];trader=rr["sender"];curve=lamport_delta(tx,market);dex=lamport_delta(tx,rr["dex_fee"]);helio=lamport_delta(tx,rr["helio_fee"])
   if side=="BUY":
    token_out=_sum(ts,rr["curve_token_account"],rr["sender_token_account"])
    sol=(curve+dex+helio)/1e9 if None not in (curve,dex,helio) else None;e=("NATIVE_SOL",sol,rr["mint"],token_out)
   else:
    token_in=_sum(ts,rr["sender_token_account"],rr["curve_token_account"])
    sol=(-curve-dex-helio)/1e9 if None not in (curve,dex,helio) else None;e=(rr["mint"],token_in,"NATIVE_SOL",sol)
  if not e:continue
  r=_row(fam,sig,market,trader,e[0],e[1],e[2],e[3],side,obs,"SOURCE_SEMANTIC_ROLES_PLUS_EXACT_TRANSFER_ECONOMICS")
  if r:out.append(r)
 return out

SUPPORTED=("PUMP_SWAP","RAYDIUM_V4","RAYDIUM_CLMM","RAYDIUM_CPMM","RAYDIUM_LAUNCHLAB",
 "METEORA_DBC","METEORA_DAMM_V2","METEORA_DLMM","ORCA","MOONIT","BOOP_FUN","HEAVEN")
PENDING={"PUMP_FUN":"EXACT_TRADE_EVENT_EXISTS_BUT_CURRENT_REPO_DOES_NOT_EXPOSE_EXACT_CURVE_ROLE_FROM_ARBITRARY_LIVE_TRADE_TX",
 "METEORA_DAMM_V1":"CURRENT_ROUTER_LABEL_METEORA_DYN_MUST_NOT_BE_CONFLATED_WITH_DAMM_V1"}

def decode_live_trade(family,signature,transaction,observed_unix=None):
 fam=str(family or "").upper()
 if fam=="METEORA_DAMM":fam="METEORA_DAMM_V2"
 if fam=="PUMP_SWAP":return _pumpswap(signature,transaction,observed_unix)
 if fam in ("RAYDIUM_V4","RAYDIUM_CLMM","RAYDIUM_CPMM"):return _raydium(fam,signature,transaction,observed_unix)
 if fam=="RAYDIUM_LAUNCHLAB":return _launchlab(signature,transaction,observed_unix)
 if fam in ("METEORA_DBC","METEORA_DAMM_V2","METEORA_DLMM","ORCA"):return _meteora_orca(fam,signature,transaction,observed_unix)
 if fam in ("MOONIT","BOOP_FUN","HEAVEN"):return _remaining(fam,signature,transaction,observed_unix)
 return []

def contract():
 return {"revision":"USLS_161K","supported_families":list(SUPPORTED),"pending_families":PENDING,
  "input_contract":["family","signature","transaction","observed_unix"],
  "output_contract":["family","trade_signature","market_address","input_asset","input_amount","output_asset","output_amount",
   "effective_output_per_input","observed_unix","strict_live_provenance"],
  "no_artifact_loader_as_decoder":True,"unknown_retention_required":True,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
