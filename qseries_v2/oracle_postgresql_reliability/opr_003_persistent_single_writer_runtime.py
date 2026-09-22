from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import os,pickle,time,uuid

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import (
    TABLE,ensure_postgresql_ingestion_schema,database_url
)
from qseries_v2.oracle_production_hardening.oph_021_exclusive_postgresql_canonical_writer import (
    acquire_writer_lease,build_canonical_router,ADVISORY_LOCK_KEY
)
from qseries_v2.oracle_production_hardening.oph_024_postgresql_stale_claim_recovery import recover_stale_claims
from qseries_v2.oracle_production_hardening.oph_029_postgresql_routing_failure_classification import (
    classify_persistence_failure
)
from qseries_v2.oracle_production_hardening.oph_030_postgresql_writer_retry_telemetry import (
    TABLE as TELEMETRY_TABLE,ensure_retry_telemetry_schema
)

OPR_003_BUILD_ID="OPR-003"
OPR_003_REVISION="OPR_003_PERSISTENT_SINGLE_WRITER_RUNTIME_V1"

def _load(v):return None if v is None else pickle.loads(bytes(v))
def _dump(v):return pickle.dumps(v,protocol=5)

class WriterQueueSession:
    def __init__(self,root=None):
        self.root=Path(root or Path.cwd()).resolve()
        self.conn=None
        self.connect_count=0

    def open(self):
        if self.conn is not None and not getattr(self.conn,"closed",False):return self.conn
        import psycopg
        self.conn=psycopg.connect(database_url(self.root),autocommit=False)
        self.connect_count+=1
        return self.conn

    def close(self):
        if self.conn is not None:
            try:self.conn.close()
            except Exception:pass
        self.conn=None

    def reconnect(self):
        self.close();return self.open()

    def backend_pid(self):
        conn=self.open()
        with conn.cursor() as cur:
            cur.execute("SELECT pg_backend_pid()");row=cur.fetchone()
        conn.rollback()
        return int(row[0])

    def claim(self,worker):
        conn=self.open()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""WITH candidate AS(
                      SELECT request_id FROM public.{TABLE}
                      WHERE status='PENDING' AND next_attempt_at<=clock_timestamp()
                      ORDER BY priority DESC,admitted_at,request_id
                      FOR UPDATE SKIP LOCKED LIMIT 1)
                      UPDATE public.{TABLE} q SET status='IN_PROGRESS',worker_id=%s,
                      claimed_at=clock_timestamp(),attempts=q.attempts+1
                      FROM candidate c WHERE q.request_id=c.request_id
                      RETURNING q.request_id,q.producer,q.priority,q.observations,q.attempts""",
                    (str(worker),)
                )
                row=cur.fetchone()
            conn.commit()
            if row is None:return None
            return str(row[0]),str(row[1]),int(row[2]),tuple(_load(row[3])),int(row[4])
        except Exception:
            conn.rollback();raise

    def complete(self,request_id,result,producer,attempt,observation_count,elapsed_ms):
        conn=self.open()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""UPDATE public.{TABLE} SET status='DONE',
                        completed_at=clock_timestamp(),result_payload=%s,
                        last_error_type=NULL,last_error_message=NULL
                        WHERE request_id=%s AND status='IN_PROGRESS'""",
                    (_dump(tuple(result)),str(request_id))
                )
                if cur.rowcount!=1:raise RuntimeError("PostgreSQL ingestion completion lost queue ownership")
                cur.execute(
                    f"""INSERT INTO public.{TELEMETRY_TABLE}
                        (request_id,producer,phase,category,retryable,terminal,attempt,
                         observation_count,elapsed_ms,error_type,error_message)
                        VALUES(%s,%s,'COMMIT','COMMIT_SUCCESS',FALSE,FALSE,%s,%s,%s,NULL,NULL)""",
                    (str(request_id),str(producer),int(attempt),int(observation_count),float(elapsed_ms))
                )
            conn.commit()
        except Exception:
            conn.rollback();raise

    def fail(self,request_id,producer,attempt,observation_count,elapsed_ms,exc,classification,max_attempts=20):
        conn=self.open()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""INSERT INTO public.{TELEMETRY_TABLE}
                        (request_id,producer,phase,category,retryable,terminal,attempt,
                         observation_count,elapsed_ms,error_type,error_message)
                        VALUES(%s,%s,'FAILURE',%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        str(request_id),str(producer),str(classification.category),
                        bool(classification.retryable),bool(classification.terminal),
                        int(attempt),int(observation_count),float(elapsed_ms),
                        type(exc).__name__,str(exc)[:2000],
                    )
                )
                if classification.terminal or int(attempt)>=int(max_attempts):
                    cur.execute(
                        f"""UPDATE public.{TABLE} SET status='FAILED',
                            completed_at=clock_timestamp(),last_error_type=%s,last_error_message=%s
                            WHERE request_id=%s""",
                        (type(exc).__name__,str(exc),str(request_id))
                    )
                else:
                    delay=min(5000,25*(2**min(int(attempt),7)))
                    cur.execute(
                        f"""UPDATE public.{TABLE} SET status='PENDING',
                            worker_id=NULL,claimed_at=NULL,
                            next_attempt_at=clock_timestamp()+(%s*interval '1 millisecond'),
                            last_error_type=%s,last_error_message=%s
                            WHERE request_id=%s""",
                        (delay,type(exc).__name__,str(exc),str(request_id))
                    )
            conn.commit()
        except Exception:
            conn.rollback();raise

def run_persistent_writer_forever(root=None,progress=None,idle_sleep_seconds=0.005):
    root=Path(root or Path.cwd()).resolve()
    ensure_postgresql_ingestion_schema(root)
    ensure_retry_telemetry_schema(root)
    recovered=recover_stale_claims(root)
    lease=acquire_writer_lease(root)
    queue=WriterQueueSession(root);queue.open()
    worker=f"opr003:{os.getpid()}:{uuid.uuid4().hex[:8]}"
    router=build_canonical_router(root)

    if progress:
        progress(f"[OPR-003 RECOVERY] stale_claims_recovered={len(recovered)}")
        progress(f"[OPR-003 WRITER] worker={worker} lease=ACQUIRED queue_backend_pid={queue.backend_pid()}")

    try:
        while True:
            try:
                item=queue.claim(worker)
            except Exception as exc:
                if progress:progress(f"[OPR-003 QUEUE RECONNECT] type={type(exc).__name__} message={exc}")
                queue.reconnect();time.sleep(0.05);continue
            if item is None:
                time.sleep(float(idle_sleep_seconds));continue

            request_id,producer,priority,observations,attempt=item
            started=time.perf_counter()
            try:
                result=tuple(router.route_batch(tuple(observations),datetime.now(timezone.utc)))
                elapsed=(time.perf_counter()-started)*1000.0
                queue.complete(request_id,result,producer,attempt,len(observations),elapsed)
                if progress:
                    progress(
                        f"[OPR-003 COMMIT] request={request_id[:10]} producer={producer} "
                        f"priority={priority} observations={len(observations)} attempt={attempt} elapsed_ms={elapsed:.2f}"
                    )
            except Exception as exc:
                elapsed=(time.perf_counter()-started)*1000.0
                c=classify_persistence_failure(exc)
                try:queue.fail(request_id,producer,attempt,len(observations),elapsed,exc,c)
                except Exception:
                    queue.reconnect()
                    raise
                if progress:
                    progress(
                        f"[OPR-003 RETRY] request={request_id[:10]} producer={producer} "
                        f"category={c.category} attempt={attempt} type={type(exc).__name__}"
                    )
                router=build_canonical_router(root)

    except KeyboardInterrupt:
        return 0
    finally:
        queue.close()
        try:
            with lease.cursor() as cur:cur.execute("SELECT pg_advisory_unlock(%s)",(ADVISORY_LOCK_KEY,))
        finally:lease.close()

def verify_opr_003_persistent_single_writer_runtime(root=None):
    return OPR_003_BUILD_ID=="OPR-003" and callable(run_persistent_writer_forever)
