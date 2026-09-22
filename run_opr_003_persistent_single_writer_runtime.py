from pathlib import Path
import time
from qseries_v2.oracle_postgresql_reliability.opr_003_persistent_single_writer_runtime import run_persistent_writer_forever

ORH_002_BUILD_ID="ORH-002"
BACKOFF_SECONDS=(1.0,2.0,5.0,10.0,30.0)

def main():
    print("="*96,flush=True)
    print(" OPR-003 PERSISTENT POSTGRESQL SINGLE-WRITER RUNTIME — ORH-002 RESILIENT",flush=True)
    print("="*96,flush=True)
    failures=0
    while True:
        try:
            return run_persistent_writer_forever(Path.cwd(),lambda x:print(x,flush=True))
        except KeyboardInterrupt:
            return 0
        except Exception as exc:
            failures+=1
            delay=BACKOFF_SECONDS[min(failures-1,len(BACKOFF_SECONDS)-1)]
            print(f"[ORH-002 WRITER RECOVERY] status=DEGRADED failure={failures} type={type(exc).__name__} retry_in={delay:.1f}s execution_authority=FALSE",flush=True)
            time.sleep(delay)

if __name__=="__main__":
    raise SystemExit(main())
