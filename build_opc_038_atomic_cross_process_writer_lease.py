from pathlib import Path
import importlib
import os
import subprocess
import sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"

MOD=PKG/"opc_038_atomic_cross_process_writer_lease.py"
TEST=ROOT/"test_opc_038_atomic_cross_process_writer_lease.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom contextlib import contextmanager\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json, os, shutil, time, uuid\n\nfrom .opc_037_canonical_writer_arbiter_foundation import writer_policy\n\nOPC_038_BUILD_ID="OPC-038"\nOPC_038_REVISION="OPC_038_ATOMIC_CROSS_PROCESS_WRITER_LEASE_V1"\n\n@dataclass(frozen=True)\nclass CanonicalWriterLease:\n    writer:str\n    token:str\n    waited_seconds:float\n    lease_dir:str\n    execution_authority:bool=False\n\ndef _runtime(root=None):\n    p=Path(root or Path.cwd()).resolve()/"runtime_state"\n    p.mkdir(parents=True,exist_ok=True)\n    return p\n\ndef lease_dir(root=None):\n    return _runtime(root)/"oracle_canonical_writer_lease"\n\ndef fast_intent_path(root=None):\n    return _runtime(root)/"oracle_canonical_fast_lane_intent.json"\n\ndef _atomic_json(path,payload):\n    tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(json.dumps(payload,sort_keys=True),encoding="utf-8")\n    os.replace(tmp,path)\n\ndef _pid_alive(pid):\n    try:\n        pid=int(pid)\n    except Exception:\n        return False\n    if pid<=0:\n        return False\n    if os.name=="nt":\n        import ctypes\n        PROCESS_QUERY_LIMITED_INFORMATION=0x1000\n        handle=ctypes.windll.kernel32.OpenProcess(\n            PROCESS_QUERY_LIMITED_INFORMATION,False,pid\n        )\n        if handle:\n            ctypes.windll.kernel32.CloseHandle(handle)\n            return True\n        return False\n    try:\n        os.kill(pid,0)\n        return True\n    except OSError:\n        return False\n\ndef publish_fast_intent(root=None,ttl_seconds=2.0):\n    token=uuid.uuid4().hex\n    _atomic_json(\n        fast_intent_path(root),\n        {\n            "token":token,\n            "pid":os.getpid(),\n            "expires_at":time.time()+float(ttl_seconds),\n        },\n    )\n    return token\n\ndef clear_fast_intent(token,root=None):\n    p=fast_intent_path(root)\n    if not p.exists():\n        return\n    try:\n        data=json.loads(p.read_text(encoding="utf-8"))\n        if data.get("token")==token:\n            p.unlink(missing_ok=True)\n    except Exception:\n        pass\n\ndef fast_intent_active(root=None):\n    p=fast_intent_path(root)\n    if not p.exists():\n        return False\n    try:\n        data=json.loads(p.read_text(encoding="utf-8"))\n        return float(data.get("expires_at") or 0)>time.time()\n    except Exception:\n        return False\n\ndef _owner_path(path):\n    return path/"owner.json"\n\ndef _read_owner(path):\n    try:\n        return json.loads(_owner_path(path).read_text(encoding="utf-8"))\n    except Exception:\n        return {}\n\ndef _remove_stale_lease(path,stale_seconds):\n    if not path.exists():\n        return False\n\n    owner=_read_owner(path)\n    pid=owner.get("pid")\n    acquired=float(owner.get("acquired_at") or 0)\n    age=max(0.0,time.time()-acquired) if acquired else 10**9\n\n    if _pid_alive(pid) and age<float(stale_seconds):\n        return False\n\n    try:\n        shutil.rmtree(path)\n        return True\n    except Exception:\n        return False\n\n@contextmanager\ndef acquire_canonical_writer_lease(\n    writer,\n    root=None,\n    timeout_seconds=None,\n    poll_seconds=0.002,\n    stale_seconds=30.0,\n):\n    policy=writer_policy(writer)\n    timeout=float(\n        policy.lease_timeout_seconds\n        if timeout_seconds is None\n        else timeout_seconds\n    )\n\n    path=lease_dir(root)\n    token=uuid.uuid4().hex\n    intent_token=None\n\n    if policy.writer=="FAST_LANE":\n        intent_token=publish_fast_intent(\n            root,\n            ttl_seconds=max(2.0,timeout+0.5),\n        )\n\n    started=time.perf_counter()\n    acquired=False\n\n    try:\n        while True:\n            if (\n                policy.writer!="FAST_LANE"\n                and fast_intent_active(root)\n            ):\n                if time.perf_counter()-started>=timeout:\n                    raise TimeoutError(\n                        "coverage yielded to fast lane beyond lease timeout"\n                    )\n                time.sleep(float(poll_seconds))\n                continue\n\n            try:\n                path.mkdir()\n                acquired=True\n                _atomic_json(\n                    _owner_path(path),\n                    {\n                        "writer":policy.writer,\n                        "pid":os.getpid(),\n                        "token":token,\n                        "acquired_at":time.time(),\n                    },\n                )\n                break\n            except FileExistsError:\n                _remove_stale_lease(path,stale_seconds)\n\n            if time.perf_counter()-started>=timeout:\n                raise TimeoutError(\n                    "canonical writer lease acquisition timed out"\n                )\n\n            time.sleep(float(poll_seconds))\n\n        waited=time.perf_counter()-started\n\n        if intent_token is not None:\n            clear_fast_intent(intent_token,root)\n            intent_token=None\n\n        yield CanonicalWriterLease(\n            policy.writer,\n            token,\n            waited,\n            str(path),\n            False,\n        )\n\n    finally:\n        if acquired:\n            owner=_read_owner(path)\n            if owner.get("token")==token:\n                try:\n                    shutil.rmtree(path)\n                except Exception:\n                    pass\n\n        if intent_token is not None:\n            clear_fast_intent(intent_token,root)\n\ndef verify_opc_038_atomic_cross_process_writer_lease():\n    with acquire_canonical_writer_lease(\n        "FAST_LANE",\n        timeout_seconds=1.0,\n    ) as lease:\n        return (\n            lease.writer=="FAST_LANE"\n            and lease.token\n            and lease.waited_seconds>=0\n            and not lease.execution_authority\n        )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_038_atomic_cross_process_writer_lease import verify_opc_038_atomic_cross_process_writer_lease\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_038_atomic_cross_process_writer_lease())\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-038 CERTIFICATION TEST")\n    print(" ATOMIC CROSS PROCESS WRITER LEASE")\n    print("="*80)\n\n    result=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] OPC-038 certified")\n    print("[DONE] OPC-038 CERTIFIED")\n'



def write_exact(path,text):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    tmp=path.with_suffix(
        path.suffix+".tmp"
    )
    tmp.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )
    os.replace(tmp,path)



def main():
    print("="*80)
    print(" OPC-038 INSTALLER")
    print(" ATOMIC CROSS PROCESS WRITER LEASE")
    print("="*80)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))


    up=importlib.import_module(
        "qseries_v2.oracle_pre_settlement_coverage."
        "opc_037_canonical_writer_arbiter_foundation"
    )
    if up.verify_opc_037_canonical_writer_arbiter_foundation() is not True:
        raise RuntimeError("Certified OPC-037 verification failed")
    print("[PASS] Certified OPC-037 upstream boundary verified")


    affected=(MOD,TEST,INIT)

    backups={
        path:(
            path.read_bytes()
            if path.exists()
            else None
        )
        for path in affected
    }

    try:
        write_exact(
            MOD,
            MODULE_SOURCE,
        )
        write_exact(
            TEST,
            TEST_SOURCE,
        )



        current=(
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        export="from .opc_038_atomic_cross_process_writer_lease import *"

        if export not in current:
            write_exact(
                INIT,
                current.rstrip()+"\n"+export+"\n",
            )

        compile(
            MOD.read_text(encoding="utf-8"),
            str(MOD),
            "exec",
        )

        compile(
            TEST.read_text(encoding="utf-8"),
            str(TEST),
            "exec",
        )

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )



    except Exception:
        for path,old in backups.items():
            if old is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(old)

        print(
            "[ROLLBACK] OPC-038 installation failed; "
            "affected files restored"
        )
        raise

    print(
        "[PASS] Wrote:",
        MOD.relative_to(ROOT),
    )
    print(
        "[PASS] Wrote:",
        TEST.name,
    )
    print(
        "[DONE] OPC-038 "
        "INSTALLATION AND CERTIFICATION COMPLETE"
    )

if __name__=="__main__":
    main()
