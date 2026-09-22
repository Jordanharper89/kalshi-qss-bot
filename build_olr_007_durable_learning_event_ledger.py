from pathlib import Path
import os,sys,subprocess,importlib
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_learning_runtime";MOD=PKG/"olr_007_learning_event_ledger.py";TEST=ROOT/"test_olr_007_durable_learning_event_ledger.py";INIT=PKG/"__init__.py"
MODULE=r"""
from dataclasses import dataclass
from pathlib import Path
import json,os
OLR_007_BUILD_ID="OLR-007"; OLR_007_REVISION="OLR_007_DURABLE_LEARNING_EVENT_LEDGER_V1"
@dataclass(frozen=True)
class LearningLedgerRecord:
    settlement_hash:str;ticker:str;settlement_ts:str;status:str;evidence_hash:str;learning_event_hash:str
def load_learning_ledger(path):
    p=Path(path)
    if not p.is_file():return {}
    d=json.loads(p.read_text(encoding="utf-8"))
    return {k:LearningLedgerRecord(**v) for k,v in d.items()}
def save_learning_ledger(path,records):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+".tmp")
    payload={k:v.__dict__ for k,v in sorted(records.items())}
    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,p)
def admit_learning_ledger_record(records,record):
    out=dict(records);old=out.get(record.settlement_hash)
    if old is not None and (old==record or old.status=="learned"):return out,False
    out[record.settlement_hash]=record;return out,True
def verify_olr_007_durable_learning_event_ledger():
    r=LearningLedgerRecord("a"*64,"KX","t","eligible","b"*64,"c"*64);x,a=admit_learning_ledger_record({},r);y,b=admit_learning_ledger_record(x,r);return a and not b and x==y
"""
TEST=r"""
import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_007_learning_event_ledger import *
class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_007_durable_learning_event_ledger())
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"ledger.json";r=LearningLedgerRecord("a"*64,"K","t","learned","b"*64,"c"*64)
            save_learning_ledger(p,{r.settlement_hash:r});self.assertEqual(load_learning_ledger(p)[r.settlement_hash],r)
if __name__=="__main__":
    print("="*72);print(" OLR-007 CERTIFICATION TEST");print(" DURABLE LEARNING EVENT LEDGER");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Durable idempotent learning-event ledger certified");print("[DONE] OLR-007 CERTIFIED")
"""
def w(p,s):p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+".tmp");tmp.write_text(s,encoding="utf-8",newline="\n");os.replace(tmp,p)
def main():
    print("="*72);print(" OLR-007 INSTALLER");print(" DURABLE LEARNING EVENT LEDGER");print("="*72)
    sys.path.insert(0,str(ROOT));m=importlib.import_module("qseries_v2.oracle_learning_runtime.olr_006_historical_evidence_matcher");assert m.verify_olr_006_historical_evidence_matcher()
    backs={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        w(MOD,MODULE);w(TEST,TEST);cur=INIT.read_text(encoding="utf-8")
        if "# OLR-007 exports" not in cur:w(INIT,cur.rstrip()+"\n\n# OLR-007 exports\nfrom .olr_007_learning_event_ledger import *\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in backs.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        raise
    print("[DONE] OLR-007 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
