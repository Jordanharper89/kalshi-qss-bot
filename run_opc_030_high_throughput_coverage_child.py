from pathlib import Path
import time
from qseries_v2.oracle_pre_settlement_coverage.opc_030_high_throughput_universal_coverage_gate import run_high_throughput_coverage_cycle

def main():
    print("="*88,flush=True)
    print(" OPC-030 HIGH-THROUGHPUT UNIVERSAL PRE-SETTLEMENT COVERAGE CHILD",flush=True)
    print(" FULL PAGE ADMISSION + CHUNKED PERSISTENCE + ADAPTIVE BACKPRESSURE",flush=True)
    print("="*88,flush=True)

    retries=0
    failures=0

    while True:
        try:
            r=run_high_throughput_coverage_cycle(
                Path.cwd(),
                progress=lambda x:print(x,flush=True),
                recent_retries=retries,
                recent_failures=failures,
            )
            retries=r.retries_used
            failures=0

            if r.requested!=r.persisted:
                failures+=1

            print(
                f"[COVERAGE SUPERVISOR] status={'SUCCESS' if r.requested==r.persisted else 'PARTIAL'} "
                f"page_markets={r.page_markets} requested={r.requested} "
                f"persisted={r.persisted} retries={r.retries_used} "
                f"chunk_size={r.chunk_size} execution_authority=FALSE",
                flush=True,
            )
        except KeyboardInterrupt:
            return 0
        except Exception as exc:
            failures+=1
            print(
                f"[COVERAGE SUPERVISOR] failure type={type(exc).__name__} "
                f"failures={failures} action=retry_next_cycle",
                flush=True,
            )
            time.sleep(min(5.0,0.5*(2**min(failures,3))))

if __name__=="__main__":
    raise SystemExit(main())
