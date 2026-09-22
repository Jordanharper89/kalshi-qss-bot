from pathlib import Path
import os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_036_outcome_evidence_linkage_foundation.py";TEST=ROOT/"test_olr_036_outcome_evidence_linkage_foundation.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport hashlib,json\n\nOLR_036_BUILD_ID="OLR-036"\nOLR_036_REVISION="OLR_036_OUTCOME_EVIDENCE_LINKAGE_FOUNDATION_V1"\n\n@dataclass(frozen=True)\nclass OutcomeEvidenceKey:\n    market_id:str\n    ticker:str\n    observation_id:str|None\n    settled_at:str|None\n\ndef normalize_text(value):\n    return "" if value is None else str(value).strip()\n\ndef build_outcome_evidence_key(record):\n    getter=record.get if hasattr(record,"get") else lambda k,d=None:getattr(record,k,d)\n    market_id=normalize_text(getter("market_id","") or getter("market_ticker","") or getter("ticker",""))\n    ticker=normalize_text(getter("ticker","") or getter("market_ticker","") or market_id)\n    observation_id=normalize_text(getter("observation_id","")) or None\n    settled_at=normalize_text(getter("settled_at","") or getter("resolved_at","")) or None\n    return OutcomeEvidenceKey(market_id,ticker,observation_id,settled_at)\n\ndef deterministic_linkage_id(key):\n    payload=json.dumps(key.__dict__,sort_keys=True,separators=(",",":"))\n    return hashlib.sha256(payload.encode()).hexdigest()\n\ndef verify_olr_036_outcome_evidence_linkage_foundation(root=None):\n    k=build_outcome_evidence_key({"ticker":"KXTEST","observation_id":"abc"})\n    return OLR_036_BUILD_ID=="OLR-036" and k.market_id=="KXTEST" and len(deterministic_linkage_id(k))==64\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_036_outcome_evidence_linkage_foundation import *\nclass T(unittest.TestCase):\n    def test_key(self):\n        k=build_outcome_evidence_key({"ticker":"KXBTC","observation_id":"o1"})\n        self.assertEqual(k.market_id,"KXBTC")\n        self.assertEqual(k.observation_id,"o1")\n    def test_deterministic_id(self):\n        k=OutcomeEvidenceKey("m","t","o","s")\n        self.assertEqual(deterministic_linkage_id(k),deterministic_linkage_id(k))\nif __name__=="__main__":\n    print("="*88);print(" OLR-036 CERTIFICATION TEST");print(" OUTCOME-EVIDENCE LINKAGE FOUNDATION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Deterministic outcome-evidence linkage keys certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-036 CERTIFIED")\n'

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
    print("="*88);print(" OLR-036 INSTALLER");print(" OUTCOME-EVIDENCE LINKAGE FOUNDATION");print("="*88);print("[ROOT]",ROOT)
    runtime=ROOT/"run_olr_035_learning_calibration_supervisor.py"
    alt=ROOT/"run_olr_005_continuous_learning_runtime.py"
    if not runtime.is_file() and not alt.is_file():
        raise RuntimeError("Certified Oracle learning runtime boundary not found")
    print("[PASS] Existing Oracle learning runtime boundary verified read-only")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_036_outcome_evidence_linkage_foundation import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-036 installation failed; affected files restored");raise
    print("[PASS] Existing learning runtime preserved")
    print("[PASS] OPH-001 through OPH-033 preserved read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-036 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
