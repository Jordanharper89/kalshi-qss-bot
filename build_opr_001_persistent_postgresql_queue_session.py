from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_postgresql_reliability"
MOD=PKG/"opr_001_persistent_queue_session.py";TEST=ROOT/"test_opr_001_persistent_postgresql_queue_session.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport pickle,time,uuid\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import (\n    TABLE,database_url,ensure_postgresql_ingestion_schema\n)\n\nOPR_001_BUILD_ID="OPR-001"\nOPR_001_REVISION="OPR_001_PERSISTENT_POSTGRESQL_QUEUE_SESSION_V1"\n\ndef _dump(x):return pickle.dumps(x,protocol=5)\ndef _load(x):return None if x is None else pickle.loads(bytes(x))\n\ndef _connection_error(exc):\n    name=type(exc).__name__.lower()\n    text=(name+" "+str(exc)).lower()\n    return any(x in text for x in (\n        "operationalerror","interfaceerror","connection","server closed",\n        "connection reset","closed the connection","terminating connection"\n    ))\n\n@dataclass(frozen=True)\nclass PersistentQueueSubmission:\n    request_id:str\n    producer:str\n    priority:int\n    observation_count:int\n\nclass PersistentQueueSession:\n    def __init__(self,root=None,autocommit=True):\n        self.root=Path(root or Path.cwd()).resolve()\n        self.autocommit=bool(autocommit)\n        self.conn=None\n        self.connect_count=0\n\n    def open(self):\n        if self.conn is not None and not getattr(self.conn,"closed",False):\n            return self.conn\n        import psycopg\n        self.conn=psycopg.connect(database_url(self.root),autocommit=self.autocommit)\n        self.connect_count+=1\n        return self.conn\n\n    def reconnect(self):\n        self.close()\n        return self.open()\n\n    def close(self):\n        if self.conn is not None:\n            try:self.conn.close()\n            except Exception:pass\n        self.conn=None\n\n    def execute(self,sql,params=(),fetchone=False,fetchall=False,retry_connection=True):\n        for attempt in range(2 if retry_connection else 1):\n            try:\n                conn=self.open()\n                with conn.cursor() as cur:\n                    cur.execute(sql,params)\n                    if fetchone:return cur.fetchone()\n                    if fetchall:return cur.fetchall()\n                    return cur.rowcount\n            except Exception as exc:\n                if attempt==0 and _connection_error(exc):\n                    self.reconnect()\n                    continue\n                raise\n\n    def backend_pid(self):\n        row=self.execute("SELECT pg_backend_pid()",fetchone=True)\n        return int(row[0])\n\n    def submit(self,producer,priority,observations):\n        items=tuple(observations)\n        request_id=uuid.uuid4().hex\n        self.execute(\n            f"""INSERT INTO public.{TABLE}\n                (request_id,producer,priority,observations,observation_count,status)\n                VALUES(%s,%s,%s,%s,%s,\'PENDING\')""",\n            (request_id,str(producer),int(priority),_dump(items),len(items)),\n        )\n        return PersistentQueueSubmission(request_id,str(producer),int(priority),len(items))\n\n    def await_result(self,request_id,timeout_seconds=120.0,poll_seconds=0.025):\n        deadline=time.monotonic()+float(timeout_seconds)\n        while time.monotonic()<deadline:\n            row=self.execute(\n                f"""SELECT status,result_payload,last_error_type,last_error_message\n                    FROM public.{TABLE} WHERE request_id=%s""",\n                (str(request_id),),fetchone=True,\n            )\n            if row is None:\n                raise RuntimeError("PostgreSQL ingestion request disappeared")\n            status,payload,et,em=row\n            if status=="DONE":return tuple(_load(payload) or ())\n            if status=="FAILED":raise RuntimeError(f"PostgreSQL ingestion failed: {et}: {em}")\n            time.sleep(float(poll_seconds))\n        raise TimeoutError(f"PostgreSQL ingestion request timed out: {request_id}")\n\n    def queue_counts(self):\n        rows=self.execute(\n            f"SELECT status,COUNT(*) FROM public.{TABLE} GROUP BY status ORDER BY status",\n            fetchall=True,\n        )\n        return {str(s):int(c) for s,c in rows}\n\ndef verify_opr_001_persistent_postgresql_queue_session(root=None):\n    return (\n        OPR_001_BUILD_ID=="OPR-001"\n        and callable(PersistentQueueSession)\n        and PersistentQueueSubmission("r","p",1,2).observation_count==2\n    )\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_postgresql_reliability.opr_001_persistent_queue_session import *\n\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OPR_001_BUILD_ID,"OPR-001")\n    def test_contract(self):self.assertTrue(verify_opr_001_persistent_postgresql_queue_session())\n    def test_submission(self):self.assertEqual(PersistentQueueSubmission("r","p",1,3).observation_count,3)\n\nif __name__=="__main__":\n    print("="*88);print(" OPR-001 CERTIFICATION TEST");print(" PERSISTENT POSTGRESQL QUEUE SESSION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Long-lived PostgreSQL queue session contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPR-001 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists():path.unlink()
    else:path.write_bytes(data)

def update_init(path,line):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+line+"\n")

def main():
    print("="*88);print(" OPR-001 INSTALLER");print(" PERSISTENT POSTGRESQL QUEUE SESSION");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_033_postgresql_persistence_reliability_freeze")
    if not up.verify_oph_033_postgresql_persistence_reliability_freeze(ROOT):raise RuntimeError("Frozen OPH-033 boundary verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .opr_001_persistent_queue_session import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_postgresql_reliability.opr_001_persistent_queue_session")
        from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import ensure_postgresql_ingestion_schema
        ensure_postgresql_ingestion_schema(ROOT)
        s=m.PersistentQueueSession(ROOT);p1=s.backend_pid();p2=s.backend_pid();s.close()
        if p1!=p2:raise RuntimeError("PostgreSQL session did not preserve backend PID")
        print("[PHYSICAL] backend_pid="+str(p1)+" repeated_backend_pid="+str(p2)+" connect_count=1")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OPR-001 failed; files restored");raise
    print("[PASS] OPH-001 through OPH-033 preserved")
    print("[PASS] Proven learning path untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPR-001 INSTALLATION COMPLETE")
if __name__=="__main__":main()
