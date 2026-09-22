import json,time,threading
from pathlib import Path
from .chf_001_foundation import runtime_dir
from .chf_003_canonical_event_normalizer import normalize_message
from .chf_004_multihorizon_windows import materialize

REVISION="CHF-006"

class ContinuousWindowWorker:
    def __init__(self,root:Path):
        self.root=Path(root)
        self.dir=runtime_dir(self.root)
        self.raw=self.dir/"raw_events.jsonl"
        self.canon=self.dir/"canonical_events.jsonl"
        self.checkpoint=self.dir/"continuous_window_checkpoint.json"
        self.stop_event=threading.Event()

    def _load_offset(self):
        if not self.checkpoint.exists():
            return 0
        try:
            return int(json.loads(self.checkpoint.read_text(encoding="utf-8")).get("raw_offset",0))
        except Exception:
            return 0

    def _save_offset(self,offset):
        tmp=self.checkpoint.with_suffix(".tmp")
        tmp.write_text(json.dumps({"revision":REVISION,"raw_offset":offset},indent=2),encoding="utf-8")
        tmp.replace(self.checkpoint)

    def cycle(self):
        if not self.raw.exists():
            return {"raw_lines":0,"canonical_events":0,"window_rows":0}
        offset=self._load_offset()
        if offset>self.raw.stat().st_size:
            offset=0
        raw_lines=0
        canon_n=0
        with self.raw.open("r",encoding="utf-8") as src, self.canon.open("a",encoding="utf-8",buffering=1) as dst:
            src.seek(offset)
            for line in src:
                raw_lines+=1
                try:
                    env=json.loads(line)
                except Exception:
                    continue
                for item in normalize_message(env):
                    dst.write(json.dumps(item,separators=(",",":"),default=str)+"\n")
                    canon_n+=1
            offset=src.tell()
        self._save_offset(offset)
        win_n=materialize(self.root) if self.canon.exists() else 0
        return {"raw_lines":raw_lines,"canonical_events":canon_n,"window_rows":win_n,"raw_offset":offset}

    def run(self,interval_s=1.0,max_seconds=None):
        started=time.monotonic()
        while not self.stop_event.is_set():
            out=self.cycle()
            if out["raw_lines"] or out["canonical_events"]:
                print("[CHF-006 CYCLE]",out,flush=True)
            if max_seconds is not None and time.monotonic()-started>=max_seconds:
                break
            time.sleep(interval_s)

    def stop(self):
        self.stop_event.set()
