from pathlib import Path
import py_compile

R = Path.cwd()
M = R / "qseries_v2/oracle_strategy_intelligence/solana_money/qarb_execution_engineering/qarb_080_single_runtime_dynamic_mriya_supervisor.py"
T = R / "test_qarb_080_single_runtime_dynamic_mriya_supervisor.py"

if not M.is_file():
    raise SystemExit("[FAIL] current QARB-080 missing: " + str(M))

src = M.read_text(encoding="utf-8")

def patch(old, new, label):
    global src
    if old not in src:
        raise SystemExit("[FAIL] exact current seam changed: " + label)
    src = src.replace(old, new, 1)

required = [
    'MEMORY=Path("runtime_state/qseries/qarb_execution_engineering/qarb_080_binding_memory.json")',
    'HYDRATION_LOCK=Path("runtime_state/qseries/qarb_execution_engineering/qarb_080_hydration.lock")',
    'def announce(root,rows):',
    'q47.p._worker=q61d.staggered_worker',
    'return await q47.p.serve(',
    'children=[]',
    'generation=0',
]
missing = [x for x in required if x not in src]
if missing:
    raise SystemExit("[FAIL] exact current QARB-080 contract changed: " + repr(missing))

patch(
    'MEMORY=Path("runtime_state/qseries/qarb_execution_engineering/qarb_080_binding_memory.json")\n'
    'HYDRATION_LOCK=Path("runtime_state/qseries/qarb_execution_engineering/qarb_080_hydration.lock")',
    'MEMORY=Path("runtime_state/qseries/qarb_execution_engineering/qarb_080_binding_memory.json")\n'
    'PRESENCE=Path("runtime_state/qseries/qarb_execution_engineering/qarb_080_presence.json")\n'
    'HYDRATION_LOCK=Path("runtime_state/qseries/qarb_execution_engineering/qarb_080_hydration.lock")',
    "presence state"
)

patch(
    'LOCK_STALE_SECONDS=240.0',
    'LOCK_STALE_SECONDS=240.0\nWS_CONNECTION_STAGGER_SECONDS=2.0',
    "ws stagger constant"
)

old_announce = '''def announce(root,rows):
    root=Path(root)
    seen=set(_load(root/SEEN,{"tokens":[]}).get("tokens",[]))
    _,retired=lifecycle_sets(root)
    now={x["token"] for x in rows if x.get("token")}

    introduced=sorted(now-seen)
    returned=sorted(set(introduced)&retired)

    for token in introduced:
        if token in returned:
            print("[TOKEN_RETURN] token=%s prior=RETIRED"%token,flush=True)
        else:
            print("[NEW_TOKEN] token=%s"%token,flush=True)

    _save(root/SEEN,{"tokens":sorted(seen|now)})
    return introduced,returned'''

new_announce = '''def announce(root,rows):
    root=Path(root)
    seen=set(_load(root/SEEN,{"tokens":[]}).get("tokens",[]))
    prior=set(_load(root/PRESENCE,{"tokens":[]}).get("tokens",[]))
    _,retired=lifecycle_sets(root)
    now={x["token"] for x in rows if x.get("token")}

    entered=now-prior
    introduced=sorted(entered-seen)
    returned=sorted(entered&seen&retired)

    for token in introduced:
        print("[NEW_TOKEN] token=%s"%token,flush=True)

    for token in returned:
        print("[TOKEN_RETURN] token=%s prior=RETIRED"%token,flush=True)

    _save(root/SEEN,{"tokens":sorted(seen|now)})
    _save(root/PRESENCE,{"tokens":sorted(now)})
    return introduced,returned'''

patch(old_announce, new_announce, "announce resurrection logic")

patch(
    '''    q61d.install()

    q47.p.m._shards=q61d.capped_valves
    q47.p._worker=q61d.staggered_worker''',
    '''    q61d.CONNECTION_STAGGER_SECONDS=WS_CONNECTION_STAGGER_SECONDS
    q61d.install()

    q47.p.m._shards=q61d.capped_valves
    q47.p._worker=q61d.staggered_worker''',
    "generation ws stagger"
)

patch(
    '''    return await q47.p.serve(
        root,
        seconds
    )''',
    '''    result=await q47.p.serve(
        root,
        seconds
    )

    reconnects=int(result.get("reconnects",0)) if isinstance(result,dict) else 0
    rate_limits=int(result.get("rate_limit_disconnects",0)) if isinstance(result,dict) else 0
    clean=(reconnects==0 and rate_limits==0)

    print(
        "[WS_TRANSPORT_%s] gen=%d reconnects=%d rate_limits=%d stagger=%.2fs"%(
            "PASS" if clean else "HOLD",
            generation,
            reconnects,
            rate_limits,
            WS_CONNECTION_STAGGER_SECONDS
        ),
        flush=True
    )

    return 0 if clean else 2''',
    "generation transport result"
)

patch(
    '''    q61d.install()

    discovery=subprocess.Popen(''',
    '''    q61d.CONNECTION_STAGGER_SECONDS=WS_CONNECTION_STAGGER_SECONDS
    q61d.install()

    discovery=subprocess.Popen(''',
    "parent ws stagger"
)

patch(
    '''    children=[]
    started=time.monotonic()
    generation=0''',
    '''    children=[]
    started=time.monotonic()
    generation=0
    transport_failures=0''',
    "transport failure counter"
)

patch(
    '''            children=[
                x for x in children
                if x.poll() is None
            ]''',
    '''            alive=[]
            for ch in children:
                rc=ch.poll()
                if rc is None:
                    alive.append(ch)
                elif rc!=0:
                    transport_failures+=1
            children=alive''',
    "child result propagation"
)

patch(
    '''                    "hydration_serialized":
                        True,
                    "ws_cap":''',
    '''                    "hydration_serialized":
                        True,
                    "transport_failures":
                        transport_failures,
                    "ws_cap":''',
    "persist transport failures"
)

patch(
    '''        for ch in children:
            try:
                ch.wait(
                    timeout=max(
                        1.0,
                        deadline-time.time()
                    )
                )

            except Exception:
                try:
                    ch.terminate()
                except Exception:
                    pass''',
    '''        for ch in children:
            try:
                rc=ch.wait(
                    timeout=max(
                        1.0,
                        deadline-time.time()
                    )
                )
                if rc not in (None,0):
                    transport_failures+=1
            except Exception:
                transport_failures+=1
                try:
                    ch.terminate()
                except Exception:
                    pass''',
    "final drain result"
)

patch(
    '''    print(
        "[RUNTIME_DONE] generations=%d execution_authority=FALSE"%generation,
        flush=True
    )

    return 0''',
    '''    transport_status="PASS" if transport_failures==0 else "HOLD"

    print(
        "[WS_TRANSPORT_FINAL] status=%s failed_generations=%d"%(
            transport_status,
            transport_failures
        ),
        flush=True
    )

    print(
        "[RUNTIME_DONE] generations=%d execution_authority=FALSE"%generation,
        flush=True
    )

    return 0 if transport_failures==0 else 2''',
    "final transport gate"
)

M.write_text(src, encoding="utf-8")

test_src = r'''
import inspect
import tempfile
import unittest
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_080_single_runtime_dynamic_mriya_supervisor as q

class T(unittest.TestCase):
    def test_current_repo_contracts(self):
        self.assertTrue(callable(q.q47.prepare_from))
        self.assertTrue(callable(q.q47.write_generation))
        self.assertTrue(callable(q.rv.gated_rpc))
        self.assertEqual(q.q61d.MAX_SUBSCRIPTIONS_PER_CONNECTION,64)

    def test_cross_process_hydration_lock(self):
        s=inspect.getsource(q.acquire_hydration_lock)
        self.assertIn("O_EXCL",s)
        self.assertIn("LOCK_STALE_SECONDS",s)

    def test_exact_rpc_valve_applied(self):
        self.assertIn(
            "q47.p.m.pd.c.rpc=rv.gated_rpc",
            inspect.getsource(q.generation_worker)
        )

    def test_single_worker_hydration(self):
        s=inspect.getsource(q.generation_worker)
        self.assertIn("pairs,landing=q47.prepare_from",s)
        self.assertIn("def cached_prepare",s)
        self.assertIn("q47.p.m.pd.prepare_pairs=cached_prepare",s)

    def test_horizon_safe_windows(self):
        r,d=q.normalize_windows(30,125)
        self.assertGreaterEqual(r,60)
        self.assertGreaterEqual(d,r+95)
        self.assertGreaterEqual(d-r,90)

    def test_learning_preserved(self):
        self.assertTrue(issubclass(q.LearningAgeLane,q.q47.AgeDrainLane))
        self.assertIn("q73.observe",inspect.getsource(q.LearningAgeLane.capture))

    def test_presence_state(self):
        self.assertEqual(q.PRESENCE.name,"qarb_080_presence.json")

    def test_new_token_only_once(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            old=q.lifecycle_sets
            try:
                q.lifecycle_sets=lambda _:(set(),set())
                new,ret=q.announce(root,[{"token":"NEW1"}])
                self.assertEqual(new,["NEW1"])
                self.assertEqual(ret,[])
                new,ret=q.announce(root,[{"token":"NEW1"}])
                self.assertEqual(new,[])
                self.assertEqual(ret,[])
            finally:
                q.lifecycle_sets=old

    def test_true_retired_return(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            old=q.lifecycle_sets
            try:
                q.lifecycle_sets=lambda _:(set(),{"TOK1"})
                q._save(root/q.SEEN,{"tokens":["TOK1"]})
                q._save(root/q.PRESENCE,{"tokens":[]})
                new,ret=q.announce(root,[{"token":"TOK1"}])
                self.assertEqual(new,[])
                self.assertEqual(ret,["TOK1"])
            finally:
                q.lifecycle_sets=old

    def test_continuous_active_not_return(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            old=q.lifecycle_sets
            try:
                q.lifecycle_sets=lambda _:({"WIN1"},set())
                q._save(root/q.SEEN,{"tokens":["WIN1"]})
                q._save(root/q.PRESENCE,{"tokens":["WIN1"]})
                new,ret=q.announce(root,[{"token":"WIN1"}])
                self.assertEqual(new,[])
                self.assertEqual(ret,[])
            finally:
                q.lifecycle_sets=old

    def test_ws_stagger_repair(self):
        self.assertGreaterEqual(q.WS_CONNECTION_STAGGER_SECONDS,2.0)
        self.assertIn(
            "CONNECTION_STAGGER_SECONDS",
            inspect.getsource(q.generation_worker)
        )

    def test_transport_zero_reconnect_requirement(self):
        s=inspect.getsource(q.generation_worker)
        self.assertIn("reconnects==0",s)
        self.assertIn("rate_limits==0",s)
        self.assertIn("WS_TRANSPORT_",s)

    def test_parent_propagates_worker_failure(self):
        s=inspect.getsource(q.run)
        self.assertIn("transport_failures",s)
        self.assertIn("WS_TRANSPORT_FINAL",s)

    def test_safety(self):
        self.assertFalse(q.EXECUTION_AUTHORITY)
        self.assertTrue(q.PAPER_ONLY)
        self.assertFalse(q.REAL_MONEY_MOVED)

if __name__=="__main__":
    unittest.main(verbosity=2)
'''

T.write_text(test_src, encoding="utf-8")

py_compile.compile(str(M), doraise=True)
py_compile.compile(str(T), doraise=True)

print("[PASS] QARB-080 final in-place repair installed")
print("[RETURN] true retired-token resurrection installed")
print("[RECYCLE] continuously profitable ACTIVE token behavior preserved")
print("[WS] 64-account cap preserved; generation starts staggered >=2.0s")
print("[CERT] any worker reconnect/rate-limit => HOLD")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE")