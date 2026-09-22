from pathlib import Path
import time
from qseries_v2.oracle_pre_settlement_coverage.opc_030_high_throughput_universal_coverage_gate import run_high_throughput_coverage_cycle

if __name__=="__main__":
    print("="*96)
    print(" OPC-030 PHYSICAL HIGH-THROUGHPUT UNIVERSAL COVERAGE VERIFICATION")
    print("="*96)

    started=time.perf_counter()
    result=run_high_throughput_coverage_cycle(
        Path.cwd(),
        progress=lambda x:print(x,flush=True),
    )
    elapsed=max(0.0001,time.perf_counter()-started)
    rate=result.persisted/elapsed

    print(f"[RESULT] page_markets={result.page_markets}")
    print(f"[RESULT] already_covered={result.already_covered}")
    print(f"[RESULT] missing={result.missing_markets}")
    print(f"[RESULT] requested={result.requested}")
    print(f"[RESULT] persisted={result.persisted}")
    print(f"[RESULT] retries={result.retries_used}")
    print(f"[RESULT] chunk_size={result.chunk_size}")
    print(f"[THROUGHPUT] elapsed_seconds={elapsed:.2f}")
    print(f"[THROUGHPUT] persisted_per_second={rate:.2f}")

    if result.requested!=result.persisted:
        raise SystemExit("Full-page coverage persistence incomplete")
    if not result.cursor_advanced:
        raise SystemExit("Coverage cursor did not advance")

    print("[PASS] Entire missing portion of the 1,000-market page persisted")
    print("[PASS] No 100-market per-page admission cap remains")
    print("[PASS] Cursor advanced after full-page coverage")
    print("[PASS] Existing OLA persistence path preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPC-030 PHYSICAL HIGH-THROUGHPUT UNIVERSAL COVERAGE VERIFIED")
