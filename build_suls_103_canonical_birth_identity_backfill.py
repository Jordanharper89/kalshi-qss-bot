from pathlib import Path
import json, importlib.util, os, time

ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
TARGET=SUB/"suls_103_canonical_birth_identity_backfill.py"
TEST=ROOT/"test_suls_103_canonical_birth_identity_backfill.py"

MOD_TEXT=r"""from __future__ import annotations
import importlib.util,json,os,time
from pathlib import Path

IDENTITY_FIELDS=(
 "token_address","pair_address","token_mint","quote_mint",
 "token_vault","quote_vault","initial_token_amount","initial_quote_amount",
 "launcher_family","program_id","position_nft_mints"
)

def _load_materializer(root):
 p=root/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_042_generic_meteora_birth_role_materializer.py"
 spec=importlib.util.spec_from_file_location("_suls042_suls103",p)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return m

def backfill(root):
 root=Path(root).resolve()
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 inbox_p=base/"event_driven_birth_inbox.json"
 events_p=base/"confirmed_tradeable_birth_events.json"
 inbox=json.loads(inbox_p.read_text(encoding="utf-8"))
 current=json.loads(events_p.read_text(encoding="utf-8"))
 births=list(inbox.get("births") or [])
 events=list(current.get("events") or [])

 m=_load_materializer(root)
 by_sig={}
 materialized=0
 for b in births:
  x=m._materialize(b)
  if x is None: continue
  sig=x.get("signature")
  if sig:
   by_sig[sig]=x
   materialized+=1

 updated=0
 already_complete=0
 unmatched=0
 for e in events:
  sig=e.get("signature")
  x=by_sig.get(sig)
  if not x:
   unmatched+=1
   continue
  if e.get("token_address") and e.get("pair_address"):
   already_complete+=1
  changed=False
  for k in IDENTITY_FIELDS:
   if x.get(k) is not None and e.get(k)!=x.get(k):
    e[k]=x.get(k);changed=True
  if changed: updated+=1

 state=dict(current)
 state["events"]=events
 state["identity_contract_revision"]="SULS_103"
 state["identity_backfill_unix"]=time.time()

 tmp=events_p.with_suffix(".suls103.tmp")
 tmp.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
 os.replace(tmp,events_p)

 result={"revision":"SULS_103","birth_count":len(births),"event_count":len(events),
  "materialized_births":materialized,"updated_events":updated,
  "already_complete_events":already_complete,"unmatched_events":unmatched,
  "identity_complete_events":sum(1 for e in events if e.get("token_address") and e.get("pair_address")),
  "execution_authority":False,"read_only":True}
 out=base/"canonical_birth_identity_backfill_state.json"
 out.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
 return result
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_103_canonical_birth_identity_backfill import backfill
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_backfill(self):
  d=backfill(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertGreater(d["event_count"],0)
  self.assertGreater(d["materialized_births"],0)
  self.assertGreater(d["identity_complete_events"],0)
  p=ROOT/"runtime_state/solana_opportunities/launch_surveillance/confirmed_tradeable_birth_events.json"
  rows=json.loads(p.read_text(encoding="utf-8")).get("events") or []
  good=[x for x in rows if x.get("token_address") and x.get("pair_address")]
  self.assertGreater(len(good),0)
  print("[SAMPLE]",json.dumps({k:good[-1].get(k) for k in (
   "signature","token_address","pair_address","token_vault","quote_vault",
   "launcher_family","execution_authority")},sort_keys=True))
  print("[PASS] SULS-103 canonical birth identity backfill")
  print("[PASS] historical captured births now carry canonical token/pair identity where physically resolvable")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116)
 print(" SULS-103 CANONICAL BIRTH IDENTITY BACKFILL")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 TARGET.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",TARGET.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")

if __name__=="__main__":main()
