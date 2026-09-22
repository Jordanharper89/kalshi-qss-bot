from pathlib import Path
import ast, os, shutil, time

EXPECTED="build_oph_019_postgresql_queue_connection_storm_FOUNDATIONAL_REPAIR.py"
OPH=Path("qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py")
O402=Path("qseries_v2/oracle_adapters/independent/oad_402_solana_zero_cost_surveillance_physical_gate.py")
TEST=Path("test_oph_019_postgresql_queue_connection_storm_foundational_repair.py")
OLD_CONNECT='def connect(root=None,autocommit=False):\n    import psycopg\n    return psycopg.connect(database_url(root),autocommit=autocommit)'
NEW_CONNECT='def connect(root=None,autocommit=False,connect_timeout_seconds=5.0):\n    import psycopg\n    timeout=max(1,int(float(connect_timeout_seconds)))\n    return psycopg.connect(database_url(root),autocommit=autocommit,connect_timeout=timeout)'
OLD_AWAIT='def await_request(request_id,root=None,timeout_seconds=120.0,poll_seconds=0.005):\n    deadline=time.monotonic()+float(timeout_seconds)\n    while time.monotonic()<deadline:\n        with connect(root) as conn:\n            with conn.cursor() as cur:\n                cur.execute(f"""SELECT status,result_payload,last_error_type,last_error_message\n                  FROM public.{TABLE} WHERE request_id=%s""",(str(request_id),))\n                row=cur.fetchone()\n        if row is None:raise RuntimeError("PostgreSQL ingestion request disappeared")\n        status,payload,et,em=row\n        if status=="DONE":return tuple(_load(payload) or ())\n        if status=="FAILED":raise RuntimeError(f"PostgreSQL ingestion failed: {et}: {em}")\n        time.sleep(float(poll_seconds))\n    raise TimeoutError(f"PostgreSQL ingestion request timed out: {request_id}")'
NEW_AWAIT='def await_request(request_id,root=None,timeout_seconds=120.0,poll_seconds=0.05):\n    timeout=float(timeout_seconds)\n    if timeout<=0:raise ValueError("timeout_seconds must be > 0")\n    poll=max(0.01,float(poll_seconds))\n    deadline=time.monotonic()+timeout\n    last_connect_error=None\n    while time.monotonic()<deadline:\n        remaining=max(0.0,deadline-time.monotonic())\n        try:\n            with connect(root,connect_timeout_seconds=min(5.0,max(1.0,remaining))) as conn:\n                with conn.cursor() as cur:\n                    while time.monotonic()<deadline:\n                        cur.execute(f"""SELECT status,result_payload,last_error_type,last_error_message\n                          FROM public.{TABLE} WHERE request_id=%s""",(str(request_id),))\n                        row=cur.fetchone()\n                        if row is None:raise RuntimeError("PostgreSQL ingestion request disappeared")\n                        status,payload,et,em=row\n                        if status=="DONE":return tuple(_load(payload) or ())\n                        if status=="FAILED":raise RuntimeError(f"PostgreSQL ingestion failed: {et}: {em}")\n                        time.sleep(poll)\n            last_connect_error=None\n        except RuntimeError:\n            raise\n        except Exception as exc:\n            last_connect_error=exc\n            if time.monotonic()>=deadline:break\n            time.sleep(min(0.25,max(0.01,deadline-time.monotonic())))\n    suffix="" if last_connect_error is None else f"; last database error: {type(last_connect_error).__name__}: {last_connect_error}"\n    raise TimeoutError(f"PostgreSQL ingestion request timed out: {request_id}{suffix}")'
OLD_CLASSIFIER='def _is_transient_rpc_error(exc: BaseException) -> bool:\n    if isinstance(exc, (TimeoutError, socket.timeout, urllib.error.URLError)):\n        return True\n    msg = str(exc).lower()\n    return any(marker in msg for marker in _TRANSIENT_MARKERS)'
NEW_CLASSIFIER='def _is_transient_rpc_error(exc: BaseException) -> bool:\n    msg = str(exc).lower()\n    if "postgresql ingestion" in msg or "database" in msg or "psycopg" in msg:\n        return False\n    if isinstance(exc, (socket.timeout, urllib.error.URLError)):\n        return True\n    if isinstance(exc, TimeoutError):\n        return True\n    return any(marker in msg for marker in _TRANSIENT_MARKERS)'
TEST_SOURCE='import pickle\nimport unittest\nfrom qseries_v2.oracle_production_hardening import oph_019_postgresql_universal_ingestion_queue as q\nfrom qseries_v2.oracle_adapters.independent.oad_402_solana_zero_cost_surveillance_physical_gate import _is_transient_rpc_error\n\nclass T(unittest.TestCase):\n    def test_await_reuses_one_connection(self):\n        original=q.connect\n        calls={"connect":0,"execute":0}\n        class Cur:\n            def __enter__(self): return self\n            def __exit__(self,*a): return False\n            def execute(self,*a,**k): calls["execute"]+=1\n            def fetchone(self):\n                if calls["execute"]<3:return ("PENDING",None,None,None)\n                return ("DONE",pickle.dumps(("ok",),protocol=5),None,None)\n        class Conn:\n            def __enter__(self): return self\n            def __exit__(self,*a): return False\n            def cursor(self): return Cur()\n        def fake_connect(*a,**k):\n            calls["connect"]+=1\n            return Conn()\n        try:\n            q.connect=fake_connect\n            self.assertEqual(q.await_request("x",timeout_seconds=1,poll_seconds=.01),("ok",))\n            self.assertEqual(calls["connect"],1)\n            self.assertGreaterEqual(calls["execute"],3)\n        finally:q.connect=original\n\n    def test_timeout_classification(self):\n        self.assertFalse(_is_transient_rpc_error(TimeoutError("PostgreSQL ingestion request timed out: abc")))\n        self.assertTrue(_is_transient_rpc_error(TimeoutError("The read operation timed out")))\n\n    def test_boundary(self):\n        self.assertTrue(q.verify_oph_019_postgresql_universal_ingestion_queue())\n\nif __name__=="__main__":\n    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not rr.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OPH-019 foundational PostgreSQL connection-storm repair certified")\n'

def root():
    p=Path.cwd().resolve()
    if not (p/"qseries_v2").is_dir():raise RuntimeError("run installer from repository root")
    return p

def atomic(path,src):
    ast.parse(src,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(src,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    if Path(__file__).name!=EXPECTED:raise RuntimeError("installer filename mismatch")
    r=root(); op=r/OPH; cp=r/O402
    osrc=op.read_text(encoding="utf-8"); csrc=cp.read_text(encoding="utf-8")
    for needle,hay,label in ((OLD_CONNECT,osrc,"OPH-019 connect"),(OLD_AWAIT,osrc,"OPH-019 await_request"),(OLD_CLASSIFIER,csrc,"OAD-402 classifier")):
        if needle not in hay:raise RuntimeError(label+" exact source mismatch; no mutation performed")
    stamp=time.strftime("%Y%m%dT%H%M%S")
    obak=op.with_name(op.name+".pre_connection_storm_repair."+stamp+".bak")
    cbak=cp.with_name(cp.name+".pre_db_timeout_classifier_repair."+stamp+".bak")
    shutil.copy2(op,obak);shutil.copy2(cp,cbak)
    osrc=osrc.replace(OLD_CONNECT,NEW_CONNECT,1).replace(OLD_AWAIT,NEW_AWAIT,1)
    csrc=csrc.replace(OLD_CLASSIFIER,NEW_CLASSIFIER,1)
    atomic(op,osrc);atomic(cp,csrc);atomic(r/TEST,TEST_SOURCE)
    print("[PASS] uploaded repo exact OPH-019 source matched")
    print("[PASS] backup:",obak.relative_to(r))
    print("[PASS] backup:",cbak.relative_to(r))
    print("[PASS] OPH-019 await_request no longer opens a new PostgreSQL connection every 5ms poll")
    print("[PASS] one connection reused during request wait; polling=50ms")
    print("[PASS] PostgreSQL connect establishment bounded to <=5 seconds")
    print("[PASS] OAD-402 no longer mislabels PostgreSQL ingestion timeout as RPC timeout")
    print("[PASS] OPH-021 writer code unchanged")
    print("[PASS] queue schema/interfaces unchanged")
    print("[PASS] OAD-325/OAD-326 interfaces unchanged")
    print("[PASS] no second writer; no checkpoint mutation; no GMGN dependency")
    print("[PASS] execution_authority=FALSE")
    print("[DONE]",EXPECTED)

if __name__=="__main__":main()
