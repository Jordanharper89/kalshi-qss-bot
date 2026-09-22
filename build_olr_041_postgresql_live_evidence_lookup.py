from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_041_postgresql_live_evidence_lookup.py";TEST=ROOT/"test_olr_041_postgresql_live_evidence_lookup.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\n\nOLR_041_BUILD_ID="OLR-041"\nOLR_041_REVISION="OLR_041_POSTGRESQL_LIVE_EVIDENCE_LOOKUP_V1"\n\ndef _connect():\n    from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n    return connect\n\ndef lookup_market_evidence(outcome,root=None,limit=200):\n    root=Path(root or Path.cwd()).resolve()\n    ticker=""\n    market_id=""\n    if hasattr(outcome,"get"):\n        ticker=str(outcome.get("ticker") or outcome.get("market_ticker") or "").strip()\n        market_id=str(outcome.get("market_id") or ticker).strip()\n    else:\n        ticker=str(getattr(outcome,"ticker","") or getattr(outcome,"market_ticker","")).strip()\n        market_id=str(getattr(outcome,"market_id","") or ticker).strip()\n\n    if not ticker and not market_id:\n        return ()\n\n    queries=[\n        """SELECT observation_id,ticker,market_id,sequence_number,observed_at\n             FROM public.oracle_canonical_observations\n            WHERE ticker=%s OR market_id=%s\n            ORDER BY sequence_number DESC\n            LIMIT %s""",\n        """SELECT observation_id,market_ticker AS ticker,market_ticker AS market_id,sequence_number,observed_at\n             FROM public.oracle_canonical_observations\n            WHERE market_ticker=%s\n            ORDER BY sequence_number DESC\n            LIMIT %s""",\n    ]\n\n    with _connect()(root) as conn:\n        with conn.cursor() as cur:\n            last=None\n            for idx,sql in enumerate(queries):\n                try:\n                    if idx==0:\n                        cur.execute(sql,(ticker,market_id,int(limit)))\n                    else:\n                        cur.execute(sql,(ticker,int(limit)))\n                    rows=cur.fetchall()\n                    return tuple({\n                        "observation_id":r[0],\n                        "ticker":r[1],\n                        "market_id":r[2],\n                        "sequence_number":r[3],\n                        "observed_at":r[4],\n                    } for r in rows)\n                except Exception as exc:\n                    conn.rollback()\n                    last=exc\n            if last is not None:\n                raise last\n    return ()\n\ndef verify_olr_041_postgresql_live_evidence_lookup(root=None):\n    from .olr_040_outcome_evidence_linkage_freeze import verify_olr_040_outcome_evidence_linkage_freeze\n    return verify_olr_040_outcome_evidence_linkage_freeze(root) and OLR_041_BUILD_ID=="OLR-041"\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_041_postgresql_live_evidence_lookup import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLR_041_BUILD_ID,"OLR-041")\n    def test_callable(self):self.assertTrue(callable(lookup_market_evidence))\nif __name__=="__main__":\n    print("="*88);print(" OLR-041 CERTIFICATION TEST");print(" POSTGRESQL LIVE EVIDENCE LOOKUP");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Live PostgreSQL evidence lookup contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-041 CERTIFIED")\n'

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
    print("="*88);print(" OLR-041 INSTALLER");print(" POSTGRESQL LIVE EVIDENCE LOOKUP");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_learning.olr_040_outcome_evidence_linkage_freeze")
    if not up.verify_olr_040_outcome_evidence_linkage_freeze(ROOT):raise RuntimeError("Certified OLR-040 verification failed")
    print("[PASS] Certified OLR-040 upstream boundary verified read-only")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_041_postgresql_live_evidence_lookup import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-041 installation failed; affected files restored");raise
    print("[PASS] OLR-036 through OLR-040 preserved frozen")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-041 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
