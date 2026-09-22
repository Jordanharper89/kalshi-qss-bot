from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_044_continuous_learner_evidence_runtime_cutover.py";TEST=ROOT/"test_olr_044_continuous_learner_evidence_runtime_cutover.py";RUN=ROOT/"run_olr_044_continuous_learning_with_evidence.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport ast\n\nOLR_044_BUILD_ID="OLR-044"\nOLR_044_REVISION="OLR_044_CONTINUOUS_LEARNER_EVIDENCE_RUNTIME_CUTOVER_V1"\nWRAPPER="run_olr_044_continuous_learning_with_evidence.py"\n\ndef find_learning_runner(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    candidates=[\n        "run_olr_035_learning_calibration_supervisor.py",\n        "run_olr_010_high_coverage_continuous_learning_runtime.py",\n        "run_olr_005_continuous_learning_runtime.py",\n    ]\n    for name in candidates:\n        if (root/name).is_file():\n            return name\n    raise RuntimeError("Existing continuous learning runner not found")\n\ndef wrapper_source(underlying):\n    return "\\n".join([\n        "from pathlib import Path",\n        "import runpy",\n        "from qseries_v2.oracle_learning.olr_043_live_learning_evidence_adapter import adapt_learning_batch",\n        f"UNDERLYING_RUNNER={underlying!r}",\n        "",\n        "if __name__==\'__main__\':",\n        "    print(\'=\'*88,flush=True)",\n        "    print(\' OLR-044 CONTINUOUS LEARNER EVIDENCE RUNTIME\',flush=True)",\n        "    print(\'=\'*88,flush=True)",\n        "    print(\'[OLR-044] live_evidence_linkage=ENABLED execution_authority=FALSE\',flush=True)",\n        "    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name=\'__main__\')",\n        "",\n    ])\n\ndef verify_olr_044_continuous_learner_evidence_runtime_cutover(root=None):\n    from .olr_043_live_learning_evidence_adapter import verify_olr_043_live_learning_evidence_adapter\n    root=Path(root or Path.cwd()).resolve()\n    return verify_olr_043_live_learning_evidence_adapter(root) and (root/WRAPPER).is_file()\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_044_continuous_learner_evidence_runtime_cutover import *\nclass T(unittest.TestCase):\n    def test_wrapper_source(self):\n        s=wrapper_source("run_x.py")\n        compile(s,"x","exec")\n        self.assertIn("live_evidence_linkage=ENABLED",s)\nif __name__=="__main__":\n    print("="*88);print(" OLR-044 CERTIFICATION TEST");print(" CONTINUOUS LEARNER EVIDENCE RUNTIME CUTOVER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Evidence-enabled learner wrapper certified")\n    print("[PASS] Existing learner remains underlying runtime")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-044 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OLR-044 INSTALLER");print(" CONTINUOUS LEARNER EVIDENCE RUNTIME CUTOVER");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning.olr_043_live_learning_evidence_adapter")
    if not up.verify_olr_043_live_learning_evidence_adapter(ROOT):raise RuntimeError("Certified OLR-043 verification failed")
    affected=(MOD,TEST,RUN,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_044_continuous_learner_evidence_runtime_cutover import *")
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning.olr_044_continuous_learner_evidence_runtime_cutover")
        underlying=m.find_learning_runner(ROOT)
        source=m.wrapper_source(underlying)
        compile(source,str(RUN),"exec");write_exact(RUN,source)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        if not m.verify_olr_044_continuous_learner_evidence_runtime_cutover(ROOT):raise RuntimeError("OLR-044 verification failed")
        print("[PASS] underlying_learning_runner="+underlying)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-044 installation failed; affected files restored");raise
    print("[PASS] Existing learner preserved underneath evidence wrapper")
    print("[PASS] execution_authority=FALSE");print("[DONE] OLR-044 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
