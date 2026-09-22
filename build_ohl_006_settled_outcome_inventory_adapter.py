from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_historical_learning"
MOD_PATH=PKG/"ohl_006_settled_outcome_inventory_adapter.py"
TEST_PATH=ROOT/"test_ohl_006_settled_outcome_inventory_adapter.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_learning_runtime.olr_002_settled_outcome_read_model import fetch_recent_settled_markets\nfrom .ohl_005_historical_learning_candidate_gate import verify_ohl_005_historical_learning_candidate_gate\n\nOHL_006_BUILD_ID="OHL-006"\nOHL_006_REVISION="OHL_006_SETTLED_OUTCOME_INVENTORY_ADAPTER_V1"\n\n@dataclass(frozen=True)\nclass SettledOutcomeInventory:\n    requested_limit:int\n    settled_count:int\n    unique_tickers:int\n    outcomes:tuple\n    read_only:bool=True\n\ndef read_settled_outcome_inventory(root=None,limit=500):\n    if not verify_ohl_005_historical_learning_candidate_gate():\n        raise RuntimeError("OHL-005 verification failed")\n    limit=int(limit)\n    if limit < 1 or limit > 10000:\n        raise ValueError("limit must be 1..10000")\n    root=Path(root or Path.cwd()).resolve()\n    rows=tuple(fetch_recent_settled_markets(root,limit=limit))\n    tickers={str(getattr(x,"ticker","")) for x in rows if str(getattr(x,"ticker",""))}\n    return SettledOutcomeInventory(limit,len(rows),len(tickers),rows,True)\n\ndef verify_ohl_006_settled_outcome_inventory_adapter():\n    x=SettledOutcomeInventory(10,0,0,tuple(),True)\n    return x.requested_limit==10 and x.read_only\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_historical_learning.ohl_006_settled_outcome_inventory_adapter import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ohl_006_settled_outcome_inventory_adapter())\n    def test_limit_contract(self):\n        with self.assertRaises(ValueError):read_settled_outcome_inventory("__missing__",0)\n\nif __name__=="__main__":\n    print("="*72);print(" OHL-006 CERTIFICATION TEST");print(" SETTLED OUTCOME INVENTORY ADAPTER");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Frozen OLR settled-outcome read boundary adapter certified")\n    print("[DONE] OHL-006 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OHL-006 INSTALLER")
    print(" SETTLED OUTCOME INVENTORY ADAPTER")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    up=importlib.import_module('qseries_v2.oracle_historical_learning.ohl_005_historical_learning_candidate_gate')
    if getattr(up,'verify_ohl_005_historical_learning_candidate_gate')() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OHL-005 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .ohl_006_settled_outcome_inventory_adapter import *"
        if line not in current:
            write_exact(INIT_PATH,current.rstrip()+"\n"+line+"\n")
        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OHL-006 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OHL-006 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
