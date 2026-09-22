from pathlib import Path
import os,sys,subprocess,importlib,json

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_historical_learning"
MOD=PKG/"ohl_002_postgresql_historical_observation_read_boundary.py"
TEST=ROOT/"test_ohl_002_postgresql_historical_observation_read_boundary.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nimport re\nfrom .ohl_001_historical_backfill_foundation import verify_ohl_001_historical_backfill_foundation\n\nOHL_002_BUILD_ID="OHL-002"\nOHL_002_REVISION="OHL_002_POSTGRESQL_HISTORICAL_OBSERVATION_READ_BOUNDARY_V1"\n_IDENT=re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")\n\n@dataclass(frozen=True)\nclass HistoricalReadSpec:\n    schema:str\n    table:str\n    limit:int\n    read_only:bool=True\n\ndef safe_identifier(value:str)->str:\n    value=str(value)\n    if not _IDENT.fullmatch(value):\n        raise ValueError("unsafe SQL identifier")\n    return value\n\ndef build_historical_read_spec(schema="public",table="oracle_canonical_observations",limit=1000):\n    if not verify_ohl_001_historical_backfill_foundation():\n        raise RuntimeError("OHL-001 verification failed")\n    schema=safe_identifier(schema); table=safe_identifier(table)\n    limit=int(limit)\n    if limit < 1 or limit > 10000:\n        raise ValueError("limit must be 1..10000")\n    return HistoricalReadSpec(schema,table,limit,True)\n\ndef build_select_sql(spec:HistoricalReadSpec):\n    return f\'SELECT * FROM "{spec.schema}"."{spec.table}" ORDER BY 1 ASC LIMIT %s\'\n\ndef verify_ohl_002_postgresql_historical_observation_read_boundary():\n    s=build_historical_read_spec(limit=50)\n    return s.read_only and s.limit==50 and "SELECT *" in build_select_sql(s)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_historical_learning.ohl_002_postgresql_historical_observation_read_boundary import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ohl_002_postgresql_historical_observation_read_boundary())\n    def test_identifier_rejected(self):\n        with self.assertRaises(ValueError): safe_identifier("x;drop")\n    def test_limit_contract(self):\n        with self.assertRaises(ValueError): build_historical_read_spec(limit=10001)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OHL-002 CERTIFICATION TEST")\n    print(" POSTGRESQL HISTORICAL OBSERVATION READ BOUNDARY")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Postgresql Historical Observation Read Boundary certified")\n    print("[DONE] OHL-002 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OHL-002 INSTALLER")
    print(" POSTGRESQL HISTORICAL OBSERVATION READ BOUNDARY")
    print("="*72)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_historical_learning.ohl_001_historical_backfill_foundation")
    if getattr(up,"verify_ohl_001_historical_backfill_foundation")() is not True:
        raise RuntimeError("Certified OHL-001 upstream verification failed")
    print("[PASS] Certified OHL-001 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .ohl_002_postgresql_historical_observation_read_boundary import *"
        if export not in current:
            write_exact(INIT,current.rstrip()+"\n"+export+"\n")
        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OHL-002 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OHL-002 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__": main()
