from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve(); PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_013_coverage_freshness_refresh_policy.py"; TEST=ROOT/"test_opc_013_coverage_freshness_refresh_policy.py"; INIT=PKG/"__init__.py"
MODULE='from dataclasses import dataclass\nfrom datetime import datetime,timezone,timedelta\n@dataclass(frozen=True)\nclass CoverageFreshnessDecision:\n    ticker:str; refresh_required:bool; reason:str; age_seconds:float|None; read_only:bool=True; execution_allowed:bool=False\ndef evaluate_freshness(ticker,last_observed_at,now=None,max_age_seconds=900):\n    now=now or datetime.now(timezone.utc)\n    if last_observed_at is None: return CoverageFreshnessDecision(str(ticker),True,"NEVER_OBSERVED",None)\n    dt=last_observed_at\n    if isinstance(dt,str): dt=datetime.fromisoformat(dt.replace("Z","+00:00"))\n    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)\n    age=max(0.0,(now-dt.astimezone(timezone.utc)).total_seconds())\n    return CoverageFreshnessDecision(str(ticker),age>=max_age_seconds,"STALE" if age>=max_age_seconds else "FRESH",age)\ndef verify_opc_013_coverage_freshness_refresh_policy():\n    n=datetime(2026,1,1,tzinfo=timezone.utc)\n    return evaluate_freshness("A",None,n).refresh_required and not evaluate_freshness("B",n-timedelta(seconds=10),n).refresh_required and evaluate_freshness("C",n-timedelta(seconds=1000),n).refresh_required\n'; TESTSRC='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_013_coverage_freshness_refresh_policy import verify_opc_013_coverage_freshness_refresh_policy\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_opc_013_coverage_freshness_refresh_policy())\nif __name__=="__main__":\n    print("="*72); print(" OPC-013 CERTIFICATION TEST"); print(" COVERAGE FRESHNESS REFRESH POLICY"); print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OPC-013 certified"); print("[DONE] OPC-013 CERTIFIED")\n'
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
    print("="*72); print(" OPC-013 INSTALLER"); print(" COVERAGE FRESHNESS REFRESH POLICY"); print("="*72); print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_012_coverage_priority_engine")
    if up.verify_opc_012_coverage_priority_engine() is not True: raise RuntimeError("OPC-012 verification failed")
    print("[PASS] Certified OPC-012 upstream boundary verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write(MOD,MODULE); write(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; ex="from .opc_013_coverage_freshness_refresh_policy import *"
        if ex not in cur: write(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] OPC-013 installation failed"); raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT)); print("[PASS] Wrote:",TEST.name); print("[PASS] Updated:",INIT.relative_to(ROOT)); print("[DONE] OPC-013 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
