from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_148_phase7_live_program_account_role_resolver.py"
TEST=ROOT/"test_usls_148_phase7_live_program_account_role_resolver.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

HYD="runtime_state/solana_opportunities/solana_scanner/phase7_live_multifamily_transaction_hydration.json"
DEL="runtime_state/solana_opportunities/solana_scanner/phase7_live_token_account_deltas.json"

PROGRAMS={
 "PUMP_FUN":"6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
 "RAYDIUM_LAUNCHLAB":"LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj",
 "RAYDIUM_V4":"675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
 "RAYDIUM_CLMM":"CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK",
 "RAYDIUM_CPMM":"CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C",
 "METEORA_DBC":"dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN",
 "METEORA_DLMM":"LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo",
 "ORCA":"whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
}

def _keys(tx):
 msg=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
 for a in msg.get("accountKeys") or []:
  out.append(a if isinstance(a,str) else a.get("pubkey"))
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 if isinstance(la,dict):out+=(la.get("writable") or [])+(la.get("readonly") or [])
 return out

def _program_accounts(tx,pid):
 keys=_keys(tx);msg=((tx or {}).get("transaction") or {}).get("message") or {}
 out=[]
 for idx,ix in enumerate(msg.get("instructions") or []):
  if not isinstance(ix,dict):continue
  prog=ix.get("programId")
  if prog is None and ix.get("programIdIndex") is not None:
   try:prog=keys[int(ix["programIdIndex"])]
   except Exception:prog=None
  if prog!=pid:continue
  accts=[]
  for a in ix.get("accounts") or []:
   if isinstance(a,str):accts.append(a)
   else:
    try:accts.append(keys[int(a)])
    except Exception:pass
  out.append({"level":"outer","instruction_index":idx,"accounts":accts})
 meta=(tx or {}).get("meta") or {}
 for g in meta.get("innerInstructions") or []:
  parent=g.get("index")
  for j,ix in enumerate(g.get("instructions") or []):
   if not isinstance(ix,dict):continue
   prog=ix.get("programId")
   if prog is None and ix.get("programIdIndex") is not None:
    try:prog=keys[int(ix["programIdIndex"])]
    except Exception:prog=None
   if prog!=pid:continue
   accts=[]
   for a in ix.get("accounts") or []:
    if isinstance(a,str):accts.append(a)
    else:
     try:accts.append(keys[int(a)])
     except Exception:pass
   out.append({"level":"inner","parent_index":parent,"instruction_index":j,"accounts":accts})
 return out

def run(root):
 root=Path(root)
 h=json.loads((root/HYD).read_text(encoding="utf-8"))
 d=json.loads((root/DEL).read_text(encoding="utf-8"))
 didx={x["trade_signature"]:x for x in d.get("rows",[])}
 rows=[];fam={}
 for x in h.get("rows",[]):
  f=x.get("family");pid=PROGRAMS.get(f);tx=x.get("transaction")
  if not pid or not isinstance(tx,dict):continue
  ixrows=_program_accounts(tx,pid)
  changed={c.get("account"):c for c in didx.get(x["trade_signature"],{}).get("token_account_changes",[]) if c.get("account")}
  matches=[]
  for ix in ixrows:
   hit=[changed[a] for a in ix["accounts"] if a in changed]
   if hit:matches.append({**ix,"changed_token_accounts":hit})
  rows.append({"family":f,"program_id":pid,"trade_signature":x["trade_signature"],
   "program_instruction_count":len(ixrows),"matched_instruction_count":len(matches),
   "matched_instructions":matches,"execution_authority":False})
  z=fam.setdefault(f,{"rows":0,"with_program_instruction":0,"with_changed_program_accounts":0})
  z["rows"]+=1;z["with_program_instruction"]+=bool(ixrows);z["with_changed_program_accounts"]+=bool(matches)
 return {"revision":"USLS_148","row_count":len(rows),"family_support":fam,"rows":rows,
  "role_semantics":"CHANGED_TOKEN_ACCOUNT_INTERSECTION_WITH_EXACT_TARGET_PROGRAM_INSTRUCTION_ACCOUNTS",
  "vault_role_claimed":False,
  "next_boundary":"STRICT_PROGRAM_LOCAL_LIQUIDITY_CANDIDATE_CERTIFICATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_live_program_account_roles.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_148_phase7_live_program_account_role_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  matched=sum(v["with_changed_program_accounts"] for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"matched_rows":matched,
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(matched,0,"NO_CHANGED_TOKEN_ACCOUNTS_INTERSECT_TARGET_PROGRAM_INSTRUCTIONS")
  self.assertFalse(d["vault_role_claimed"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-148 live program-account role resolver")
  print("[PASS] exact target-program instruction accounts intersected with physical token deltas")
  print("[PASS] no pool-vault role claimed yet")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8"); TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
