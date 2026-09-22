from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
BUILD_ID="OAD-066"
REVISION="OAD_066_PRODUCTION_INSTALLER_V1"
TITLE='INDEPENDENT TO OPH UNIVERSAL SINGLE-WRITER INGRESS BINDING'
def locate_root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")
ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_066_independent_single_writer_ingress_binding.py'
TEST=ROOT/'test_oad_066_independent_single_writer_ingress_binding.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nfrom qseries_v2.oracle_production_hardening.oph_020_universal_postgresql_producer_admission import verify_oph_020_universal_postgresql_producer_admission\nfrom qseries_v2.oracle_production_hardening.oph_021_exclusive_postgresql_canonical_writer import verify_oph_021_exclusive_postgresql_canonical_writer\nREAD_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False\nPRODUCER="oracle.independent_research";PRIORITY=20\ndef submit_independent_canonical_batch(observations,root=None):\n    items=tuple(observations)\n    if not items: raise ValueError("non-empty canonical observation batch required")\n    if any(getattr(x,"execution_allowed",None) is not False for x in items): raise ValueError("execution-enabled observation rejected")\n    return submit_observation_batch(PRODUCER,PRIORITY,items,Path(root or Path.cwd()).resolve())\ndef await_independent_commit(request_id,root=None,timeout_seconds=120.0):\n    return tuple(await_request(str(request_id),Path(root or Path.cwd()).resolve(),float(timeout_seconds)))\ndef verify_oad_066_independent_single_writer_ingress_binding():\n    return verify_oph_020_universal_postgresql_producer_admission() is True and verify_oph_021_exclusive_postgresql_canonical_writer() is True and not EXECUTION_AUTHORITY and not PROBABILITY_ENABLED\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_066_independent_single_writer_ingress_binding import *\nclass T(unittest.TestCase):\n    def test_contract(self):\n        self.assertTrue(verify_oad_066_independent_single_writer_ingress_binding())\n        self.assertEqual(PRODUCER,"oracle.independent_research")\n        self.assertEqual(PRIORITY,20)\nif __name__=="__main__":\n    print("="*88);print(" OAD-066 CERTIFICATION TEST");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Independent producer bound to OPH universal PostgreSQL queue")\n    print("[PASS] OPH-021 remains exclusive canonical writer")\n    print("[DONE] OAD-066 CERTIFIED")\n'
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
