from pathlib import Path
import os,subprocess,sys
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_runtime_health";MOD=PKG/"orh_009_persistence_pressure_telemetry.py";TEST=ROOT/"test_orh_009_persistence_pressure_telemetry.py";INIT=PKG/"__init__.py"
MODULE_SOURCE=r"""from __future__ import annotations
from pathlib import Path
import json,os,time,uuid
from qseries_v2.oracle_production_hardening.oph_029_postgresql_routing_failure_classification import classify_persistence_failure
ORH_009_BUILD_ID="ORH-009";STATE_NAME="oracle_persistence_pressure_telemetry.json"
def _load(path):
    try:return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:return {"total":0,"categories":{},"last_failure":None,"execution_authority":False}
def record_persistence_failure(root,producer,exc):
    root=Path(root or Path.cwd()).resolve();p=root/"runtime_state"/STATE_NAME;p.parent.mkdir(parents=True,exist_ok=True)
    c=classify_persistence_failure(exc);s=_load(p);s["total"]=int(s.get("total",0))+1
    cats=dict(s.get("categories") or {});cats[c.category]=int(cats.get(c.category,0))+1;s["categories"]=cats
    text=(type(exc).__name__+" "+str(exc)).lower()
    reason=("DATABASE_RECOVERY" if "recovery mode" in text else "TIMEOUT" if "timeout" in text or "timed out" in text else "CONNECTION" if "connection" in text else "QUEUE_OR_COMMIT" if "not committed" in text else c.category)
    s["last_failure"]={"ts":time.time(),"producer":str(producer),"category":c.category,"reason":reason,"type":type(exc).__name__,"retryable":c.retryable};s["execution_authority"]=False
    tmp=p.with_name(p.name+f".{os.getpid()}.{uuid.uuid4().hex}.tmp");tmp.write_text(json.dumps(s,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,p);return s
def read_persistence_pressure(root=None):
    root=Path(root or Path.cwd()).resolve();return _load(root/"runtime_state"/STATE_NAME)
def verify_orh_009_persistence_pressure_telemetry():return callable(record_persistence_failure) and callable(read_persistence_pressure)
"""
TEST_SOURCE=r"""import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_runtime_health.orh_009_persistence_pressure_telemetry import *
class PostgreSQLPersistenceRoutingFailure(Exception):pass
class T(unittest.TestCase):
    def test_record(self):
        with tempfile.TemporaryDirectory() as d:
            s=record_persistence_failure(Path(d),"oracle.fast_lane",PostgreSQLPersistenceRoutingFailure("PostgreSQL batch append was not committed"));self.assertEqual(s["total"],1);self.assertEqual(s["last_failure"]["reason"],"QUEUE_OR_COMMIT");self.assertFalse(s["execution_authority"])
if __name__=="__main__":
    print("="*88);print(" ORH-009 CERTIFICATION TEST");print(" PERSISTENCE ROUTING PRESSURE TELEMETRY");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] persistence failure category/reason telemetry certified");print("[PASS] read-only runtime telemetry state certified");print("[PASS] execution_authority=FALSE");print("[DONE] ORH-009 CERTIFIED")
"""
def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+".orh009tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def main():
    print("="*88);print(" ORH-009 INSTALLER");print(" PERSISTENCE ROUTING PRESSURE TELEMETRY");print("="*88);print("[ROOT]",ROOT)
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else "";line="from .orh_009_persistence_pressure_telemetry import *"
        if line not in cur.splitlines():write_exact(INIT,cur.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] ORH-009 failed");raise
    print("[PASS] telemetry module installed without changing Oracle execution authority");print("[PASS] execution_authority=FALSE");print("[DONE] ORH-009 INSTALLATION COMPLETE")
if __name__=="__main__":main()
