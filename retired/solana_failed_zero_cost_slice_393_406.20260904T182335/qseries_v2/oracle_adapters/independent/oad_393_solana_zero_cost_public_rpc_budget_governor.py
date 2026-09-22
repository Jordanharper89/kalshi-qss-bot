from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque
import time
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaRpcBudgetPolicy:
    window_seconds: float = 10.0
    total_requests_per_window: int = 20
    per_method_requests_per_window: int = 8
    min_spacing_seconds: float = 0.15
    max_backoff_seconds: float = 30.0

@dataclass(slots=True)
class SolanaRpcBudgetState:
    total: deque = field(default_factory=deque)
    by_method: dict = field(default_factory=dict)
    next_allowed_at: float = 0.0
    throttle_count: int = 0
    last_retry_after_seconds: float = 0.0

class SolanaPublicRpcBudgetGovernor:
    def __init__(self, policy=None, clock=time.monotonic):
        self.policy=policy or SolanaRpcBudgetPolicy()
        self.state=SolanaRpcBudgetState()
        self.clock=clock
    def _prune(self,now):
        cutoff=now-self.policy.window_seconds
        while self.state.total and self.state.total[0] <= cutoff:
            self.state.total.popleft()
        for method,q in list(self.state.by_method.items()):
            while q and q[0] <= cutoff:
                q.popleft()
            if not q:
                self.state.by_method.pop(method,None)
    def wait_seconds(self,method,now=None):
        now=self.clock() if now is None else float(now)
        self._prune(now)
        waits=[max(0.0,self.state.next_allowed_at-now)]
        if len(self.state.total)>=self.policy.total_requests_per_window:
            waits.append(max(0.0,self.state.total[0]+self.policy.window_seconds-now))
        q=self.state.by_method.get(method,deque())
        if len(q)>=self.policy.per_method_requests_per_window:
            waits.append(max(0.0,q[0]+self.policy.window_seconds-now))
        return max(waits)
    def admit(self,method,now=None):
        now=self.clock() if now is None else float(now)
        if self.wait_seconds(method,now)>0:
            return False
        self.state.total.append(now)
        self.state.by_method.setdefault(method,deque()).append(now)
        self.state.next_allowed_at=now+self.policy.min_spacing_seconds
        return True
    def record_throttle(self,retry_after_seconds=None,now=None):
        now=self.clock() if now is None else float(now)
        self.state.throttle_count+=1
        retry=float(retry_after_seconds or min(self.policy.max_backoff_seconds,2**min(self.state.throttle_count,5)))
        retry=min(max(0.0,retry),self.policy.max_backoff_seconds)
        self.state.last_retry_after_seconds=retry
        self.state.next_allowed_at=max(self.state.next_allowed_at,now+retry)
    def snapshot(self,now=None):
        now=self.clock() if now is None else float(now)
        self._prune(now)
        return {
            "window_seconds":self.policy.window_seconds,
            "requests_in_window":len(self.state.total),
            "per_method_in_window":{k:len(v) for k,v in self.state.by_method.items()},
            "next_allowed_in_seconds":max(0.0,self.state.next_allowed_at-now),
            "throttle_count":self.state.throttle_count,
            "last_retry_after_seconds":self.state.last_retry_after_seconds,
            "execution_authority":False,
        }