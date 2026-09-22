from pathlib import Path
ROOT=Path.cwd(); TEST=ROOT/"test_ksem_078_native_launcher_physical_child_start_gate.py"
TEST_BODY=r"""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,json,time
root=Path.cwd()
spec=importlib.util.spec_from_file_location("oracle_live_ksem078",root/"run_oracle_LIVE.py")
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
assert mod.CHILDREN.get("ksem_mapping")=="run_ksem_live_mapping.py"
hb=root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_worker_heartbeat.json"
before=json.loads(hb.read_text()) if hb.is_file() else {}
before_completed=before.get("completed_at")
proc=mod._start(root,mod.CHILDREN["ksem_mapping"])
try:
    deadline=time.time()+90
    fresh=None
    while time.time()<deadline:
        if proc.poll() is not None: raise RuntimeError(f"KSEM_CHILD_EXITED code={proc.returncode}")
        if hb.is_file():
            cur=json.loads(hb.read_text())
            if cur.get("completed_at") and cur.get("completed_at")!=before_completed:
                fresh=cur; break
        time.sleep(1)
    assert fresh is not None,"native launcher child did not advance KSEM heartbeat within 90s"
    print("[HEARTBEAT]",fresh)
    assert fresh["accounted_rows"]==fresh["total_rows"]>0
    assert fresh["execution_authority"] is False and fresh["probability_enabled"] is False
finally:
    proc.terminate()
    try: proc.wait(timeout=10)
    except Exception: proc.kill()
print("[PASS] run_oracle_LIVE._start physically launched KSEM child and durable state advanced")
print("[PASS] KSEM-078 certified")
"""
def main():
    print("="*120); print(" KSEM-078 NATIVE LAUNCHER PHYSICAL CHILD START GATE INSTALLER"); print("="*120)
    if not (ROOT/"run_oracle_LIVE.py").is_file(): raise RuntimeError("launcher missing")
    if not (ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem077_native_launcher_cutover.json").is_file():
        raise RuntimeError("KSEM-077 cutover state missing")
    TEST.write_text(TEST_BODY.lstrip(),encoding="utf-8")
    print("[PASS] wrote",TEST.name)
    print("[PASS] gate uses production launcher's actual _start primitive")
    print("[PASS] KSEM-078 installer complete")
if __name__=="__main__": main()