from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_017_durable_coverage_runtime_state.py"
TEST=ROOT/"test_opc_017_durable_coverage_runtime_state.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import asdict, dataclass\nfrom datetime import datetime, timezone\nfrom hashlib import sha256\nfrom pathlib import Path\nimport json, os\n\nSTATE_NAME="oracle_pre_settlement_coverage_runtime_state.json"\n\n@dataclass(frozen=True)\nclass DurableCoverageRuntimeState:\n    cycles_completed:int=0\n    markets_planned:int=0\n    markets_persisted:int=0\n    transient_failures:int=0\n    consecutive_failures:int=0\n    last_cycle_status:str="NEVER_RUN"\n    last_cycle_at:str=""\n    state_hash:str=""\n\ndef state_path(root=None):\n    return Path(root or Path.cwd()).resolve()/"runtime_state"/STATE_NAME\n\ndef _hash_payload(payload):\n    clean=dict(payload)\n    clean["state_hash"]=""\n    return sha256(json.dumps(clean,sort_keys=True,separators=(",",":")).encode()).hexdigest()\n\ndef load_coverage_runtime_state(root=None):\n    p=state_path(root)\n    if not p.exists():\n        return DurableCoverageRuntimeState()\n    data=json.loads(p.read_text(encoding="utf-8"))\n    return DurableCoverageRuntimeState(**data)\n\ndef save_coverage_runtime_state(state,root=None):\n    p=state_path(root)\n    p.parent.mkdir(parents=True,exist_ok=True)\n    payload=asdict(state)\n    payload["state_hash"]=_hash_payload(payload)\n    tmp=p.with_suffix(".json.tmp")\n    tmp.write_text(json.dumps(payload,sort_keys=True,indent=2),encoding="utf-8")\n    os.replace(tmp,p)\n    return DurableCoverageRuntimeState(**payload)\n\ndef advance_coverage_runtime_state(state,*,planned,persisted,status,transient_failure=False,at=None):\n    at=at or datetime.now(timezone.utc).isoformat()\n    failed=status!="SUCCESS"\n    return DurableCoverageRuntimeState(\n        cycles_completed=state.cycles_completed+1,\n        markets_planned=state.markets_planned+int(planned),\n        markets_persisted=state.markets_persisted+int(persisted),\n        transient_failures=state.transient_failures+(1 if transient_failure else 0),\n        consecutive_failures=(state.consecutive_failures+1 if failed else 0),\n        last_cycle_status=str(status),\n        last_cycle_at=str(at),\n        state_hash="",\n    )\n\ndef verify_opc_017_durable_coverage_runtime_state():\n    s=DurableCoverageRuntimeState()\n    n=advance_coverage_runtime_state(s,planned=10,persisted=10,status="SUCCESS",at="2026-01-01T00:00:00+00:00")\n    return n.cycles_completed==1 and n.markets_persisted==10 and n.consecutive_failures==0\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_017_durable_coverage_runtime_state import verify_opc_017_durable_coverage_runtime_state\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_017_durable_coverage_runtime_state())\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OPC-017 CERTIFICATION TEST")\n    print(" DURABLE COVERAGE RUNTIME STATE")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-017 certified")\n    print("[DONE] OPC-017 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OPC-017 INSTALLER")
    print(" DURABLE COVERAGE RUNTIME STATE")
    print("="*72)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_016_physical_coverage_cycle_adapter")
    if up.verify_opc_016_physical_coverage_cycle_adapter() is not True:
        raise RuntimeError("Certified OPC-016 verification failed")
    print("[PASS] Certified OPC-016 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export_line="from .opc_017_durable_coverage_runtime_state import *"
        if export_line not in current:
            write_exact(INIT,current.rstrip()+"\n"+export_line+"\n")

        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

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
        print("[ROLLBACK] OPC-017 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OPC-017 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
