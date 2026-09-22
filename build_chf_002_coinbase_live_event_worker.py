from pathlib import Path
import py_compile
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_coinbase_high_frequency"
assert (PKG/"chf_001_foundation.py").exists(),"CHF-001 required"
BODY=r"""
import json,time,threading
from datetime import datetime,timezone
from pathlib import Path
from .chf_001_foundation import CHFConfig,subscription_messages,runtime_dir

REVISION="CHF-002"

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def _ws_module():
    try:
        import websocket
        return websocket
    except Exception as e:
        raise RuntimeError("websocket-client is required: python -m pip install websocket-client") from e

class CoinbaseHFWorker:
    def __init__(self,root:Path,cfg=CHFConfig()):
        self.root=Path(root); self.cfg=cfg; self.stop_event=threading.Event()
        self.dir=runtime_dir(self.root); self.raw=self.dir/"raw_events.jsonl"
        self.state=self.dir/"worker_state.json"

    def _append(self,obj):
        line=json.dumps(obj,separators=(",",":"),default=str)
        with self.raw.open("a",encoding="utf-8",buffering=1) as f:
            f.write(line+"\n")

    def _state(self,**kw):
        cur={}
        if self.state.exists():
            try: cur=json.loads(self.state.read_text(encoding="utf-8"))
            except Exception: pass
        cur.update(kw); cur["updated_at"]=utcnow()
        tmp=self.state.with_suffix(".tmp"); tmp.write_text(json.dumps(cur,indent=2),encoding="utf-8"); tmp.replace(self.state)

    def run(self,max_seconds=None):
        websocket=_ws_module(); started=time.monotonic(); backoff=self.cfg.reconnect_min_s
        self._state(status="STARTING",revision=REVISION,products=list(self.cfg.products))
        while not self.stop_event.is_set():
            if max_seconds is not None and time.monotonic()-started>=max_seconds: break
            ws=None
            try:
                ws=websocket.create_connection(self.cfg.ws_url,timeout=self.cfg.recv_timeout_s,enable_multithread=True)
                for m in subscription_messages(self.cfg): ws.send(json.dumps(m))
                self._state(status="RUNNING",connected_at=utcnow())
                backoff=self.cfg.reconnect_min_s
                while not self.stop_event.is_set():
                    if max_seconds is not None and time.monotonic()-started>=max_seconds: break
                    raw=ws.recv()
                    if not raw: continue
                    try: msg=json.loads(raw)
                    except Exception: continue
                    self._append({"received_at":utcnow(),"message":msg})
                if max_seconds is not None and time.monotonic()-started>=max_seconds: break
            except Exception as e:
                self._state(status="RECONNECTING",last_error=repr(e))
                time.sleep(backoff); backoff=min(self.cfg.reconnect_max_s,backoff*2)
            finally:
                if ws is not None:
                    try: ws.close()
                    except Exception: pass
        self._state(status="STOPPED")
        return self.raw

    def stop(self): self.stop_event.set()
"""
TEST=r"""
from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_002_live_event_worker import CoinbaseHFWorker
w=CoinbaseHFWorker(Path.cwd())
assert w.raw.name=="raw_events.jsonl"
assert w.state.name=="worker_state.json"
print("[RAW_JOURNAL]",w.raw)
print("[STATE]",w.state)
print("[PASS] CHF-002 live event worker interface certified")
"""
(PKG/"chf_002_live_event_worker.py").write_text(BODY.lstrip(),encoding="utf-8")
(ROOT/"test_chf_002_coinbase_live_event_worker.py").write_text(TEST.lstrip(),encoding="utf-8")
py_compile.compile(str(PKG/"chf_002_live_event_worker.py"),doraise=True)
py_compile.compile(str(ROOT/"test_chf_002_coinbase_live_event_worker.py"),doraise=True)
print("[PASS] wrote CHF-002 worker + test")
print("[PASS] public market-data only; no order/user channel")
print("[PASS] execution_authority=FALSE")
