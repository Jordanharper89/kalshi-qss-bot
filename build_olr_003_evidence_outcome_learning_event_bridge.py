from __future__ import annotations
import importlib, os, subprocess, sys
from pathlib import Path
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_learning_runtime"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OLR-003'
TITLE='EVIDENCE + OUTCOME LEARNING EVENT BRIDGE'
REVISION='OLR_003_PRODUCTION_V1'
MODULE=PACKAGE/'olr_003_learning_event_bridge.py'
TEST=ROOT/'test_olr_003_evidence_outcome_learning_event_bridge.py'
EXPORTS=('OLR_003_BUILD_ID', 'OLR_003_REVISION', 'find_market_evidence', 'build_learning_runtime_input', 'verify_olr_003_evidence_outcome_learning_event_bridge')
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom hashlib import sha256\nimport json\nfrom qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation\nfrom qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event\nfrom qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input\nfrom qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import read_latest_canonical_observations\nfrom qseries_v2.oracle_continuous_reasoning.ocr_006_market_identity_recovery import recover_market_identity\nOLR_003_BUILD_ID="OLR-003"\nOLR_003_REVISION="OLR_003_EVIDENCE_OUTCOME_LEARNING_EVENT_BRIDGE_V1"\n\ndef find_market_evidence(root,ticker,scan_limit=500):\n    rows=read_latest_canonical_observations(Path(root),limit=min(max(1,int(scan_limit)),500)).rows\n    for row in rows:\n        ident=recover_market_identity(row)\n        if ident.recovered and ident.market_ticker==ticker:\n            h=str(row.get("content_hash") or row.get("observation_id") or "")\n            if len(h)!=64:\n                h=sha256(json.dumps(row,sort_keys=True,default=str).encode()).hexdigest()\n            return row,h\n    return None,None\n\ndef build_learning_runtime_input(sequence,outcome,evidence_hash):\n    value=True if outcome.result=="yes" else False if outcome.result=="no" else outcome.raw.get("settlement_value")\n    oo=build_outcome_observation(\n        outcome.ticker,"settlement",value,outcome.settlement_ts,\n        "kalshi:"+outcome.ticker,outcome.source_hash\n    )\n    lineage=sha256((evidence_hash+outcome.source_hash).encode()).hexdigest()\n    event=assemble_learning_event(outcome.ticker,evidence_hash,lineage,oo)\n    return build_runtime_input(\n        int(sequence),"learning_event",event.event_id,event.event_hash,\n        {"subject_id":event.subject_id,"evidence_hash":event.evidence_hash,\n         "outcome_hash":event.outcome_hash,"lineage_hash":event.lineage_hash,\n         "outcome_type":event.outcome_type}\n    )\n\ndef verify_olr_003_evidence_outcome_learning_event_bridge():\n    from .olr_002_settled_outcome_read_model import normalize_settled_market\n    o=normalize_settled_market({"ticker":"KXTEST","result":"yes","settlement_ts":"t"})\n    x=build_learning_runtime_input(1,o,"a"*64)\n    return x.source_kind=="learning_event" and len(x.source_hash)==64\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_003_learning_event_bridge import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_003_evidence_outcome_learning_event_bridge())\nif __name__=="__main__":\n    print("="*72);print(" OLR-003 CERTIFICATION TEST");print(" EVIDENCE + OUTCOME LEARNING EVENT BRIDGE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Frozen OCL evidence/outcome event bridge certified")\n    print("[DONE] OLR-003 CERTIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_002_settled_outcome_read_model')
        if getattr(m,'verify_olr_002_kalshi_settled_outcome_read_model')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified frozen upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)

        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_learning_runtime."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
        run_test(TEST)

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():p.unlink()
            else:p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
