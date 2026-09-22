from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_026_full_page_coverage_admission.py"
TEST=ROOT/"test_opc_026_full_page_coverage_admission.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nOPC_026_BUILD_ID="OPC-026"\nOPC_026_REVISION="OPC_026_FULL_PAGE_COVERAGE_ADMISSION_V1"\n\n@dataclass(frozen=True)\nclass FullPageCoverageAdmission:\n    page_markets:int\n    already_covered:int\n    missing_markets:int\n    admitted_tickers:tuple\n    full_page_mode:bool=True\n    execution_authority:bool=False\n\ndef admit_full_page_coverage(markets,recent_tickers):\n    recent={str(x) for x in recent_tickers}\n    ordered=[]\n    covered=0\n    seen=set()\n\n    for row in markets:\n        if not isinstance(row,dict):\n            continue\n        ticker=str(row.get("ticker") or "")\n        if not ticker or ticker in seen:\n            continue\n        seen.add(ticker)\n        if ticker in recent:\n            covered+=1\n        else:\n            ordered.append(ticker)\n\n    return FullPageCoverageAdmission(\n        page_markets=len(seen),\n        already_covered=covered,\n        missing_markets=len(ordered),\n        admitted_tickers=tuple(ordered),\n        full_page_mode=True,\n        execution_authority=False,\n    )\n\ndef verify_opc_026_full_page_coverage_admission():\n    rows=tuple({"ticker":f"KX{i:04d}"} for i in range(1000))\n    recent={f"KX{i:04d}" for i in range(125)}\n    x=admit_full_page_coverage(rows,recent)\n    return (\n        x.page_markets==1000\n        and x.already_covered==125\n        and x.missing_markets==875\n        and len(x.admitted_tickers)==875\n        and x.full_page_mode\n        and not x.execution_authority\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_026_full_page_coverage_admission import verify_opc_026_full_page_coverage_admission\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_026_full_page_coverage_admission())\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-026 CERTIFICATION TEST")\n    print(" FULL PAGE COVERAGE ADMISSION")\n    print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-026 certified")\n    print("[DONE] OPC-026 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)


def main():
    print("="*80)
    print(" OPC-026 INSTALLER")
    print(" FULL PAGE COVERAGE ADMISSION")
    print("="*80)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_025_physical_oracle_live_runtime_activation_gate")
    if up.verify_opc_025_physical_oracle_live_runtime_activation_gate() is not True:
        raise RuntimeError("Certified OPC-025 verification failed")
    print("[PASS] Certified OPC-025 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .opc_026_full_page_coverage_admission import *"
        if export not in cur:
            write_exact(INIT,cur.rstrip()+"\n"+export+"\n")
        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OPC-026 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[DONE] OPC-026 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
