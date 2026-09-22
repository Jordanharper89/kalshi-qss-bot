from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os,pickle,sqlite3,time,uuid

OPH_006_BUILD_ID="OPH-006"
OPH_006_REVISION="OPH_006_DURABLE_CROSS_PROCESS_OBSERVATION_QUEUE_V1"

@dataclass(frozen=True)
class QueueSubmission:
    request_id:str
    writer_id:str
    priority:int
    observation_count:int
    execution_authority:bool=False

def queue_path(root=None):
    return Path(root or Path.cwd()).resolve()/"runtime_state"/"oracle_canonical_ingestion_queue.sqlite3"

def _connect(root=None):
    p=queue_path(root)
    p.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(str(p),timeout=30.0,isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS canonical_write_queue(
            request_id TEXT PRIMARY KEY,
            writer_id TEXT NOT NULL,
            priority INTEGER NOT NULL,
            created_at REAL NOT NULL,
            status TEXT NOT NULL,
            observations BLOB NOT NULL,
            result BLOB,
            error_type TEXT,
            error_message TEXT,
            claimed_by TEXT,
            claimed_at REAL,
            completed_at REAL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_canonical_write_queue_status_priority
        ON canonical_write_queue(status,priority DESC,created_at ASC)
    """)
    return conn

def initialize_queue(root=None):
    c=_connect(root); c.close(); return queue_path(root)

def submit_observation_batch(writer_id,priority,observations,root=None):
    items=tuple(observations)
    if not items: raise ValueError("empty observation batch")
    rid=uuid.uuid4().hex
    payload=sqlite3.Binary(pickle.dumps(items,protocol=pickle.HIGHEST_PROTOCOL))
    c=_connect(root)
    try:
        c.execute(
            "INSERT INTO canonical_write_queue(request_id,writer_id,priority,created_at,status,observations) VALUES(?,?,?,?,?,?)",
            (rid,str(writer_id),int(priority),time.time(),"PENDING",payload),
        )
    finally:
        c.close()
    return QueueSubmission(rid,str(writer_id),int(priority),len(items),False)

def claim_next_request(worker_id,root=None):
    c=_connect(root)
    try:
        c.execute("BEGIN IMMEDIATE")
        row=c.execute(
            "SELECT request_id,writer_id,priority,observations FROM canonical_write_queue WHERE status='PENDING' ORDER BY priority DESC,created_at ASC LIMIT 1"
        ).fetchone()
        if row is None:
            c.execute("COMMIT"); return None
        rid,writer,priority,blob=row
        updated=c.execute(
            "UPDATE canonical_write_queue SET status='CLAIMED',claimed_by=?,claimed_at=? WHERE request_id=? AND status='PENDING'",
            (str(worker_id),time.time(),rid),
        ).rowcount
        c.execute("COMMIT")
        if updated!=1: return None
        return rid,writer,int(priority),pickle.loads(blob)
    except Exception:
        try:c.execute("ROLLBACK")
        except Exception:pass
        raise
    finally:c.close()

def complete_request(request_id,result,root=None):
    c=_connect(root)
    try:
        c.execute(
            "UPDATE canonical_write_queue SET status='DONE',result=?,completed_at=? WHERE request_id=?",
            (sqlite3.Binary(pickle.dumps(result,protocol=pickle.HIGHEST_PROTOCOL)),time.time(),str(request_id)),
        )
    finally:c.close()

def fail_request(request_id,exc,root=None):
    c=_connect(root)
    try:
        c.execute(
            "UPDATE canonical_write_queue SET status='FAILED',error_type=?,error_message=?,completed_at=? WHERE request_id=?",
            (type(exc).__name__,str(exc),time.time(),str(request_id)),
        )
    finally:c.close()

def await_request(request_id,root=None,timeout_seconds=30.0,poll_seconds=0.005):
    deadline=time.time()+float(timeout_seconds)
    while time.time()<deadline:
        c=_connect(root)
        try:
            row=c.execute(
                "SELECT status,result,error_type,error_message FROM canonical_write_queue WHERE request_id=?",
                (str(request_id),),
            ).fetchone()
        finally:c.close()
        if row is None: raise RuntimeError("queue request disappeared")
        status,result,error_type,error_message=row
        if status=="DONE": return pickle.loads(result)
        if status=="FAILED": raise RuntimeError(f"canonical writer failed: {error_type}: {error_message}")
        time.sleep(float(poll_seconds))
    raise TimeoutError("canonical writer response timed out")

def queue_counts(root=None):
    c=_connect(root)
    try:
        rows=c.execute("SELECT status,COUNT(*) FROM canonical_write_queue GROUP BY status").fetchall()
        return {str(k):int(v) for k,v in rows}
    finally:c.close()

def verify_oph_006_durable_cross_process_observation_queue():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        initialize_queue(td)
        s=submit_observation_batch("fast_lane",100,("a","b"),td)
        claimed=claim_next_request("worker",td)
        complete_request(s.request_id,("ok",),td)
        result=await_request(s.request_id,td,1.0)
        return claimed[0]==s.request_id and claimed[1]=="fast_lane" and result==("ok",) and not s.execution_authority
