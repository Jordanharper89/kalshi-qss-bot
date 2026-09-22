from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os,pickle,time,uuid

OPH_019_BUILD_ID="OPH-019"
OPH_019_REVISION="OPH_019_POSTGRESQL_UNIVERSAL_INGESTION_QUEUE_V1"
TABLE="oracle_universal_ingestion_queue"

@dataclass(frozen=True)
class PostgreSQLQueueSubmission:
    request_id:str
    producer:str
    priority:int
    observation_count:int

def database_url(root=None):
    root=Path(root or Path.cwd()).resolve()
    keys=("ORACLE_POSTGRESQL_URL","ORACLE_DATABASE_URL","DATABASE_URL","POSTGRES_URL")
    for key in keys:
        value=os.environ.get(key)
        if value:return value
    env=root/".env"
    if env.exists():
        for raw in env.read_text(encoding="utf-8",errors="ignore").splitlines():
            line=raw.strip()
            if not line or line.startswith("#") or "=" not in line:continue
            key,value=line.split("=",1)
            if key.strip() in keys:
                value=value.strip().strip('"').strip("'")
                if value:return value
    raise RuntimeError("PostgreSQL URL not configured")

def connect(root=None,autocommit=False,connect_timeout_seconds=5.0):
    import psycopg
    timeout=max(1,int(float(connect_timeout_seconds)))
    return psycopg.connect(database_url(root),autocommit=autocommit,connect_timeout=timeout)

def ensure_postgresql_ingestion_schema(root=None):
    ddl=f"""
    CREATE TABLE IF NOT EXISTS public.{TABLE}(
      request_id TEXT PRIMARY KEY,
      producer TEXT NOT NULL,
      priority INTEGER NOT NULL,
      observations BYTEA NOT NULL,
      observation_count INTEGER NOT NULL CHECK(observation_count>=0),
      status TEXT NOT NULL CHECK(status IN ('PENDING','IN_PROGRESS','DONE','FAILED')),
      admitted_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      claimed_at TIMESTAMPTZ,
      worker_id TEXT,
      attempts INTEGER NOT NULL DEFAULT 0,
      completed_at TIMESTAMPTZ,
      result_payload BYTEA,
      last_error_type TEXT,
      last_error_message TEXT
    );
    CREATE INDEX IF NOT EXISTS oracle_universal_ingestion_queue_claim_idx
      ON public.{TABLE}(status,priority DESC,admitted_at,request_id);
    CREATE INDEX IF NOT EXISTS oracle_universal_ingestion_queue_next_idx
      ON public.{TABLE}(next_attempt_at) WHERE status='PENDING';
    """
    with connect(root,autocommit=True) as conn:
        with conn.cursor() as cur:cur.execute(ddl)
    return True

def _dump(x):return pickle.dumps(x,protocol=5)
def _load(x):return None if x is None else pickle.loads(bytes(x))

def submit_observation_batch(writer_id,priority,observations,root=None):
    items=tuple(observations);request_id=uuid.uuid4().hex
    ensure_postgresql_ingestion_schema(root)
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""INSERT INTO public.{TABLE}
              (request_id,producer,priority,observations,observation_count,status)
              VALUES(%s,%s,%s,%s,%s,'PENDING')""",
              (request_id,str(writer_id),int(priority),_dump(items),len(items)))
        conn.commit()
    return PostgreSQLQueueSubmission(request_id,str(writer_id),int(priority),len(items))

def claim_next_request(worker_id,root=None):
    ensure_postgresql_ingestion_schema(root)
    sql=f"""WITH candidate AS(
      SELECT request_id FROM public.{TABLE}
      WHERE status='PENDING' AND next_attempt_at<=clock_timestamp()
      ORDER BY priority DESC,admitted_at,request_id
      FOR UPDATE SKIP LOCKED LIMIT 1)
      UPDATE public.{TABLE} q SET status='IN_PROGRESS',worker_id=%s,
      claimed_at=clock_timestamp(),attempts=q.attempts+1
      FROM candidate c WHERE q.request_id=c.request_id
      RETURNING q.request_id,q.producer,q.priority,q.observations"""
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(sql,(str(worker_id),));row=cur.fetchone()
        conn.commit()
    if row is None:return None
    return row[0],row[1],int(row[2]),tuple(_load(row[3]))

def complete_request(request_id,result,root=None):
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""UPDATE public.{TABLE} SET status='DONE',
              completed_at=clock_timestamp(),result_payload=%s,
              last_error_type=NULL,last_error_message=NULL
              WHERE request_id=%s AND status='IN_PROGRESS'""",
              (_dump(tuple(result)),str(request_id)))
            if cur.rowcount!=1:raise RuntimeError("PostgreSQL ingestion completion lost queue ownership")
        conn.commit()
    return True

def fail_request(request_id,exc,root=None,max_attempts=20):
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT attempts FROM public.{TABLE} WHERE request_id=%s FOR UPDATE",(str(request_id),))
            row=cur.fetchone()
            if row is None:raise RuntimeError("PostgreSQL ingestion request missing")
            attempts=int(row[0])
            if attempts>=int(max_attempts):
                cur.execute(f"""UPDATE public.{TABLE} SET status='FAILED',
                  completed_at=clock_timestamp(),last_error_type=%s,last_error_message=%s
                  WHERE request_id=%s""",(type(exc).__name__,str(exc),str(request_id)))
            else:
                delay=min(5000,25*(2**min(attempts,7)))
                cur.execute(f"""UPDATE public.{TABLE} SET status='PENDING',
                  worker_id=NULL,claimed_at=NULL,
                  next_attempt_at=clock_timestamp()+(%s*interval '1 millisecond'),
                  last_error_type=%s,last_error_message=%s WHERE request_id=%s""",
                  (delay,type(exc).__name__,str(exc),str(request_id)))
        conn.commit()
    return True

def await_request(request_id,root=None,timeout_seconds=120.0,poll_seconds=0.05):
    timeout=float(timeout_seconds)
    if timeout<=0:raise ValueError("timeout_seconds must be > 0")
    poll=max(0.01,float(poll_seconds))
    deadline=time.monotonic()+timeout
    last_connect_error=None
    while time.monotonic()<deadline:
        remaining=max(0.0,deadline-time.monotonic())
        try:
            with connect(root,connect_timeout_seconds=min(5.0,max(1.0,remaining))) as conn:
                with conn.cursor() as cur:
                    while time.monotonic()<deadline:
                        cur.execute(f"""SELECT status,result_payload,last_error_type,last_error_message
                          FROM public.{TABLE} WHERE request_id=%s""",(str(request_id),))
                        row=cur.fetchone()
                        if row is None:raise RuntimeError("PostgreSQL ingestion request disappeared")
                        status,payload,et,em=row
                        if status=="DONE":return tuple(_load(payload) or ())
                        if status=="FAILED":raise RuntimeError(f"PostgreSQL ingestion failed: {et}: {em}")
                        time.sleep(poll)
            last_connect_error=None
        except RuntimeError:
            raise
        except Exception as exc:
            last_connect_error=exc
            if time.monotonic()>=deadline:break
            time.sleep(min(0.25,max(0.01,deadline-time.monotonic())))
    suffix="" if last_connect_error is None else f"; last database error: {type(last_connect_error).__name__}: {last_connect_error}"
    raise TimeoutError(f"PostgreSQL ingestion request timed out: {request_id}{suffix}")

def queue_counts(root=None):
    ensure_postgresql_ingestion_schema(root)
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT status,COUNT(*) FROM public.{TABLE} GROUP BY status ORDER BY status")
            return {str(s):int(c) for s,c in cur.fetchall()}

def verify_oph_019_postgresql_universal_ingestion_queue():
    return TABLE=="oracle_universal_ingestion_queue" and "POSTGRESQL" in OPH_019_REVISION
