from __future__ import annotations
import time
def preload(fn,root,attempts=8):
    last=None
    for n in range(1,attempts+1):
        try:
            out=fn(root)
            print("[MRIYA_ALT_PRELOAD_OK] attempt=%d"%n,flush=True)
            return out
        except Exception as exc:
            last=exc
            s=str(exc).lower()
            limited=("429" in s or "too many requests" in s or "rate limit" in s)
            if not limited or n>=attempts:
                raise
            delay=min(20.0,2.0*(2**(n-1)))
            print("[MRIYA_ALT_PRELOAD_429] attempt=%d sleep=%.1f"%(n,delay),flush=True)
            time.sleep(delay)
    raise last
