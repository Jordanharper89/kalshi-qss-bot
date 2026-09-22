from pathlib import Path
import os,subprocess,sys
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_003_canonical_observation_coverage_read_model.py"
TEST=ROOT/"test_opc_003_canonical_observation_coverage_read_model.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from dataclasses import dataclass\nfrom pathlib import Path\nimport json,os\n\n@dataclass(frozen=True)\nclass CanonicalCoverageResult:\n    sampled_markets:int\n    markets_with_canonical_observation:int\n    markets_without_canonical_observation:int\n    coverage_rate:float\n    observed_tickers:tuple\n    missing_tickers:tuple\n    read_only:bool=True\n\ndef _db(root):\n    u=os.environ.get("DATABASE_URL") or os.environ.get("ORACLE_DATABASE_URL")\n    if u:\n        return u\n    p=Path(root)/".env"\n    if p.is_file():\n        for line in p.read_text(encoding="utf-8",errors="ignore").splitlines():\n            if "=" in line and not line.lstrip().startswith("#"):\n                k,v=line.split("=",1)\n                if k.strip() in ("DATABASE_URL","ORACLE_DATABASE_URL"):\n                    return v.strip().strip(\'"\').strip("\'")\n    raise RuntimeError("database url missing")\n\ndef _ticker(obj):\n    if isinstance(obj,dict):\n        for k in ("ticker","market_ticker","market_id","canonical_market_id","venue_market_id","symbol"):\n            if isinstance(obj.get(k),str) and obj[k]:\n                return obj[k]\n        for v in obj.values():\n            x=_ticker(v)\n            if x:\n                return x\n    elif isinstance(obj,list):\n        for v in obj:\n            x=_ticker(v)\n            if x:\n                return x\n    return ""\n\ndef read_recent_canonical_tickers(root=None,lookback_hours=24,row_limit=250000):\n    root=Path(root or Path.cwd()).resolve()\n    lookback_hours=float(lookback_hours)\n    row_limit=int(row_limit)\n    if lookback_hours<=0 or lookback_hours>168:\n        raise ValueError("lookback_hours out of bounds")\n    import psycopg\n    conn=psycopg.connect(_db(root))\n    try:\n        with conn.cursor() as c:\n            c.execute(\n                "SELECT canonical_observation_json FROM public.oracle_canonical_observations "\n                "WHERE observed_at >= NOW()-(%s*INTERVAL \'1 hour\') ORDER BY observed_at DESC LIMIT %s",\n                (lookback_hours,row_limit)\n            )\n            rows=c.fetchall()\n    finally:\n        conn.close()\n    out=set()\n    for (raw,) in rows:\n        obj=raw\n        if isinstance(raw,str):\n            try:\n                obj=json.loads(raw)\n            except Exception:\n                continue\n        t=_ticker(obj)\n        if t:\n            out.add(t)\n    return out\n\ndef evaluate_canonical_coverage(sample_tickers,canonical_tickers):\n    sample=tuple(dict.fromkeys(str(x) for x in sample_tickers if str(x)))\n    obs=tuple(sorted(t for t in sample if t in canonical_tickers))\n    miss=tuple(sorted(t for t in sample if t not in canonical_tickers))\n    rate=len(obs)/len(sample) if sample else 0.0\n    return CanonicalCoverageResult(len(sample),len(obs),len(miss),rate,obs,miss,True)\n\ndef verify_opc_003_canonical_observation_coverage_read_model():\n    return evaluate_canonical_coverage(("A","B"),{"B"}).coverage_rate==0.5\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_003_canonical_observation_coverage_read_model import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_003_canonical_observation_coverage_read_model())\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OPC-003 CERTIFICATION TEST")\n    print(" CANONICAL OBSERVATION COVERAGE READ MODEL")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Canonical pre-settlement coverage read model certified")\n    print("[DONE] OPC-003 CERTIFIED")\n'

def write_exact(p,t):
    p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp")
    q.write_text(t,encoding="utf-8",newline="\n")
    os.replace(q,p)

def main():
    print("="*72)
    print(" OPC-003 INSTALLER")
    print("="*72)
    print("[ROOT]",ROOT)
    import importlib,sys
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_002_bounded_open_market_sampler")
    fn=getattr(up,"verify_opc_002_bounded_open_market_sampler")
    if fn() is not True:
        raise RuntimeError("upstream verification failed")
    print("[PASS] Certified OPC-002 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line="from .opc_003_canonical_observation_coverage_read_model import *"
        if line not in cur:
            write_exact(INIT,cur.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OPC-003 installation failed")
        raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OPC-003 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
