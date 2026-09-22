from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve(); PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_003_shared_durable_state_persistence_runtime.py"; TEST=ROOT/"test_oph_003_shared_durable_state_persistence_runtime.py"; INIT=PKG/"__init__.py"
MODULE='from dataclasses import dataclass\nfrom hashlib import sha256\nfrom pathlib import Path\nimport json,os,time,uuid\n\n@dataclass(frozen=True)\nclass DurableStateWriteResult:\n    path:str; state_hash:str; attempts:int; execution_authority:bool=False\n\ndef deterministic_state_hash(payload):\n    return sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\n\ndef atomic_write_json(path,payload,retries=8,base_delay_seconds=0.01):\n    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)\n    h=deterministic_state_hash(payload); body=dict(payload); body["_state_hash"]=h\n    last=None\n    for attempt in range(1,int(retries)+1):\n        temp=path.with_name(path.name+f".{os.getpid()}.{uuid.uuid4().hex}.tmp")\n        try:\n            temp.write_text(json.dumps(body,sort_keys=True,separators=(",",":"),default=str),encoding="utf-8",newline="\\n")\n            os.replace(temp,path)\n            return DurableStateWriteResult(str(path),h,attempt,False)\n        except (PermissionError,OSError) as exc:\n            last=exc\n            try: temp.unlink(missing_ok=True)\n            except Exception: pass\n            if attempt<int(retries): time.sleep(min(.5,float(base_delay_seconds)*(2**(attempt-1))))\n    raise last if last else RuntimeError("durable state write failed")\n\ndef read_json_state(path):\n    path=Path(path)\n    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None\n\ndef verify_oph_003_shared_durable_state_persistence_runtime():\n    import tempfile\n    with tempfile.TemporaryDirectory() as td:\n        p=Path(td)/"state.json"; r=atomic_write_json(p,{"value":7}); x=read_json_state(p)\n        return x["value"]==7 and x["_state_hash"]==r.state_hash and not r.execution_authority\n'; TESTSRC='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_003_shared_durable_state_persistence_runtime import verify_oph_003_shared_durable_state_persistence_runtime\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oph_003_shared_durable_state_persistence_runtime())\nif __name__=="__main__":\n    print("="*80); print(" OPH-003 CERTIFICATION TEST"); print(" SHARED DURABLE STATE PERSISTENCE RUNTIME"); print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OPH-003 certified"); print("[DONE] OPH-003 CERTIFIED")\n'
def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
    print("="*80); print(" OPH-003 INSTALLER"); print(" SHARED DURABLE STATE PERSISTENCE RUNTIME"); print("="*80); print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT)); up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_002_priority_observation_ingestion_queue")
    if up.verify_oph_002_priority_observation_ingestion_queue() is not True: raise RuntimeError("OPH-002 verification failed")
    print("[PASS] Certified OPH-002 upstream boundary verified")
    affected=(MOD,TEST,INIT); old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE); write_exact(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; ex="from .oph_003_shared_durable_state_persistence_runtime import *"
        if ex not in cur: write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] OPH-003 installation failed"); raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT)); print("[PASS] Wrote:",TEST.name); print("[DONE] OPH-003 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
