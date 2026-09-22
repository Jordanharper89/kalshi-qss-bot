from __future__ import annotations
import ast,os,textwrap,hashlib
from pathlib import Path
EXPECTED='build_oad_289_gmgn_clean_single_writer_persistence.py'
MODULE='oad_289_gmgn_clean_single_writer_persistence.py'
TEST='test_oad_289_gmgn_clean_single_writer_persistence.py'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport hashlib,json\nfrom .oad_288_gmgn_clean_acquisition_boundary import acquire_current_gmgn_token\nfrom .oad_261_universal_expansion_source_single_writer_postgresql_persistence import PRODUCER,PRIORITY,canonicalize_expansion_observation\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False; BATCH_ID="oad289.gmgn.clean"\n@dataclass(frozen=True,slots=True)\nclass Raw:\n source_id:str;provenance_hash:str;observed_at:object;observation_type:str;source_class:str;provider:str;subject:str;payload:dict;execution_authority:bool=False\n@dataclass(frozen=True,slots=True)\nclass Result:\n token_address:str;raw_observations:int;canonical_observations:int;already_present:int;committed_new:int;exact_readback:int;observation_ids:tuple;execution_authority:bool=False\ndef _h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\ndef persist_current_gmgn(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=30.0):\n root=Path(root or Path.cwd()).resolve();g=acquire_current_gmgn_token(acquisition_timeout_seconds);raw=[]\n for s in ("info","security","pool"):\n  sid=f"source.gmgn.solana.token.{g.token_address}.{s}";payload=g.payload[s];raw.append(Raw(sid,_h({"source_id":sid,"observed_at":g.observed_at,"payload":payload}),g.observed_at,"gmgn_solana_token_"+s,"token_intelligence","gmgn",g.token_address,dict(payload),False))\n can=tuple(canonicalize_expansion_observation(x,BATCH_ID) for x in raw);backend=_backend(root);missing=[];existing=0\n for i,x in enumerate(can):\n  if _query_one(backend,x.observation_id,i) is None:missing.append(x)\n  else:existing+=1\n committed=0\n if missing:\n  sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root);events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)));accepted=tuple(e for e in events if getattr(e,"accepted",False) is True)\n  if len(accepted)!=len(missing):raise RuntimeError("single-writer commit mismatch")\n  committed=len(accepted)\n ids=tuple(x.observation_id for x in can);rows=tuple(exact_postgresql_readback(ids,root))\n if len(rows)!=3:raise RuntimeError("exact readback mismatch")\n return Result(g.token_address,3,3,existing,committed,3,ids,False)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_289_gmgn_clean_single_writer_persistence import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  r=persist_current_gmgn();print("[PHYSICAL] token=",r.token_address);print("[PHYSICAL] already_present=",r.already_present);print("[PHYSICAL] committed_new=",r.committed_new);print("[PHYSICAL] exact_readback=",r.exact_readback);self.assertEqual(r.already_present+r.committed_new,3);self.assertEqual(r.exact_readback,3)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));raise SystemExit(0 if r.wasSuccessful() else 1)\n'
def root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for p in (b,*b.parents):
   if (p/"qseries_v2").is_dir(): return p
 raise RuntimeError("Q Series repository root not found")
def write(p,s):
 s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
 if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
 r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
 for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"):
  if not (r/rel).is_file(): raise RuntimeError("frozen boundary missing: "+rel)
 write(pkg/MODULE,MODULE_SOURCE); write(r/TEST,TEST_SOURCE)
 
 print("[PASS] installed:",MODULE); print("[PASS] frozen OPH-023/Kalshi OAD-055 preserved"); print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE"); print("[DONE] installation complete")
if __name__=="__main__": main()
