from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_032_cross_process_persistence_arbiter.py"
TEST=ROOT/"test_opc_032_cross_process_persistence_arbiter.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom contextlib import contextmanager\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json, os, time, uuid\n\nOPC_032_BUILD_ID="OPC-032"\nOPC_032_REVISION="OPC_032_CROSS_PROCESS_PERSISTENCE_ARBITER_V1"\n\n@dataclass(frozen=True)\nclass ArbiterLease:\n    priority_name:str\n    waited_seconds:float\n    token:str\n    execution_authority:bool=False\n\ndef _runtime(root=None):\n    p=Path(root or Path.cwd()).resolve()/"runtime_state"\n    p.mkdir(parents=True,exist_ok=True)\n    return p\n\ndef lock_path(root=None):\n    return _runtime(root)/"oracle_canonical_persistence_priority.lock"\n\ndef fast_intent_path(root=None):\n    return _runtime(root)/"oracle_fast_lane_persistence_intent.json"\n\ndef _atomic_json(path,data):\n    tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(json.dumps(data,sort_keys=True),encoding="utf-8")\n    os.replace(tmp,path)\n\ndef publish_fast_intent(root=None,ttl_seconds=2.0):\n    token=uuid.uuid4().hex\n    _atomic_json(\n        fast_intent_path(root),\n        {"token":token,"pid":os.getpid(),"expires_at":time.time()+float(ttl_seconds)}\n    )\n    return token\n\ndef clear_fast_intent(token,root=None):\n    p=fast_intent_path(root)\n    if not p.exists():\n        return\n    try:\n        data=json.loads(p.read_text(encoding="utf-8"))\n        if data.get("token")==token:\n            p.unlink(missing_ok=True)\n    except Exception:\n        pass\n\ndef fast_intent_active(root=None):\n    p=fast_intent_path(root)\n    if not p.exists():\n        return False\n    try:\n        data=json.loads(p.read_text(encoding="utf-8"))\n        return float(data.get("expires_at") or 0)>time.time()\n    except Exception:\n        return False\n\ndef _prepare_lock_file(path):\n    path.parent.mkdir(parents=True,exist_ok=True)\n    if not path.exists() or path.stat().st_size<1:\n        with path.open("wb") as f:\n            f.write(b"0")\n\ndef _try_lock(handle):\n    try:\n        import msvcrt\n        handle.seek(0)\n        msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)\n        return True\n    except ImportError:\n        import fcntl\n        try:\n            fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)\n            return True\n        except BlockingIOError:\n            return False\n    except OSError:\n        return False\n\ndef _unlock(handle):\n    try:\n        import msvcrt\n        handle.seek(0)\n        msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)\n    except ImportError:\n        import fcntl\n        fcntl.flock(handle.fileno(),fcntl.LOCK_UN)\n    except OSError:\n        pass\n\n@contextmanager\ndef acquire_persistence_lease(priority_name,root=None,timeout_seconds=5.0,poll_seconds=0.005):\n    priority=str(priority_name).upper()\n    path=lock_path(root)\n    _prepare_lock_file(path)\n    intent_token=None\n\n    if priority=="FAST_LANE":\n        intent_token=publish_fast_intent(root,max(2.0,float(timeout_seconds)+0.5))\n\n    started=time.perf_counter()\n    handle=path.open("r+b",buffering=0)\n    acquired=False\n\n    try:\n        while True:\n            if priority!="FAST_LANE" and fast_intent_active(root):\n                if time.perf_counter()-started>=float(timeout_seconds):\n                    raise TimeoutError("background persistence yielded beyond timeout")\n                time.sleep(float(poll_seconds))\n                continue\n\n            if _try_lock(handle):\n                acquired=True\n                break\n\n            if time.perf_counter()-started>=float(timeout_seconds):\n                raise TimeoutError("persistence arbiter acquisition timed out")\n\n            time.sleep(float(poll_seconds))\n\n        waited=time.perf_counter()-started\n\n        if intent_token is not None:\n            clear_fast_intent(intent_token,root)\n            intent_token=None\n\n        yield ArbiterLease(priority,waited,uuid.uuid4().hex,False)\n\n    finally:\n        if acquired:\n            _unlock(handle)\n        handle.close()\n        if intent_token is not None:\n            clear_fast_intent(intent_token,root)\n\ndef verify_opc_032_cross_process_persistence_arbiter():\n    with acquire_persistence_lease("FAST_LANE",timeout_seconds=1.0) as lease:\n        return (\n            lease.priority_name=="FAST_LANE"\n            and lease.waited_seconds>=0\n            and not lease.execution_authority\n        )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_032_cross_process_persistence_arbiter import verify_opc_032_cross_process_persistence_arbiter\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_032_cross_process_persistence_arbiter())\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-032 CERTIFICATION TEST")\n    print(" CROSS PROCESS PERSISTENCE ARBITER")\n    print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-032 certified")\n    print("[DONE] OPC-032 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)


def main():
    print("="*80)
    print(" OPC-032 INSTALLER")
    print(" CROSS PROCESS PERSISTENCE ARBITER")
    print("="*80)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_031_persistence_priority_contract")
    if up.verify_opc_031_persistence_priority_contract() is not True:
        raise RuntimeError("Certified OPC-031 verification failed")
    print("[PASS] Certified OPC-031 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .opc_032_cross_process_persistence_arbiter import *"
        if export not in current:
            write_exact(INIT,current.rstrip()+"\n"+export+"\n")

        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )

    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OPC-032 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[DONE] OPC-032 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
