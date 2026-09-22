from __future__ import annotations
from pathlib import Path
import json,os,time,uuid
from qseries_v2.oracle_production_hardening.oph_029_postgresql_routing_failure_classification import classify_persistence_failure
ORH_009_BUILD_ID="ORH-009";STATE_NAME="oracle_persistence_pressure_telemetry.json"
def _load(path):
    try:return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:return {"total":0,"categories":{},"last_failure":None,"execution_authority":False}
def record_persistence_failure(root,producer,exc):
    root=Path(root or Path.cwd()).resolve();p=root/"runtime_state"/STATE_NAME;p.parent.mkdir(parents=True,exist_ok=True)
    c=classify_persistence_failure(exc);s=_load(p);s["total"]=int(s.get("total",0))+1
    cats=dict(s.get("categories") or {});cats[c.category]=int(cats.get(c.category,0))+1;s["categories"]=cats
    text=(type(exc).__name__+" "+str(exc)).lower()
    reason=("DATABASE_RECOVERY" if "recovery mode" in text else "TIMEOUT" if "timeout" in text or "timed out" in text else "CONNECTION" if "connection" in text else "QUEUE_OR_COMMIT" if "not committed" in text else c.category)
    s["last_failure"]={"ts":time.time(),"producer":str(producer),"category":c.category,"reason":reason,"type":type(exc).__name__,"retryable":c.retryable};s["execution_authority"]=False
    tmp=p.with_name(p.name+f".{os.getpid()}.{uuid.uuid4().hex}.tmp");tmp.write_text(json.dumps(s,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,p);return s
def read_persistence_pressure(root=None):
    root=Path(root or Path.cwd()).resolve();return _load(root/"runtime_state"/STATE_NAME)
def verify_orh_009_persistence_pressure_telemetry():return callable(record_persistence_failure) and callable(read_persistence_pressure)
