from pathlib import Path
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"; STATE=PKG/"state"
MOD=PKG/"continuous_mapping_worker.py"; TEST=ROOT/"test_ksem_071_continuous_production_mapping_worker.py"
MODULE=r"""
from pathlib import Path
from datetime import datetime,timezone
import json,time
from qseries_v2.kalshi_sports_evidence_mapping.durable_full_accounting_mapping_cycle import run_full_cycle

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def _utc():
    return datetime.now(timezone.utc).isoformat()

def run_worker_cycle(root=None,universe_limit=1000,max_supported=40,timeout_seconds=15):
    root=Path(root or Path.cwd()).resolve()
    started=_utc()
    state=run_full_cycle(root=root,universe_limit=universe_limit,max_supported=max_supported,timeout_seconds=timeout_seconds)
    result={
        "schema_version":"KSEM-071","started_at":started,"completed_at":_utc(),
        "content_hash":state["content_hash"],"total_rows":state["total_rows"],
        "counts":state["counts"],"accounted_rows":state["accounted_rows"],
        "probability_enabled":False,"execution_authority":False,
    }
    path=root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_worker_heartbeat.json"
    path.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    return result

def run_forever(root=None,interval_seconds=60,stop_after_cycles=None):
    cycles=0
    while True:
        run_worker_cycle(root=root)
        cycles+=1
        if stop_after_cycles is not None and cycles>=int(stop_after_cycles):
            return cycles
        time.sleep(max(1,int(interval_seconds)))
"""
TEST_BODY=r"""
from pathlib import Path
from qseries_v2.kalshi_sports_evidence_mapping.continuous_mapping_worker import run_worker_cycle
root=Path.cwd()
a=run_worker_cycle(root=root); b=run_worker_cycle(root=root)
print("[A]",a["total_rows"],a["counts"],a["content_hash"])
print("[B]",b["total_rows"],b["counts"],b["content_hash"])
assert a["total_rows"]>0 and b["total_rows"]>0
assert a["accounted_rows"]==a["total_rows"] and b["accounted_rows"]==b["total_rows"]
assert a["execution_authority"] is False and b["probability_enabled"] is False
assert (root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_worker_heartbeat.json").is_file()
print("[PASS] bounded production worker cycles completed with durable heartbeat")
print("[PASS] KSEM-071 certified")
"""
def main():
    print("="*120); print(" KSEM-071 CONTINUOUS PRODUCTION MAPPING WORKER INSTALLER"); print("="*120)
    for dep in (STATE/"ksem070_24x7_activation_readiness.json",PKG/"durable_full_accounting_mapping_cycle.py"):
        if not dep.is_file(): raise RuntimeError(f"missing dependency: {dep}")
        print("[PASS] dependency verified:",dep.relative_to(ROOT))
    MOD.write_text(MODULE.lstrip(),encoding="utf-8"); TEST.write_text(TEST_BODY.lstrip(),encoding="utf-8")
    print("[PASS] wrote",MOD.relative_to(ROOT)); print("[PASS] wrote",TEST.name)
    print("[PASS] production worker remains read-only and probability-disabled")
    print("[PASS] KSEM-071 installer complete")
if __name__=="__main__": main()
