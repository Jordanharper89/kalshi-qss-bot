from __future__ import annotations
import os,sys,subprocess
from pathlib import Path
REVISION="OAD_238_CRYPTO_PROSPECTIVE_LEARNING_STATE_REFRESH_V1"
EXPECTED="build_oad_238_crypto_prospective_learning_state_refresh.py"
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_235_prospective_calibration_source_reliability_materialization import materialize_prospective_calibration_and_reliability\nfrom .oad_236_prospective_adaptive_ocl029_readmission import build_prospective_adaptive_ocl029_readmission\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass ProspectiveLearningStateRefresh:\n    calibration_state_hash:object;source_reliability_state_hash:object;adaptive_weight_state_hash:object\n    admission_state:str;handoff_verified:bool;execution_authority:bool=False\ndef refresh_prospective_learning_states(root=None):\n    c=materialize_prospective_calibration_and_reliability(root)\n    a=build_prospective_adaptive_ocl029_readmission(root)\n    return ProspectiveLearningStateRefresh(\n        getattr(c,"calibration_state_hash",None),getattr(c,"source_reliability_state_hash",None),\n        getattr(a,"adaptive_weight_state_hash",None),str(getattr(a,"admission_state","HOLD")),\n        bool(getattr(a,"handoff_verified",False)),False)\n'
TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_238_crypto_prospective_learning_state_refresh as m\nclass T(unittest.TestCase):\n def test_hold_is_truthful(self):\n  with patch.object(m,"materialize_prospective_calibration_and_reliability",return_value=SimpleNamespace(calibration_state_hash=None,source_reliability_state_hash=None)), \\\n       patch.object(m,"build_prospective_adaptive_ocl029_readmission",return_value=SimpleNamespace(adaptive_weight_state_hash=None,admission_state="HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED",handoff_verified=False)):\n   x=m.refresh_prospective_learning_states()\n  print("[STATE]",x.admission_state);self.assertFalse(x.handoff_verified);self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] OAD-238 truthful prospective state refresh certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,b/"kalshi-qss-bot",*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write_atomic(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);compile(s,str(p),"exec")
    t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def run(r,p,*args):
    q=subprocess.run([sys.executable,str(p),*args],cwd=str(r))
    if q.returncode: raise RuntimeError("Certification command failed: "+p.name)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("Installer identity mismatch")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/"oad_238_crypto_prospective_learning_state_refresh.py";t=r/"test_oad_238_crypto_prospective_learning_state_refresh.py"
    print("="*124);print(" OAD-238 CRYPTO PROSPECTIVE LEARNING STATE REFRESH");print("="*124);print("[BOOT]",REVISION);print("[ROOT]",r)
    for d in ['qseries_v2/oracle_adapters/independent/oad_235_prospective_calibration_source_reliability_materialization.py', 'qseries_v2/oracle_adapters/independent/oad_236_prospective_adaptive_ocl029_readmission.py']:
        p=r/d
        if not p.is_file(): raise RuntimeError("Required certified dependency missing: "+str(p))
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t)}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST);run(r,t)
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-238 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OAD-238 rolled back");raise
if __name__=="__main__":main()
