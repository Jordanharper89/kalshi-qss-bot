from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import pickle,time,uuid

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import (
    TABLE,database_url,ensure_postgresql_ingestion_schema
)

OPR_001_BUILD_ID="OPR-001"
OPR_001_REVISION="OPR_001_PERSISTENT_POSTGRESQL_QUEUE_SESSION_V1"

def _dump(x):return pickle.dumps(x,protocol=5)
def _load(x):return None if x is None else pickle.loads(bytes(x))

def _connection_error(exc):
    name=type(exc).__name__.lower()
    text=(name+" "+str(exc)).lower()
    return any(x in text for x in (
        "operationalerror","interfaceerror","connection","server closed",
        "connection reset","closed the connection","terminating connection"
    ))

@dataclass(frozen=True)
class PersistentQueueSubmission:
    request_id:str
    producer:str
    priority:int
    observation_count:int

class PersistentQueueSession:
    def __init__(self,root=None,autocommit=True):
        self.root=Path(root or Path.cwd()).resolve()
        self.autocommit=bool(autocommit)
        self.conn=None
        self.connect_count=0

    def open(self):
        if self.conn is not None and not getattr(self.conn,"closed",False):
            return self.conn
        import psycopg
        self.conn=psycopg.connect(database_url(self.root),autocommit=self.autocommit)
        self.connect_count+=1
        return self.conn

    def reconnect(self):
        self.close()
        return self.open()

    def close(self):
        if self.conn is not None:
            try:self.conn.close()
            except Exception:pass
        self.conn=None

    def execute(self,sql,params=(),fetchone=False,fetchall=False,retry_connection=True):
        for attempt in range(2 if retry_connection else 1):
            try:
                conn=self.open()
                with conn.cursor() as cur:
                    cur.execute(sql,params)
                    if fetchone:return cur.fetchone()
                    if fetchall:return cur.fetchall()
                    return cur.rowcount
            except Exception as exc:
                if attempt==0 and _connection_error(exc):
                    self.reconnect()
                    continue
                raise

    def backend_pid(self):
        row=self.execute("SELECT pg_backend_pid()",fetchone=True)
        return int(row[0])

    def submit(self,producer,priority,observations):
        items=tuple(observations)
        request_id=uuid.uuid4().hex
        self.execute(
            f"""INSERT INTO public.{TABLE}
                (request_id,producer,priority,observations,observation_count,status)
                VALUES(%s,%s,%s,%s,%s,'PENDING')""",
            (request_id,str(producer),int(priority),_dump(items),len(items)),
        )
        return PersistentQueueSubmission(request_id,str(producer),int(priority),len(items))

    def await_result(self,request_id,timeout_seconds=120.0,poll_seconds=0.025):
        deadline=time.monotonic()+float(timeout_seconds)
        while time.monotonic()<deadline:
            row=self.execute(
                f"""SELECT status,result_payload,last_error_type,last_error_message
                    FROM public.{TABLE} WHERE request_id=%s""",
                (str(request_id),),fetchone=True,
            )
            if row is None:
                raise RuntimeError("PostgreSQL ingestion request disappeared")
            status,payload,et,em=row
            if status=="DONE":return tuple(_load(payload) or ())
            if status=="FAILED":raise RuntimeError(f"PostgreSQL ingestion failed: {et}: {em}")
            time.sleep(float(poll_seconds))
        raise TimeoutError(f"PostgreSQL ingestion request timed out: {request_id}")

    def queue_counts(self):
        rows=self.execute(
            f"SELECT status,COUNT(*) FROM public.{TABLE} GROUP BY status ORDER BY status",
            fetchall=True,
        )
        return {str(s):int(c) for s,c in rows}

def verify_opr_001_persistent_postgresql_queue_session(root=None):
    return (
        OPR_001_BUILD_ID=="OPR-001"
        and callable(PersistentQueueSession)
        and PersistentQueueSubmission("r","p",1,2).observation_count==2
    )
