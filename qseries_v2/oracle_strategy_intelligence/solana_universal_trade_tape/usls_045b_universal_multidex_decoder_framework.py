from __future__ import annotations
import base64,json,struct
from pathlib import Path

PROGRAMS={
"PUMP_FUN":"6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
"PUMP_SWAP":"pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA",
"RAYDIUM_LAUNCHLAB":"LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj",
"RAYDIUM_V4":"675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
"RAYDIUM_CLMM":"CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK",
"RAYDIUM_CPMM":"CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C",
"METEORA_DBC":"dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN",
"METEORA_DAMM":"cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG",
"METEORA_DLMM":"LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo",
"METEORA_DYN":"Eo7WjKq67jJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB",
"ORCA":"whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
"MOONIT":"MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG",
"BOOP_FUN":"boop8hVGQGqehUK2iVEMEnMrL5RbjywRzHKBmBE7ry4",
"HEAVEN":"HEAVENoP2qxoeuF8Dj2oT1GHEnu49U5mJYkdeC8BAX2o"}

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
PS_BUY=bytes([103,244,82,31,44,245,119,119])
PS_SELL=bytes([62,47,55,10,165,3,220,42])

def b58(raw):
 n=int.from_bytes(raw,"big");s=""
 while n:n,r=divmod(n,58);s=ALPH[r]+s
 pad=len(raw)-len(raw.lstrip(b"\0"))
 return "1"*pad+(s or ("" if pad else "1"))

def decode_pumpswap_program_data(encoded):
 try:raw=base64.b64decode(encoded)
 except Exception:return None
 if len(raw)<184 or raw[:8] not in (PS_BUY,PS_SELL):return None
 vals=struct.unpack_from("<q"+"Q"*13,raw,8)
 pool=b58(raw[120:152]);user=b58(raw[152:184]);side="BUY" if raw[:8]==PS_BUY else "SELL"
 names=("timestamp","base_amount_raw","limit_quote_amount","user_base_token_reserves",
 "user_quote_token_reserves","pool_base_token_reserves","pool_quote_token_reserves",
 "quote_amount_raw","lp_fee_basis_points","lp_fee","protocol_fee_basis_points",
 "protocol_fee","quote_amount_net_or_gross","user_quote_amount")
 d=dict(zip(names,vals));d.update({"side":side,"pool":pool,"user":user,
  "event_discriminator_hex":raw[:8].hex(),"decoder_state":"EXACT_EVENT_PREFIX"})
 return d

def route(venue,line):
 if venue=="PUMP_SWAP" and line.startswith("Program data: "):
  x=decode_pumpswap_program_data(line.split("Program data: ",1)[1])
  if x:return {"decode_status":"EXACT","event":x}
 return {"decode_status":"RAW_RETAINED_DECODER_PENDING","event":None}

def contract():
 return {"revision":"USLS_045B","programs":PROGRAMS,
  "decoder_plugins":{"PUMP_SWAP":"EXACT_EVENT_PREFIX","PUMP_FUN":"CERTIFIED_UPSTREAM_PHASE3"},
  "shared_capture":True,"shared_schema":True,"unknown_retention":True,
  "execution_authority":False,"read_only":True}

def write(root):
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/multidex_decoder_framework.json"
 p.parent.mkdir(parents=True,exist_ok=True);d=contract()
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
