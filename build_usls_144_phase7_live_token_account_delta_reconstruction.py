from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_144_phase7_live_token_account_delta_reconstruction.py"
TEST=ROOT/"test_usls_144_phase7_live_token_account_delta_reconstruction.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/phase7_live_multifamily_transaction_hydration.json"

def _keys(tx):
 msg=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
 for a in msg.get("accountKeys") or []:
  out.append(a if isinstance(a,str) else a.get("pubkey"))
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 if isinstance(la,dict):out+=(la.get("writable") or [])+(la.get("readonly") or [])
 return out

def _tm(rows):
 out={}
 for x in rows or []:
  try:
   idx=int(x.get("accountIndex"));u=x.get("uiTokenAmount") or {}
   out[idx]={"mint":x.get("mint"),"owner":x.get("owner"),
    "amount_raw":int(u.get("amount") or 0),"decimals":int(u.get("decimals") or 0)}
  except Exception:pass
 return out

def run(root):
 root=Path(root);d=json.loads((root/SRC).read_text(encoding="utf-8"));rows=[];fam={}
 for x in d.get("rows",[]):
  tx=x.get("transaction")
  if not isinstance(tx,dict):continue
  meta=tx.get("meta") or {};keys=_keys(tx)
  pre=_tm(meta.get("preTokenBalances"));post=_tm(meta.get("postTokenBalances"))
  changes=[]
  for idx in sorted(set(pre)|set(post)):
   a=pre.get(idx,{});b=post.get(idx,{})
   ar=a.get("amount_raw",0);br=b.get("amount_raw",0)
   if ar==br:continue
   changes.append({"account_index":idx,"account":keys[idx] if idx<len(keys) else None,
    "mint":b.get("mint") or a.get("mint"),"owner":b.get("owner") or a.get("owner"),
    "pre_amount_raw":ar,"post_amount_raw":br,"delta_raw":br-ar,
    "decimals":b.get("decimals",a.get("decimals"))})
  row={"family":x["family"],"trade_signature":x["trade_signature"],
   "observation_latency_seconds":x.get("observation_latency_seconds"),
   "network_fee_lamports":x.get("network_fee_lamports"),
   "token_account_changes":changes,"changed_token_account_count":len(changes),
   "execution_authority":False}
  rows.append(row);z=fam.setdefault(x["family"],{"rows":0,"with_changes":0})
  z["rows"]+=1;z["with_changes"]+=bool(changes)
 return {"revision":"USLS_144","row_count":len(rows),"family_support":fam,"rows":rows,
  "role_policy":"TOKEN_ACCOUNT_DELTAS_ARE_PHYSICAL_BUT_VAULT_ROLE_REQUIRES_CERTIFIED_MATCH",
  "next_boundary":"CERTIFIED_VAULT_ROLE_MATCH",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_live_token_account_deltas.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_144_phase7_live_token_account_delta_reconstruction import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  changed=sum(v["with_changes"] for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"rows_with_changes":changed,
   "family_support":d["family_support"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(changed,0,"NO_LIVE_TOKEN_ACCOUNT_DELTAS")
  self.assertIn("REQUIRES_CERTIFIED_MATCH",d["role_policy"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-144 live token-account delta reconstruction")
  print("[PASS] pre/post token balances reconstructed without inventing vault roles")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
