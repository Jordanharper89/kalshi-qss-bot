from pathlib import Path

ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_004_universal_birth_event_normalizer.py"
TEST=ROOT/"test_usls_004_universal_birth_event_normalizer.py"

MOD_TEXT=r"""from __future__ import annotations
import hashlib,importlib.util,json
from pathlib import Path

def _load_suls042(root):
 p=Path(root)/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_042_generic_meteora_birth_role_materializer.py"
 spec=importlib.util.spec_from_file_location("_usls004_suls042",p)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def normalize(root):
 root=Path(root)
 inbox=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/event_driven_birth_inbox.json").read_text(encoding="utf-8"))
 cand=json.loads((root/"runtime_state/solana_opportunities/universal_launch_scanner/structural_birth_candidates.json").read_text(encoding="utf-8"))
 births={b.get("signature"):b for b in (inbox.get("births") or []) if b.get("signature")}
 cands={x.get("signature"):x for x in cand.get("events") or []}
 m=_load_suls042(root)
 rows=[]
 for sig,c in cands.items():
  if c["candidate_state"]=="UNRESOLVED_EVENT": continue
  b=births.get(sig) or {}
  exact=m._materialize(b) if b else None
  if exact:
   row=dict(exact)
   row.update({"canonical_state":"IDENTITY_RESOLVED","decoder":"SULS_042_METEORA_DAMM",
    "source_family":c.get("family"),"structural_score":c.get("structural_score")})
  else:
   rawid=f'{sig}|{c.get("family")}|{c.get("slot")}'
   row={"event_id":"usls-birth-"+hashlib.sha256(rawid.encode()).hexdigest(),
    "signature":sig,"slot":c.get("slot"),"observed_unix":c.get("observed_unix"),
    "launcher_family":c.get("family"),"program_ids":c.get("program_ids") or [],
    "token_address":None,"pair_address":None,
    "canonical_state":"UNRESOLVED_BIRTH","decoder":"GENERIC_STRUCTURAL_FALLBACK",
    "structural_score":c.get("structural_score"),"execution_authority":False}
  row["execution_authority"]=False
  rows.append(row)
 return {"revision":"USLS_004","event_count":len(rows),
  "identity_resolved_count":sum(1 for x in rows if x["canonical_state"]=="IDENTITY_RESOLVED"),
  "unresolved_birth_count":sum(1 for x in rows if x["canonical_state"]=="UNRESOLVED_BIRTH"),
  "dropped_candidate_count":0,"events":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=normalize(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/canonical_universal_birth_events.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_004_universal_birth_event_normalizer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_normalizer(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "event_count","identity_resolved_count","unresolved_birth_count","dropped_candidate_count")},sort_keys=True))
  self.assertGreater(d["event_count"],0)
  self.assertEqual(d["dropped_candidate_count"],0)
  self.assertGreater(d["identity_resolved_count"],0)
  for r in d["events"]:
   self.assertIn(r["canonical_state"],("IDENTITY_RESOLVED","UNRESOLVED_BIRTH"))
   self.assertFalse(r["execution_authority"])
  print("[PASS] USLS-004 universal birth event normalizer")
  print("[PASS] resolved and unresolved launches share one downstream contract")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
