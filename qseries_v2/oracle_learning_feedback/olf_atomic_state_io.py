from __future__ import annotations
from pathlib import Path
import json, os, time, uuid

OLF_ATOMIC_STATE_IO_REVISION = "OLF_ATOMIC_STATE_IO_V1"

def atomic_write_json(path, payload, max_attempts=8):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    last = None

    for attempt in range(1, int(max_attempts) + 1):
        tmp = p.with_name(p.name + f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
        try:
            tmp.write_text(raw, encoding="utf-8", newline="\n")
            os.replace(tmp, p)
            return p
        except PermissionError as exc:
            last = exc
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:
                pass
            if attempt >= int(max_attempts):
                break
            time.sleep(min(0.5, 0.025 * (2 ** (attempt - 1))))
        finally:
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:
                pass

    raise last or PermissionError(f"atomic JSON replace failed: {p}")
