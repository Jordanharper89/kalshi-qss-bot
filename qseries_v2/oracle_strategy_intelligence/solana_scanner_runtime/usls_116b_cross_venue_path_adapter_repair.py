from __future__ import annotations
import json,math
from pathlib import Path

TARGETS=("PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM",
 "RAYDIUM_CPMM","METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM",
 "ORCA","MOONIT","BOOP_FUN","HEAVEN")

ROOTDIR="runtime_state/solana_opportunities/universal_trade_tape"

def _walk(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_walk(v,out)
 elif isinstance(x,list):
  for v in x:_walk(v,out)

def _first(d,*keys):
 for k in keys:
  v=d.get(k)
  if v not in (None,""):return v
 return None

def _num(v):
 try:
  x=float(v)
  return x if math.isfinite(x) else None
 except Exception:return None

def _norm_family(v):
 if not v:return None
 s=str(v).upper().replace("-","_").replace(" ","_")
 aliases={
  "PUMP":"PUMP_FUN","PUMPFUN":"PUMP_FUN","PUMPSWAP":"PUMP_SWAP",
  "RAYDIUM_LAUNCH_LAB":"RAYDIUM_LAUNCHLAB",
  "RAYDIUM_AMM_V4":"RAYDIUM_V4","RAYDIUM_AMM":"RAYDIUM_V4",
  "RAYDIUM_CONCENTRATED":"RAYDIUM_CLMM",
  "RAYDIUM_CONSTANT_PRODUCT":"RAYDIUM_CPMM",
  "METEORA_DAMM":"METEORA_DAMM_V1","DAMM_V1":"METEORA_DAMM_V1",
  "DAMM_V2":"METEORA_DAMM_V2","METEORA_DYNAMIC_AMM_V1":"METEORA_DAMM_V1",
  "METEORA_DYNAMIC_AMM_V2":"METEORA_DAMM_V2",
  "METEORA_DYNAMIC_BONDING_CURVE":"METEORA_DBC",
  "METEORA_DYNAMIC_LIQUIDITY_MARKET_MAKER":"METEORA_DLMM",
  "BOOP":"BOOP_FUN","BOOPFUN":"BOOP_FUN"}
 s=aliases.get(s,s)
 return s if s in TARGETS else None

def _family(row,path):
 for k in ("venue","family","program_family","source_family","launcher_family"):
  f=_norm_family(row.get(k))
  if f:return f
 name=str(path).upper()
 tests=(
  ("PUMPSWAP","PUMP_SWAP"),("PUMP_","PUMP_FUN"),
  ("LAUNCHLAB","RAYDIUM_LAUNCHLAB"),("RAYDIUM_V4","RAYDIUM_V4"),
  ("RAYDIUM_CLMM","RAYDIUM_CLMM"),("RAYDIUM_CPMM","RAYDIUM_CPMM"),
  ("DAMM_V2","METEORA_DAMM_V2"),("DAMM_V1","METEORA_DAMM_V1"),
  ("METEORA_DBC","METEORA_DBC"),("METEORA_DLMM","METEORA_DLMM"),
  ("ORCA","ORCA"),("MOONIT","MOONIT"),("BOOP","BOOP_FUN"),("HEAVEN","HEAVEN"))
 for needle,f in tests:
  if needle in name:return f
 return None

def _economics(row):
 # Prefer explicit normalized economics when present.
 base=_num(_first(row,"base_quantity","base_amount","token_amount"))
 quote=_num(_first(row,"quote_quantity","quote_amount","sol_amount"))
 price=_num(_first(row,"effective_price","price","price_usd","effective_output_per_input"))
 if price is not None and price>0:
  return base,quote,price,"SOURCE_EXPLICIT"
 if base not in (None,0) and quote not in (None,0):
  return base,quote,abs(quote/base),"QUOTE_OVER_BASE"
 # Generic exact swap rows often expose input/output amounts instead.
 inp=_num(_first(row,"input_amount"))
 out=_num(_first(row,"output_amount"))
 if inp not in (None,0) and out not in (None,0):
  return inp,out,abs(out/inp),"OUTPUT_OVER_INPUT"
 eco=row.get("economics")
 if isinstance(eco,dict):
  inp=_num(_first(eco,"input_amount","amount_in","source_amount"))
  out=_num(_first(eco,"output_amount","amount_out","destination_amount"))
  if inp not in (None,0) and out not in (None,0):
   return inp,out,abs(out/inp),"NESTED_OUTPUT_OVER_INPUT"
 return None,None,None,None

def _identity(row):
 market=_first(row,"market_address","pool","pool_address","curve","bonding_curve","amm")
 token=_first(row,"token_address","token","mint","base_mint","trade_mint")
 input_asset=_first(row,"input_mint","input_asset")
 output_asset=_first(row,"output_mint","output_asset")
 # For quote-agnostic venues, preserve the directed asset pair instead of inventing a token/quote role.
 asset_a=token or input_asset
 asset_b=_first(row,"quote_mint") or output_asset
 return market,token,asset_a,asset_b

def run(root):
 root=Path(root);base=root/ROOTDIR;rows=[];seen=set();artifacts=0
 for p in sorted(base.glob("*.json")):
  if p.stat().st_size>120_000_000:continue
  try:d=json.loads(p.read_text(encoding="utf-8"))
  except Exception:continue
  objs=[];_walk(d,objs);used=False
  for o in objs:
   if not isinstance(o,dict):continue
   sig=_first(o,"trade_signature","signature")
   fam=_family(o,p)
   if not sig or not fam:continue
   market,token,asset_a,asset_b=_identity(o)
   if not market:continue
   baseq,quoteq,price,method=_economics(o)
   if price is None or price<=0:continue
   key=(fam,str(sig),str(market),str(asset_a),str(asset_b),method)
   if key in seen:continue
   seen.add(key);used=True
   rows.append({"family":fam,"market_address":market,"token_address":token,
    "asset_a":asset_a,"asset_b":asset_b,"trade_signature":sig,
    "trade_slot":_first(o,"trade_slot","slot"),
    "trade_observed_unix":_first(o,"trade_observed_unix","observed_unix","received_unix","block_time"),
    "side":_first(o,"side","trade_side","direction") or "UNKNOWN",
    "base_quantity":baseq,"quote_quantity":quoteq,"effective_price":price,
    "price_method":method,"source_artifact":str(p.relative_to(root)),
    "decoder_state":_first(o,"decoder_state","decode_status"),
    "execution_authority":False})
  if used:artifacts+=1
 by={}
 for x in rows:by[x["family"]]=by.get(x["family"],0)+1
 missing=[f for f in TARGETS if by.get(f,0)==0]
 return {"revision":"USLS_116B","source_revision":"USLS_116_FAILED",
  "source_artifact_count":artifacts,"economic_row_count":len(rows),
  "family_row_counts":by,"missing_economic_families":missing,"rows":rows,
  "identity_policy":"EXPLICIT_MARKET_PLUS_PRESERVE_DIRECTED_ASSET_PAIR_NO_GUESSED_TOKEN_ROLE",
  "quote_asset_policy":"AGNOSTIC","next_boundary":
   "REBUILD_CROSS_VENUE_PATHS_FROM_REPAIRED_ROWS" if rows else "NO_ECONOMIC_ROWS",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
