from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_138_phase7_missing_venue_transaction_lineage_census.py"
TEST=ROOT/"test_usls_138_phase7_missing_venue_transaction_lineage_census.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

MISSING=("PUMP_FUN","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM","RAYDIUM_CPMM",
 "METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM",
 "ORCA","MOONIT","BOOP_FUN","HEAVEN")
SRC="runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"

def _walk(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_walk(v,out)
 elif isinstance(x,list):
  for v in x:_walk(v,out)

def _sig(o):return o.get("trade_signature") or o.get("signature")

def run(root):
 root=Path(root)
 econ=json.loads((root/SRC).read_text(encoding="utf-8"))
 cache={};fam={f:{"rows":0,"raw_tx":0,"account_roles":0,"vault_fields":0,
                  "block_time":0,"observed_time":0} for f in MISSING}
 examples=[]
 for x in econ.get("rows",[]):
  f=x.get("family")
  if f not in fam:continue
  rel=x.get("source_artifact");sig=x.get("trade_signature")
  if not rel or not sig:continue
  fam[f]["rows"]+=1
  if rel not in cache:
   try:
    raw=json.loads((root/rel).read_text(encoding="utf-8"))
    objs=[];_walk(raw,objs);idx={}
    for o in objs:
     if isinstance(o,dict) and _sig(o):idx.setdefault(str(_sig(o)),[]).append(o)
    cache[rel]=idx
   except Exception:cache[rel]={}
  matches=cache[rel].get(str(sig),[])
  keys=set()
  rawtx=False;block=False;obs=False
  for o in matches:
   keys.update(o.keys())
   rawtx |= isinstance(o.get("transaction"),dict) or isinstance(o.get("raw_transaction"),dict)
   block |= o.get("block_time") is not None or o.get("blockTime") is not None
   obs |= any(o.get(k) is not None for k in ("observed_unix","trade_observed_unix","received_unix"))
  vault=[k for k in keys if "vault" in k.lower() or "reserve" in k.lower()]
  roles=[k for k in keys if any(w in k.lower() for w in ("account","pool","market","curve"))]
  fam[f]["raw_tx"]+=rawtx;fam[f]["block_time"]+=block;fam[f]["observed_time"]+=obs
  fam[f]["vault_fields"]+=bool(vault);fam[f]["account_roles"]+=bool(roles)
  if len(examples)<40 and (rawtx or vault or roles):
   examples.append({"family":f,"signature":sig,"source_artifact":rel,
                    "raw_tx":rawtx,"vault_fields":vault[:20],"role_fields":roles[:20]})
 return {"revision":"USLS_138","family_lineage":fam,"examples":examples,
  "families_with_raw_tx":sum(v["raw_tx"]>0 for v in fam.values()),
  "families_with_vault_or_role_evidence":sum((v["vault_fields"]>0 or v["account_roles"]>0) for v in fam.values()),
  "next_boundary":"HYDRATE_MISSING_VENUE_TRANSACTIONS_AND_POOL_STATE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_missing_venue_transaction_lineage_census.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_138_phase7_missing_venue_transaction_lineage_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"families_with_raw_tx":d["families_with_raw_tx"],
   "families_with_vault_or_role_evidence":d["families_with_vault_or_role_evidence"],
   "family_lineage":d["family_lineage"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertEqual(len(d["family_lineage"]),13)
  self.assertGreater(d["families_with_vault_or_role_evidence"],0,
                     "NO_POOL_OR_ACCOUNT_ROLE_LINEAGE_FOUND")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-138 missing-venue transaction lineage census")
  print("[PASS] pool/account/vault lineage measured before friction reconstruction")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
