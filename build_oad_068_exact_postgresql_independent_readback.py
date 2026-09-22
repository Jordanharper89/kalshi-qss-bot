from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
BUILD_ID="OAD-068"
REVISION="OAD_068_PRODUCTION_INSTALLER_V1"
TITLE='EXACT POSTGRESQL INDEPENDENT OBSERVATION READBACK'
def locate_root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")
ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_068_exact_postgresql_independent_readback.py'
TEST=ROOT/'test_oad_068_exact_postgresql_independent_readback.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import CanonicalPersistenceQueryRequest\nfrom qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import build_existing_canonical_router\nREAD_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False\ndef exact_postgresql_readback(observation_ids,root=None):\n    ids=tuple(str(x) for x in observation_ids)\n    router=build_existing_canonical_router(Path(root or Path.cwd()).resolve())\n    backend=getattr(router,"_persistence_backend",None)\n    if backend is None or not callable(getattr(backend,"query",None)): raise RuntimeError("existing PostgreSQL backend query unavailable")\n    found=[];now=datetime.now(timezone.utc)\n    for i,oid in enumerate(ids):\n        req=CanonicalPersistenceQueryRequest.by_observation_id(query_id="query.oad068."+str(i)+"."+oid[:12],backend_id=backend.backend_id,observation_id=oid,requested_at=now,query_metadata={"read_only":True})\n        rows=tuple(backend.query(request=req))\n        if len(rows)!=1 or rows[0].observation_id!=oid: raise RuntimeError("exact readback failed: "+oid)\n        found.append(rows[0])\n    return tuple(found)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_067_independent_physical_single_writer_persistence import persist_fresh_independent_batch\nfrom qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import *\nclass T(unittest.TestCase):\n    def test_physical(self):\n        p=persist_fresh_independent_batch(timeout_seconds=120.0);rows=exact_postgresql_readback(p.observation_ids)\n        print("[PHYSICAL] committed=",p.committed,"exact_readback=",len(rows));print("[PHYSICAL] source_ids=",tuple(x.source_id for x in rows))\n        self.assertEqual(len(rows),p.committed);self.assertTrue(all(x.source_id.startswith("source.independent.") for x in rows))\nif __name__=="__main__":\n    print("="*88);print(" OAD-068 PHYSICAL CERTIFICATION TEST");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        print("[NOTE] Physical gate requires OPH-021 canonical writer RUNNING.")\n        raise SystemExit(1)\n    print("[PASS] Exact by_observation_id PostgreSQL readback verified");print("[DONE] OAD-068 CERTIFIED")\n'
def write_exact(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def main():
    print("="*88);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*88)
    print("[BOOT] Revision:",REVISION);print("[ROOT]",ROOT)
    freeze=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"
    oph=ROOT/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py"
    dep=PKG/"oad_065_independent_canonical_batch_gate.py"
    for p,label in ((freeze,"Frozen Kalshi OAD-055"),(oph,"Frozen OPH-023"),(dep,"Certified OAD-065")):
        if not p.is_file(): raise RuntimeError(label+" dependency missing")
    freeze_hash=hashlib.sha256(freeze.read_bytes()).hexdigest()
    oph_hash=hashlib.sha256(oph.read_bytes()).hexdigest()
    affected=(MODULE,TEST,INIT)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from ."+MODULE.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_exact(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        if hashlib.sha256(freeze.read_bytes()).hexdigest()!=freeze_hash: raise RuntimeError("Frozen Kalshi OAD-055 changed")
        if hashlib.sha256(oph.read_bytes()).hexdigest()!=oph_hash: raise RuntimeError("Frozen OPH-023 changed")
        print("[PASS] Certified OAD-065 dependency verified")
        print("[PASS] Frozen Kalshi OAD-055 unchanged")
        print("[PASS] Frozen OPH-023 single-writer boundary unchanged")
        print("[PASS] Wrote:",MODULE.relative_to(ROOT));print("[PASS] Wrote:",TEST.name)
        print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored");raise
if __name__=="__main__": main()
