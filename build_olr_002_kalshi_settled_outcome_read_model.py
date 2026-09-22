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

BUILD_ID='OLR-002'
TITLE='KALSHI SETTLED OUTCOME READ MODEL'
REVISION='OLR_002_PRODUCTION_V1'
MODULE=PACKAGE/'olr_002_settled_outcome_read_model.py'
TEST=ROOT/'test_olr_002_kalshi_settled_outcome_read_model.py'
EXPORTS=('OLR_002_BUILD_ID', 'OLR_002_REVISION', 'SettledMarketOutcome', 'normalize_settled_market', 'fetch_recent_settled_markets', 'verify_olr_002_kalshi_settled_outcome_read_model')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom hashlib import sha256\nimport json\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\nfrom qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get\nOLR_002_BUILD_ID="OLR-002"\nOLR_002_REVISION="OLR_002_KALSHI_SETTLED_OUTCOME_READ_MODEL_V1"\n\n@dataclass(frozen=True)\nclass SettledMarketOutcome:\n    ticker:str\n    result:str\n    settlement_ts:str\n    source_hash:str\n    raw:dict\n\ndef _h(v):\n    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\n\ndef normalize_settled_market(market):\n    m=dict(market)\n    ticker=str(m.get("ticker") or "").strip()\n    result=str(m.get("result") or "").lower().strip()\n    ts=str(m.get("settlement_ts") or m.get("settled_ts") or m.get("settled_time") or "").strip()\n    if not ticker or result not in ("yes","no","scalar") or not ts:\n        return None\n    return SettledMarketOutcome(ticker,result,ts,_h(m),m)\n\ndef fetch_recent_settled_markets(root=None,limit=100):\n    root=Path(root or Path.cwd()).resolve()\n    c=load_kalshi_credentials(root=root)\n    r=kalshi_rest_get(c,"/markets",{"limit":max(1,min(int(limit),1000)),"status":"settled"},10)\n    rows=tuple(x for x in (normalize_settled_market(m) for m in r.body.get("markets",())) if x is not None)\n    return tuple(sorted(rows,key=lambda x:(x.settlement_ts,x.ticker)))\n\ndef verify_olr_002_kalshi_settled_outcome_read_model():\n    x=normalize_settled_market({"ticker":"KXTEST","result":"yes","settlement_ts":"2026-08-14T00:00:00Z"})\n    return x is not None and x.result=="yes" and len(x.source_hash)==64\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_002_settled_outcome_read_model import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_002_kalshi_settled_outcome_read_model())\n    def test_unresolved_rejected(self):self.assertIsNone(normalize_settled_market({"ticker":"A","result":""}))\nif __name__=="__main__":\n    print("="*72);print(" OLR-002 CERTIFICATION TEST");print(" KALSHI SETTLED OUTCOME READ MODEL");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Settled outcome normalization certified")\n    print("[DONE] OLR-002 CERTIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_001_foundation')
        if getattr(m,'verify_olr_001_oracle_learning_runtime_foundation')() is not True:
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
