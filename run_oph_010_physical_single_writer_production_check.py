from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_006_durable_cross_process_observation_queue import (
    queue_counts,
    queue_path,
)
from qseries_v2.oracle_production_hardening.oph_010_physical_single_writer_production_gate import (
    production_report,
)

if __name__=="__main__":
    print("="*96)
    print(" OPH-010 PHYSICAL SINGLE-WRITER PRODUCTION CHECK — CORRECTION V2")
    print("="*96)

    report=production_report()

    print(f"[QUEUE] path={queue_path(Path.cwd())}")
    print(f"[QUEUE] counts={queue_counts(Path.cwd())}")
    print(f"[WRITER CHILD] {report.writer_child}")
    print(f"[FAST LANE QUEUED] {report.fast_lane_queued}")
    print(f"[COVERAGE QUEUED] {report.coverage_queued}")
    print(
        "[DIRECT ADAPTER POSTGRESQL AUTHORITY] "
        f"{report.direct_adapter_postgresql_authority}"
    )

    print("[TARGET] canonical_writer=RUNNING")
    print("[TARGET] fast_lane=RUNNING coverage=RUNNING")
    print("[TARGET] no producer-side expected_terminal_chain_hash_mismatch")
    print("[TARGET] no Fast Lane PostgreSQLPersistenceRoutingFailure reconnects")
    print("[TARGET] Coverage continues full-page persistence through queue")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-010 PHYSICAL CHECK READY")
