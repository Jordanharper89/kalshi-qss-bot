from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_139_phase7_missing_venue_transaction_hydration.py"
TEST=ROOT/"test_usls_139_phase7_missing_venue_transaction_hydration.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path

MISSING=("PUMP_FUN","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM","RAYDIUM_CPMM",
 "METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM",
 "ORCA","MOONIT","BOOP_FUN","HEAVEN")
SRC="runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"

def _rpc(method,params,timeout=20.0):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 return _rpc(method,params,timeout)

def run(root):
 root=Path(root);d=json.loads((root/SRC).read_text(encoding="utf-8"))
 chosen={}
 for x in d.get("rows",[]):
  f=x.get("family");sig=x.get("trade_signature")
  if f in MISSING and sig and f not in chosen:chosen[f]=x
 rows=[]
 for i,f in enumerate(MISSING):
  x=chosen.get(f);tx=None;err=None
  if x:
   try:
    tx=_rpc("getTransaction",[x["trade_signature"],{"commitment":"confirmed",
      "encoding":"jsonParsed","maxSupportedTransactionVersion":1}],20.0)
   except Exception as e:err=repr(e)
  meta=(tx or {}).get("meta") or {}
  rows.append({"family":f,"trade_signature":None if x is None else x.get("trade_signature"),
   "market_address":None if x is None else x.get("market_address"),
   "tx_found":isinstance(tx,dict),"rpc_error":err,
   "slot":None if tx is None else tx.get("slot"),
   "block_time":None if tx is None else tx.get("blockTime"),
   "network_fee_lamports":meta.get("fee"),
   "pre_token_balances":meta.get("preTokenBalances") or [],
   "post_token_balances":meta.get("postTokenBalances") or [],
   "pre_balances":meta.get("preBalances") or [],
   "post_balances":meta.get("postBalances") or [],
   "transaction":tx,"execution_authority":False})
  if i+1<len(MISSING):time.sleep(0.7)
 return {"revision":"USLS_139","family_count":len(rows),
  "tx_found_count":sum(x["tx_found"] for x in rows),
  "fee_found_count":sum(x["network_fee_lamports"] is not None for x in rows),
  "rows":rows,"next_boundary":"POOL_VAULT_PRE_POST_STATE_RECONSTRUCTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_missing_venue_transaction_hydration.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_139_phase7_missing_venue_transaction_hydration import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"family_count":d["family_count"],
   "tx_found_count":d["tx_found_count"],"fee_found_count":d["fee_found_count"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertEqual(d["family_count"],13)
  self.assertGreater(d["tx_found_count"],0,"NO_MISSING_VENUE_TRANSACTIONS_HYDRATED")
  self.assertGreater(d["fee_found_count"],0,"NO_NETWORK_FEES_RECOVERED")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-139 missing-venue transaction hydration")
  print("[PASS] transaction fee + pre/post account state physically recovered")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_140_phase7_pool_vault_prepost_state_reconstructor.py"
TEST=ROOT/"test_usls_140_phase7_pool_vault_prepost_state_reconstructor.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

HYD="runtime_state/solana_opportunities/solana_scanner/phase7_missing_venue_transaction_hydration.json"

def _keys(tx):
 msg=((tx or {}).get("transaction") or {}).get("message") or {}
 out=[]
 for a in msg.get("accountKeys") or []:
  if isinstance(a,str):out.append(a)
  elif isinstance(a,dict):out.append(a.get("pubkey"))
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 if isinstance(la,dict):
  out += la.get("writable") or [];out += la.get("readonly") or []
 return out

def _token_map(rows):
 out={}
 for x in rows:
  try:
   idx=int(x.get("accountIndex"));amt=int((x.get("uiTokenAmount") or {}).get("amount") or 0)
   dec=int((x.get("uiTokenAmount") or {}).get("decimals") or 0)
   out[idx]={"mint":x.get("mint"),"owner":x.get("owner"),"amount_raw":amt,"decimals":dec}
  except Exception:pass
 return out

def run(root):
 root=Path(root);h=json.loads((root/HYD).read_text(encoding="utf-8"))
 rows=[];fam={}
 for x in h.get("rows",[]):
  tx=x.get("transaction")
  if not isinstance(tx,dict):continue
  keys=_keys(tx);pre=_token_map(x.get("pre_token_balances") or []);post=_token_map(x.get("post_token_balances") or [])
  changes=[]
  for idx in sorted(set(pre)|set(post)):
   a=pre.get(idx,{});b=post.get(idx,{})
   ar=a.get("amount_raw",0);br=b.get("amount_raw",0)
   if ar==br:continue
   changes.append({"account_index":idx,"account":keys[idx] if idx<len(keys) else None,
    "mint":b.get("mint") or a.get("mint"),"owner":b.get("owner") or a.get("owner"),
    "pre_amount_raw":ar,"post_amount_raw":br,"delta_raw":br-ar,
    "decimals":b.get("decimals",a.get("decimals"))})
  # Strictly expose balance-changing token accounts; do not label them pool vaults without lineage.
  rows.append({"family":x["family"],"trade_signature":x.get("trade_signature"),
   "market_address":x.get("market_address"),"token_account_changes":changes,
   "changed_token_account_count":len(changes),
   "pool_vault_identity_state":"UNRESOLVED_UNLESS_ACCOUNT_ROLE_LINEAGE_MATCHES",
   "execution_authority":False})
  z=fam.setdefault(x["family"],{"rows":0,"with_token_changes":0})
  z["rows"]+=1;z["with_token_changes"]+=bool(changes)
 return {"revision":"USLS_140","row_count":len(rows),
  "family_support":fam,"rows":rows,
  "liquidity_semantics":"PRE_POST_TOKEN_ACCOUNT_STATE_AVAILABLE_BUT_POOL_VAULT_ROLE_NOT_GUESSED",
  "next_boundary":"LIVE_PROSPECTIVE_MISSING_VENUE_LATENCY_COHORT",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_pool_vault_prepost_state.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_140_phase7_pool_vault_prepost_state_reconstructor import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  changed=sum(v["with_token_changes"] for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"rows_with_token_changes":changed,
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(changed,0,"NO_PRE_POST_TOKEN_ACCOUNT_CHANGES_RECOVERED")
  self.assertIn("NOT_GUESSED",d["liquidity_semantics"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-140 pool/vault pre-post state reconstructor")
  print("[PASS] token-account reserve state recovered without guessing pool-vault identity")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
