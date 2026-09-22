from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
BUILD_ID="OAD-067"
REVISION="OAD_067_PRODUCTION_INSTALLER_V1"
TITLE='PHYSICAL INDEPENDENT SINGLE-WRITER POSTGRESQL PERSISTENCE'
def locate_root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")
ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_067_independent_physical_single_writer_persistence.py'
TEST=ROOT/'test_oad_067_independent_physical_single_writer_persistence.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import acquire_independent_production_bundle\nfrom qseries_v2.oracle_adapters.independent.oad_065_independent_canonical_batch_gate import build_independent_canonical_batch\nfrom qseries_v2.oracle_adapters.independent.oad_066_independent_single_writer_ingress_binding import submit_independent_canonical_batch,await_independent_commit\nREAD_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False\n@dataclass(frozen=True,slots=True)\nclass IndependentPersistenceResult:\n    requested:int;committed:int;observation_ids:tuple;request_id:str;execution_authority:bool=False\ndef persist_fresh_independent_batch(root=None,per_source_limit=2,timeout_seconds=120.0):\n    raw=acquire_independent_production_bundle(per_source_limit)\n    batch=build_independent_canonical_batch(raw,"oad067.physical")\n    if not batch.ready_for_existing_persistence_router: raise RuntimeError("OAD-065 batch not ready")\n    sub=submit_independent_canonical_batch(batch.canonical_observations,root)\n    evidence=await_independent_commit(sub.request_id,root,timeout_seconds)\n    accepted=tuple(x for x in evidence if getattr(x,"accepted",False) is True)\n    if len(accepted)!=len(batch.canonical_observations): raise RuntimeError("single-writer commit count mismatch")\n    return IndependentPersistenceResult(len(batch.canonical_observations),len(accepted),tuple(x.observation_id for x in batch.canonical_observations),str(sub.request_id),False)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_067_independent_physical_single_writer_persistence import *\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=persist_fresh_independent_batch(timeout_seconds=120.0)\n        print("[PHYSICAL] requested=",r.requested);print("[PHYSICAL] committed=",r.committed);print("[PHYSICAL] request_id=",r.request_id)\n        print("[PHYSICAL] observation_ids=",r.observation_ids)\n        self.assertGreater(r.requested,0);self.assertEqual(r.requested,r.committed)\nif __name__=="__main__":\n    print("="*88);print(" OAD-067 PHYSICAL CERTIFICATION TEST");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        print("[NOTE] Physical gate requires OPH-021 canonical writer RUNNING, normally via Oracle Live Runtime.")\n        raise SystemExit(1)\n    print("[PASS] Real independent observations committed through OPH single-writer path");print("[DONE] OAD-067 CERTIFIED")\n'
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
