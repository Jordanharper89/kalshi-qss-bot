from __future__ import annotations
import time

BASE_INTERVAL=45.0
MAX_INTERVAL=180.0

class RpcGovernor:
    def __init__(self,base=BASE_INTERVAL,maximum=MAX_INTERVAL):
        self.base=float(base)
        self.maximum=float(maximum)
        self.interval=self.base
        self.pressure=0

    def success(self):
        self.pressure=max(0,self.pressure-1)
        if self.pressure==0:
            self.interval=max(self.base,self.interval*.75)
        return self.interval

    def failure(self,exc):
        text=str(exc).lower()
        limited=("429" in text or "too many requests" in text or "rate limit" in text)
        if limited:
            self.pressure=min(8,self.pressure+1)
            self.interval=min(self.maximum,max(self.base,self.interval*1.8))
        return limited,self.interval

    def sleep_seconds(self):
        return max(self.base,min(self.maximum,self.interval))

def is_rate_limited(exc):
    s=str(exc).lower()
    return "429" in s or "too many requests" in s or "rate limit" in s

def paced_sleep(seconds,stop_fn=lambda:False):
    end=time.monotonic()+max(0.0,float(seconds))
    while time.monotonic()<end:
        if stop_fn():
            return False
        time.sleep(min(.1,end-time.monotonic()))
    return True
