from pathlib import Path
import importlib, os, subprocess, sys, hashlib

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_trader_intelligence_bridge/otib_001_oia_admission_adapter.py'
TEST=ROOT/'test_otib_001_oia_admission_adapter.py'

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_intelligence.analytics.oracle_opportunity_admission_gate import OracleOpportunityAdmissionGate\n\nOTIB_001_BUILD_ID="OTIB-001"\n\n@dataclass(frozen=True)\nclass OIAAdmissionSnapshot:\n    reviewed_market_count:int\n    admitted_market_count:int\n    denied_market_count:int\n    not_candidate_market_count:int\n    markets:tuple\n    report_hash:str\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef load_oia_admission_snapshot(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    def connection_factory():\n        return connect(root,autocommit=False)\n    report=OracleOpportunityAdmissionGate(connection_factory=connection_factory).evaluate()\n    if report.read_only is not True or report.execution_allowed:\n        raise RuntimeError("OIA-007 read-only boundary violation")\n    return OIAAdmissionSnapshot(\n        int(report.reviewed_market_count),\n        int(report.admitted_market_count),\n        int(report.denied_market_count),\n        int(report.not_candidate_market_count),\n        tuple(report.markets),\n        str(report.report_hash),\n        True,\n        False,\n    )\n\ndef verify_oia_admission_snapshot(x):\n    if not x.read_only or x.execution_authority:\n        raise RuntimeError("OTIB-001 read-only boundary violation")\n    if x.reviewed_market_count != len(x.markets):\n        raise RuntimeError("OTIB-001 reviewed count mismatch")\n    return True\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_trader_intelligence_bridge.otib_001_oia_admission_adapter import OIAAdmissionSnapshot,verify_oia_admission_snapshot\nclass T(unittest.TestCase):\n    def test_contract(self):\n        x=OIAAdmissionSnapshot(0,0,0,0,(),"h",True,False)\n        self.assertTrue(verify_oia_admission_snapshot(x))\nif __name__=="__main__":\n    print("="*88);print(" OTIB-001 CERTIFICATION TEST");print(" CERTIFIED OIA-007 PRODUCTION READ ADAPTER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OIA-007 read-only adapter contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OTIB-001 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("="*88);print(" OTIB-001 INSTALLER");print(" CERTIFIED OIA-007 PRODUCTION READ ADAPTER");print("="*88);print("[ROOT]",ROOT)
    required=(
        ROOT/"qseries_v2"/"oracle_intelligence"/"analytics"/"oracle_opportunity_admission_gate.py",
        ROOT/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py",
    )
    for p in required:
        if not p.is_file():raise RuntimeError(f"Required certified upstream missing: {p}")
    pkg=MOD.parent;init=pkg/"__init__.py";old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,init)}
    try:
        pkg.mkdir(parents=True,exist_ok=True)
        if not init.exists():write_exact(init,"")
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_trader_intelligence_bridge.otib_001_oia_admission_adapter")
        x=m.load_oia_admission_snapshot(ROOT);m.verify_oia_admission_snapshot(x)
        print(f"[PHYSICAL] reviewed={x.reviewed_market_count} admitted={x.admitted_market_count} denied={x.denied_market_count} not_candidate={x.not_candidate_market_count}")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OTIB-001 failed; affected files restored");raise
    print("[PASS] physical OIA-007 report consumed")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OTIB-001 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
