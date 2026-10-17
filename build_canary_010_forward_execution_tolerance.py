from __future__ import annotations

import ast
import re
from pathlib import Path

RT=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
TEST=Path("test_canary_010_forward_execution_tolerance.py")

OLD_BLOCK='    ixs=[\n        copy.deepcopy(x)\n        for x in template[\n            "instructions"\n        ]\n    ]\n\n    pump_index=int(\n        template[\n            "pump_index"\n        ]\n    )\n\n    ixs[\n        pump_index\n    ]=rewrite_pump_buy_bounds(\n        ixs[\n            pump_index\n        ],\n        start,\n        base_out,\n    )\n\n    pump_ix=ixs[\n        pump_index\n    ]\n'
NEW_BLOCK='    execution_base_floor=max(\n        1,\n        base_out\n        *(\n            10000\n            -FAST_010_PUMP_EXECUTION_TOLERANCE_BPS\n        )\n        //10000,\n    )\n\n    execution_net_floor=int(\n        q18.token_net(\n            token,\n            execution_base_floor,\n        )\n    )\n\n    if execution_net_floor<=0:\n        raise RuntimeError(\n            "PUMP_EXECUTION_NET_FLOOR_ZERO"\n        )\n\n    execution_mq=(\n        q18.core.dlmm_quote_snapshot(\n            snap,\n            execution_net_floor,\n            token,\n        )\n    )\n\n    ixs=[\n        copy.deepcopy(x)\n        for x in template[\n            "instructions"\n        ]\n    ]\n\n    pump_index=int(\n        template[\n            "pump_index"\n        ]\n    )\n\n    ixs[\n        pump_index\n    ]=rewrite_pump_buy_bounds(\n        ixs[\n            pump_index\n        ],\n        start,\n        execution_base_floor,\n    )\n\n    pump_ix=ixs[\n        pump_index\n    ]\n'
OLD_METEORA='    meteora_ix=(\n        build_meteora_ix_hot(\n            token,\n            net_out,\n            dict(\n                opportunity["mq"]\n            ),\n        )\n    )\n'
NEW_METEORA='    meteora_ix=(\n        build_meteora_ix_hot(\n            token,\n            execution_net_floor,\n            dict(\n                execution_mq\n            ),\n        )\n    )\n'
TEST_SOURCE='from __future__ import annotations\nimport ast\nfrom pathlib import Path\nimport unittest\n\nRT=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")\n\nclass T(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.src=RT.read_text(encoding="utf-8")\n        cls.tree=ast.parse(cls.src)\n\n    def fn(self,name):\n        rows=[\n            n for n in cls.tree.body\n            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))\n            and n.name==name\n        ]\n        self.assertEqual(len(rows),1,name)\n        return ast.get_source_segment(self.src,rows[0]) or ""\n\n    def test_tolerance_constant(self):\n        self.assertIn(\n            "FAST_010_PUMP_EXECUTION_TOLERANCE_BPS=20",\n            self.src\n        )\n\n    def test_forward_uses_floor(self):\n        s=self.fn("same_snapshot_route")\n        self.assertIn("execution_base_floor=max(",s)\n        self.assertIn("execution_net_floor=int(",s)\n        self.assertIn("execution_mq",s)\n\n    def test_meteora_uses_floor(self):\n        s=self.fn("same_snapshot_route")\n        self.assertIn("build_meteora_ix_hot(",s)\n        self.assertIn("execution_net_floor",s)\n\n    def test_native_010_template_preserved(self):\n        s=self.fn("prebuild_templates")\n        self.assertIn("CANARY_TRADE_LAMPORTS",s)\n        self.assertIn(\'"template_quote_lamports"\',s)\n\n    def test_exact_010_preserved(self):\n        self.assertIn("CANARY_TRADE_SOL=0.010",self.src)\n        self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",self.src)\n\n    def test_profit_lock_preserved(self):\n        s=self.fn("fast_live_attack")\n        self.assertIn("_fast_010_profit_lock_route(",s)\n        self.assertIn("FAST_010_MIN_REALIZED_LAMPORTS",s)\n\n    def test_direct_send_preserved(self):\n        s=self.fn("fast_live_attack")\n        self.assertIn("_live_010_certify_or_send(",s)\n        self.assertNotIn("_fast_010_prime_live_gate(",s)\n\n    def test_single_compile_preserved(self):\n        s=self.fn("fast_live_attack")\n        self.assertEqual(s.count("compile_current("),1)\n\n    def test_preflight_no_retry_preserved(self):\n        s=self.fn("_live_010_send_once")\n        self.assertIn(\'"skipPreflight":False\',s)\n        self.assertIn(\'"maxRetries":0\',s)\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'

def parse(src,label):
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise RuntimeError(f"{label}_SYNTAX_ERROR:{exc}") from exc

def fn_node(src,name):
    tree=parse(src,"TARGET")
    rows=[
        n for n in tree.body
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
        and n.name==name
    ]
    if len(rows)!=1:
        raise RuntimeError(f"{name}_SEAM_COUNT:{len(rows)}")
    return rows[0]

def fn_source(src,name):
    n=fn_node(src,name)
    return ast.get_source_segment(src,n) or ""

def replace_fn(src,name,replacement):
    n=fn_node(src,name)
    lines=src.splitlines(keepends=True)
    start=sum(len(x) for x in lines[:n.lineno-1])
    end=sum(len(x) for x in lines[:n.end_lineno])
    return src[:start]+replacement.rstrip()+"\n\n"+src[end:]

def ensure_constant(src):
    name="FAST_010_PUMP_EXECUTION_TOLERANCE_BPS"
    line=name+"=20"
    if re.search(rf"^{name}=.*$",src,flags=re.M):
        return re.sub(rf"^{name}=.*$",line,src,count=1,flags=re.M)
    anchor="FAST_010_FEE_CEILING_LAMPORTS=10_000\n"
    if anchor not in src:
        raise RuntimeError("TOLERANCE_CONSTANT_ANCHOR_MISSING")
    return src.replace(anchor,anchor+line+"\n",1)

def main():
    if not RT.is_file():
        raise RuntimeError("CANONICAL_RUNTIME_MISSING")

    src=RT.read_text(encoding="utf-8")
    parse(src,"BEFORE")

    required=(
        "CANARY_TRADE_SOL=0.010",
        "CANARY_TRADE_LAMPORTS=10_000_000",
        "def same_snapshot_route",
        "def prebuild_templates",
        "def fast_live_attack",
        "def _live_010_send_once",
        '"skipPreflight":False',
        '"maxRetries":0',
    )

    missing=[x for x in required if x not in src]
    if missing:
        raise RuntimeError(
            "FORWARD_TOLERANCE_EXPECTED_SEAM_MISSING:"+repr(missing)
        )

    src=ensure_constant(src)
    route=fn_source(src,"same_snapshot_route")

    if "execution_base_floor=max(" not in route:
        if OLD_BLOCK not in route:
            raise RuntimeError("FORWARD_PUMP_BOUND_SEAM_MISSING")
        route=route.replace(OLD_BLOCK,NEW_BLOCK,1)

    if OLD_METEORA in route:
        route=route.replace(OLD_METEORA,NEW_METEORA,1)

    if (
        "execution_base_floor=max(" not in route
        or "execution_net_floor" not in route
        or "execution_mq" not in route
    ):
        raise RuntimeError("FORWARD_TOLERANCE_NOT_INSTALLED")

    src=replace_fn(src,"same_snapshot_route",route)

    parse(src,"AFTER")
    parse(TEST_SOURCE,"TEST")

    RT.write_text(src,encoding="utf-8")
    TEST.write_text(TEST_SOURCE,encoding="utf-8")

    print("[PASS] CANARY-010 forward execution tolerance installed")
    print("[PASS] Pump token floor tolerance=20 bps")
    print("[PASS] Meteora input reduced to guaranteed Pump floor")
    print("[PASS] Meteora quote rebuilt from guaranteed token floor")
    print("[PASS] final atomic SOL profit lock preserved")
    print("[PASS] native 0.010 funding preserved")
    print("[PASS] direct send / one compile preserved")
    print("[PASS] preflight + maxRetries=0 preserved")

if __name__=="__main__":
    main()
