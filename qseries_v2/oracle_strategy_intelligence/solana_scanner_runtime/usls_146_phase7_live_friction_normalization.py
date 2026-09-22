from __future__ import annotations
import json
from pathlib import Path

HYD="runtime_state/solana_opportunities/solana_scanner/phase7_live_multifamily_transaction_hydration.json"
DEL="runtime_state/solana_opportunities/solana_scanner/phase7_live_token_account_deltas.json"
ROLE="runtime_state/solana_opportunities/solana_scanner/phase7_certified_vault_role_match.json"

def _load(root,p):return json.loads((Path(root)/p).read_text(encoding="utf-8"))

def run(root):
 h=_load(root,HYD);d=_load(root,DEL);r=_load(root,ROLE)
 didx={x["trade_signature"]:x for x in d.get("rows",[])}
 ridx={x["trade_signature"]:x for x in r.get("rows",[])}
 rows=[];fam={}
 for x in h.get("rows",[]):
  sig=x["trade_signature"];dx=didx.get(sig,{});rx=ridx.get(sig,{})
  matches=rx.get("certified_role_matches") or []
  liq_ready=bool(matches)
  rows.append({"family":x["family"],"trade_signature":sig,
   "observation_latency_seconds":x.get("observation_latency_seconds"),
   "network_fee_lamports":x.get("network_fee_lamports"),
   "changed_token_account_count":dx.get("changed_token_account_count",0),
   "certified_role_match_count":len(matches),
   "liquidity_reference_ready":liq_ready,
   "fee_state":"NETWORK_FEE_PHYSICAL_PROTOCOL_FEE_UNRESOLVED",
   "slippage_state":"UNRESOLVED_UNTIL_PRETRADE_REFERENCE_AND_VAULT_ROLE_AVAILABLE",
   "execution_authority":False})
  z=fam.setdefault(x["family"],{"rows":0,"latency":0,"network_fee":0,"liquidity_reference":0})
  z["rows"]+=1;z["latency"]+=x.get("observation_latency_seconds") is not None
  z["network_fee"]+=x.get("network_fee_lamports") is not None
  z["liquidity_reference"]+=liq_ready
 return {"revision":"USLS_146","row_count":len(rows),"family_support":fam,"rows":rows,
  "strict_policy":"NETWORK_FEE_IS_NOT_PROTOCOL_FEE_AND_CHANGED_TOKEN_ACCOUNT_IS_NOT_POOL_LIQUIDITY_WITHOUT_ROLE_PROOF",
  "next_boundary":"PHASE7_LIVE_FRICTION_COVERAGE_CHECKPOINT",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_live_friction_normalized.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
