from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-306'
TITLE='SOLANA LAUNCH / SECURITY SINGLE-WRITER PERSISTENCE'
EXPECTED='build_oad_306_solana_launch_security_single_writer_persistence_CERTIFIED_REBUILD.py'
MODULE='oad_306_solana_launch_security_single_writer_persistence.py'
TEST='test_oad_306_solana_launch_security_single_writer_persistence.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_305_solana_launch_security_profile.py', ('def build_current_solana_launch_security_profile',)), ('qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py', ('def canonicalize_expansion_observation', 'PRODUCER=', 'PRIORITY=')), ('qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py', ('def exact_postgresql_readback', 'def _query_one', 'def _backend')), ('qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py', ('def submit_observation_batch', 'def await_request'))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nimport hashlib,json\nfrom .oad_305_solana_launch_security_profile import build_current_solana_launch_security_profile\nfrom .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation\nfrom .oad_261_universal_expansion_source_single_writer_postgresql_persistence import PRODUCER,PRIORITY,canonicalize_expansion_observation\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\nBATCH_ID="oad306.solana.launch-security"\n@dataclass(frozen=True,slots=True)\nclass LaunchSecurityPersistenceResult:\n    token_address:str; raw_observations:int; canonical_observations:int; already_present:int; committed_new:int; exact_readback:int; observation_ids:tuple; execution_authority:bool=False\ndef persist_current_solana_launch_security(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=30.0):\n    root=Path(root or Path.cwd()).resolve(); x=build_current_solana_launch_security_profile(acquisition_timeout_seconds)\n    raw=(\n      build_independent_crypto_observation(source_id="source.onchain.solana.launch_security."+x.token_address,provider="solana_mainnet_rpc",source_class="launch_security_chain",subject=x.token_address,observation_type="solana_launch_security_chain_evidence",payload=x.chain_mint_payload),\n      build_independent_crypto_observation(source_id="source.gmgn.solana.launch_security."+x.token_address,provider="gmgn",source_class="launch_security_provider_claim",subject=x.token_address,observation_type="solana_launch_security_provider_claim",payload={"security":x.gmgn_security,"creator_deployer_claims":[{"field_path":c.field_path,"value":c.value,"provider":c.provider,"oracle_verified":c.oracle_verified} for c in x.creator_deployer_claims],"provider_claim_only":True}),\n    )\n    canonical=tuple(canonicalize_expansion_observation(y,BATCH_ID) for y in raw); backend=_backend(root); missing=[]; existing=0\n    for i,y in enumerate(canonical):\n        if _query_one(backend,y.observation_id,i) is None: missing.append(y)\n        else: existing+=1\n    committed=0\n    if missing:\n        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)\n        ev=tuple(await_request(str(sub.request_id),root,float(timeout_seconds))); acc=tuple(e for e in ev if getattr(e,"accepted",False) is True)\n        if len(acc)!=len(missing): raise RuntimeError("launch/security single-writer commit mismatch")\n        committed=len(acc)\n    ids=tuple(y.observation_id for y in canonical); rows=tuple(exact_postgresql_readback(ids,root))\n    if len(rows)!=2: raise RuntimeError("launch/security exact PostgreSQL readback mismatch")\n    return LaunchSecurityPersistenceResult(x.token_address,2,2,existing,committed,2,ids,False)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_306_solana_launch_security_single_writer_persistence import *\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=persist_current_solana_launch_security()\n        print("[PHYSICAL] token=",r.token_address); print("[PHYSICAL] already_present=",r.already_present); print("[PHYSICAL] committed_new=",r.committed_new); print("[PHYSICAL] exact_readback=",r.exact_readback); print("[PHYSICAL] observation_ids=",r.observation_ids)\n        self.assertEqual(r.raw_observations,2); self.assertEqual(r.canonical_observations,2); self.assertEqual(r.already_present+r.committed_new,2); self.assertEqual(r.exact_readback,2); self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-306 launch/security evidence persisted through universal single writer")\n    print("[PASS] exact 2/2 observation-ID PostgreSQL readback certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def checked_write(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+".tmp")
    q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer filename identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" — CERTIFIED REBUILD INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPENDENCIES:
        p=r/rel
        if not p.is_file(): raise RuntimeError("dependency missing: "+rel)
        s=p.read_text(encoding="utf-8"); ast.parse(s,filename=str(p))
        for mark in marks:
            if mark not in s: raise RuntimeError("exact dependency marker missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"):
        p=r/rel
        if not p.is_file(): raise RuntimeError("frozen boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        checked_write(m,MODULE_SOURCE); checked_write(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines: lines.append(exp)
        checked_write(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("frozen boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" CERTIFIED REBUILD INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
