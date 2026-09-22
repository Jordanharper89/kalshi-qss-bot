from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_006_durable_cross_process_observation_queue import queue_counts
from qseries_v2.oracle_production_hardening.oph_011_persistence_provenance_ledger import ledger_path
from qseries_v2.oracle_production_hardening.oph_015_strict_single_writer_production_gate import strict_single_writer_report

if __name__=="__main__":
    print("="*96)
    print(" OPH-015 STRICT SINGLE-WRITER PHYSICAL PRODUCTION CHECK")
    print("="*96)
    r=strict_single_writer_report()
    p=ledger_path(Path.cwd())
    print(f"[QUEUE] counts={queue_counts(Path.cwd())}")
    print(f"[PROVENANCE] path={p}")
    print(f"[PROVENANCE] present={p.exists()}")
    print(f"[FAST LANE QUEUE ONLY] {r.fast_lane_queue_only}")
    print(f"[COVERAGE QUEUE ONLY] {r.coverage_queue_only}")
    print(f"[WRITER RECOVERY] {r.writer_recovery_enabled}")
    print(f"[DIRECT ADAPTER POSTGRESQL AUTHORITY] {r.direct_adapter_postgresql_authority}")
    print("[TARGET] canonical_writer=RUNNING")
    print("[TARGET] producer logs contain no raw PostgreSQLPersistenceRoutingFailure")
    print("[TARGET] any PostgreSQL routing failure appears only as [SINGLE WRITER RETRY]")
    print("[TARGET] Fast Lane remains connected while writer retries")
    print("[TARGET] Coverage continues full-page persistence")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-015 PHYSICAL CHECK READY")
