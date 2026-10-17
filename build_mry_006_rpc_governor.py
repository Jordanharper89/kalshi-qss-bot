from pathlib import Path
import ast

TARGET=Path("qseries_v2/oracle_execution/solana_atomic_executor/mry_006_rpc_governor.py")
TEST=Path("test_mry_006_rpc_governor.py")

MODULE='from __future__ import annotations\nimport time\n\nBASE_INTERVAL=45.0\nMAX_INTERVAL=180.0\n\nclass RpcGovernor:\n    def __init__(self,base=BASE_INTERVAL,maximum=MAX_INTERVAL):\n        self.base=float(base)\n        self.maximum=float(maximum)\n        self.interval=self.base\n        self.pressure=0\n\n    def success(self):\n        self.pressure=max(0,self.pressure-1)\n        if self.pressure==0:\n            self.interval=max(self.base,self.interval*.75)\n        return self.interval\n\n    def failure(self,exc):\n        text=str(exc).lower()\n        limited=("429" in text or "too many requests" in text or "rate limit" in text)\n        if limited:\n            self.pressure=min(8,self.pressure+1)\n            self.interval=min(self.maximum,max(self.base,self.interval*1.8))\n        return limited,self.interval\n\n    def sleep_seconds(self):\n        return max(self.base,min(self.maximum,self.interval))\n\ndef is_rate_limited(exc):\n    s=str(exc).lower()\n    return "429" in s or "too many requests" in s or "rate limit" in s\n\ndef paced_sleep(seconds,stop_fn=lambda:False):\n    end=time.monotonic()+max(0.0,float(seconds))\n    while time.monotonic()<end:\n        if stop_fn():\n            return False\n        time.sleep(min(.1,end-time.monotonic()))\n    return True\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_execution.solana_atomic_executor import mry_006_rpc_governor as m\n\nclass T(unittest.TestCase):\n    def test_429_backoff(self):\n        g=m.RpcGovernor(base=10,maximum=100)\n        limited,x=g.failure(RuntimeError("HTTP 429 Too Many Requests"))\n        self.assertTrue(limited)\n        self.assertGreater(x,10)\n\n    def test_success_recovers(self):\n        g=m.RpcGovernor(base=10,maximum=100)\n        g.failure(RuntimeError("429"))\n        self.assertGreaterEqual(g.success(),10)\n\n    def test_classifier(self):\n        self.assertTrue(m.is_rate_limited(Exception("server rate limit")))\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'

ast.parse(MODULE)
ast.parse(TEST_SOURCE)
TARGET.parent.mkdir(parents=True,exist_ok=True)
TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_SOURCE,encoding="utf-8")

print("[PASS] MRY-006 installed")
print("[PASS] module:",TARGET)
print("[PASS] test:",TEST)
