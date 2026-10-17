from __future__ import annotations

import ast
from pathlib import Path

TARGET=Path("qseries_v2/oracle_execution/solana_atomic_executor/mry_004_adaptive_capacity.py")
TEST=Path("test_mry_004_adaptive_capacity.py")

MODULE=(
    'from __future__ import annotations\nclass'
    ' CapacityController:\n    def __init__(se'
    'lf,start=20,minimum=4,maximum=40):\n     '
    '   self.target=max(minimum,min(maximum,i'
    'nt(start)))\n        self.minimum=int(min'
    'imum);self.maximum=int(maximum)\n        '
    'self.healthy_streak=0\n    def observe(se'
    'lf,metrics):\n        rate=int(metrics.ge'
    't("rate_limits") or 0)\n        reconnect'
    's=int(metrics.get("reconnects") or 0)\n  '
    '      p95=float(metrics.get("p95_event_a'
    'ge_ms") or 0.0)\n        pricing=float(me'
    'trics.get("p95_pricing_ms") or 0.0)\n    '
    '    overloaded=bool(rate>0 or reconnects'
    '>1 or p95>40.0 or pricing>15.0)\n        '
    'if overloaded:\n            self.target=m'
    'ax(self.minimum,self.target-4);self.heal'
    'thy_streak=0\n            return self.tar'
    'get\n        self.healthy_streak+=1\n     '
    '   if self.healthy_streak>=3:\n          '
    '  self.target=min(self.maximum,self.targ'
    'et+2);self.healthy_streak=0\n        retu'
    'rn self.target\n\ndef percentile(rows,q):\n'
    '    vals=sorted(float(x) for x in rows i'
    'f x is not None)\n    if not vals:return '
    '0.0\n    i=min(len(vals)-1,max(0,int((len'
    '(vals)-1)*float(q))))\n    return vals[i]'
    '\n'
)

TEST_SOURCE=(
    'import unittest\nfrom qseries_v2.oracle_e'
    'xecution.solana_atomic_executor import m'
    'ry_004_adaptive_capacity as m\nclass T(un'
    'ittest.TestCase):\n    def test_shrink(se'
    'lf):\n        c=m.CapacityController()\n  '
    '      self.assertEqual(c.observe({"rate_'
    'limits":1}),16)\n    def test_grow(self):'
    '\n        c=m.CapacityController()\n      '
    '  for _ in range(3):x=c.observe({})\n    '
    '    self.assertEqual(x,22)\n    def test_'
    'pct(self):\n        self.assertEqual(m.pe'
    'rcentile([1,2,3,4],.95),3.0)\nif __name__'
    '=="__main__":unittest.main(verbosity=2)\n'
)

ast.parse(MODULE)
ast.parse(TEST_SOURCE)
TARGET.parent.mkdir(parents=True,exist_ok=True)
TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_SOURCE,encoding="utf-8")

print("[PASS] MRY-004 installed")
print("[PASS] module: qseries_v2/oracle_execution/solana_atomic_executor/mry_004_adaptive_capacity.py")
print("[PASS] test: test_mry_004_adaptive_capacity.py")
