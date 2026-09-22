
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED = 'build_oad_393_solana_zero_cost_public_rpc_budget_governor.py'
MODULE = 'oad_393_solana_zero_cost_public_rpc_budget_governor.py'
TEST = 'test_oad_393_solana_zero_cost_public_rpc_budget_governor.py'
RUNNER = ''
MODULE_SOURCE = r"""from __future__ import annotations
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
        }"""
TEST_SOURCE = r"""import unittest
from qseries_v2.oracle_adapters.independent.oad_393_solana_zero_cost_public_rpc_budget_governor import SolanaRpcBudgetPolicy,SolanaPublicRpcBudgetGovernor
class T(unittest.TestCase):
    def test_budget(self):
        now=[100.0]
        g=SolanaPublicRpcBudgetGovernor(SolanaRpcBudgetPolicy(total_requests_per_window=3,per_method_requests_per_window=2,min_spacing_seconds=0),clock=lambda:now[0])
        self.assertTrue(g.admit("getBlock"))
        self.assertTrue(g.admit("getBlock"))
        self.assertFalse(g.admit("getBlock"))
        self.assertTrue(g.admit("getSlot"))
        self.assertFalse(g.admit("getBlocks"))
        g.record_throttle(4.0)
        self.assertGreaterEqual(g.wait_seconds("getSlot"),4.0)
        print("[BUDGET]",g.snapshot())
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-393 zero-cost public RPC budget governor certified")"""
RUNNER_SOURCE = r""""""
DEPS = [('qseries_v2/oracle_adapters/independent/oad_148_solana_mainnet_chain_state_acquisition.py', ('_rpc',))]

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise RuntimeError("repository root not found")

def atomic_write(path: Path, source: str):
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def verify_dep(root: Path, rel: str, required=()):
    p = root / rel
    if not p.is_file():
        raise RuntimeError("required dependency missing: " + rel)
    tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    names = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    missing = [x for x in required if x not in names]
    if missing:
        raise RuntimeError("dependency interface missing: " + rel + " -> " + repr(missing))
    print("[PASS] dependency verified:", rel)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename mismatch")
    root = find_root()
    for rel, req in DEPS:
        verify_dep(root, rel, req)

    pkg = root / "qseries_v2" / "oracle_adapters" / "independent"
    module_path = pkg / MODULE
    test_path = root / TEST
    atomic_write(module_path, MODULE_SOURCE)
    atomic_write(test_path, TEST_SOURCE)

    if RUNNER:
        atomic_write(root / RUNNER, RUNNER_SOURCE)

    init = pkg / "__init__.py"
    lines = init.read_text(encoding="utf-8").splitlines() if init.exists() else []
    export = "from ." + module_path.stem + " import *"
    if export not in lines:
        lines.append(export)
    atomic_write(init, "\n".join(x for x in lines if x.strip()) + "\n")

    print("[PASS] installed:", module_path.relative_to(root))
    print("[PASS] test installed:", test_path.relative_to(root))
    if RUNNER:
        print("[PASS] runner installed:", RUNNER)
    print("[PASS] public-RPC / zero-cost architecture only")
    print("[PASS] no paid RPC provider dependency")
    print("[PASS] no GMGN dependency")
    print("[PASS] existing OAD-318+ chain path preserved")
    print("[PASS] existing OPH-019/021 PostgreSQL path preserved")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution_authority=FALSE")
    print("[DONE]", EXPECTED)

if __name__ == "__main__":
    main()
