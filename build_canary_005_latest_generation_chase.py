from __future__ import annotations

import ast
from pathlib import Path

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)

TEST=Path(
    "test_canary_005_latest_generation_chase.py"
)

REFRESH_BLOCK='def _fast_005_refresh_latest(\n    lane,\n    token,\n    snap,\n    opportunity,\n    slot,\n    received_ns,\n    generation,\n):\n    current_snap=snap\n    current_opportunity=opportunity\n    current_slot=int(slot)\n    current_received_ns=int(received_ns)\n    current_generation=int(generation)\n\n    refreshes=0\n\n    while refreshes<3:\n        with lane.cv:\n            row=lane.latest.get(\n                token\n            )\n\n        if not row:\n            break\n\n        if int(\n            row[3]\n        )<=current_generation:\n            break\n\n        current_snap=row[0]\n        current_slot=int(\n            row[1]\n        )\n        current_received_ns=int(\n            row[2]\n        )\n        current_generation=int(\n            row[3]\n        )\n\n        rows=q18.exact_snapshot_opportunities(\n            current_snap,\n            0.005,\n        )\n\n        if not rows:\n            print(\n                "[FAST_005_REFRESH_HOLD] "\n                "token=%s reason=NO_005_QUOTES"\n                %token[:10],\n                flush=True,\n            )\n            return None\n\n        current_opportunity=max(\n            rows,\n            key=lambda x:int(\n                x["local_net"]\n            ),\n        )\n\n        refreshes+=1\n\n        print(\n            "[FAST_005_REFRESH] "\n            "token=%s refresh=%d slot=%s "\n            "dir=%s bps=%+.2f net=%+d"\n            %(\n                token[:10],\n                refreshes,\n                current_slot,\n                current_opportunity[\n                    "direction"\n                ],\n                float(\n                    current_opportunity[\n                        "local_bps"\n                    ]\n                ),\n                int(\n                    current_opportunity[\n                        "local_net"\n                    ]\n                ),\n            ),\n            flush=True,\n        )\n\n        if int(\n            current_opportunity[\n                "local_net"\n            ]\n        )<=0:\n            print(\n                "[FAST_005_REFRESH_HOLD] "\n                "token=%s reason=LATEST_NONPOSITIVE "\n                "net=%+d"\n                %(\n                    token[:10],\n                    int(\n                        current_opportunity[\n                            "local_net"\n                        ]\n                    ),\n                ),\n                flush=True,\n            )\n            return None\n\n    if lane.newer_waiting(\n        token,\n        current_generation,\n    ):\n        print(\n            "[FAST_005_REFRESH_HOLD] "\n            "token=%s reason=GENERATION_CHURN_LIMIT"\n            %token[:10],\n            flush=True,\n        )\n        return None\n\n    return (\n        current_snap,\n        current_opportunity,\n        current_slot,\n        current_received_ns,\n        current_generation,\n    )'
TEST_SOURCE='from __future__ import annotations\n\nimport ast\nfrom pathlib import Path\nimport unittest\n\nRT=Path(\n    "qseries_v2/oracle_execution/"\n    "solana_atomic_executor/runtime.py"\n)\n\n\nclass T(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.src=RT.read_text(\n            encoding="utf-8"\n        )\n        cls.tree=ast.parse(\n            cls.src\n        )\n\n    def fn(self,name):\n        rows=[\n            n for n in self.tree.body\n            if isinstance(\n                n,\n                (\n                    ast.FunctionDef,\n                    ast.AsyncFunctionDef,\n                ),\n            )\n            and n.name==name\n        ]\n\n        self.assertEqual(\n            len(rows),\n            1,\n            name,\n        )\n\n        return (\n            ast.get_source_segment(\n                self.src,\n                rows[0],\n            )\n            or ""\n        )\n\n    def test_refresh_helper_exists(self):\n        s=self.fn(\n            "_fast_005_refresh_latest"\n        )\n\n        self.assertIn(\n            "lane.latest.get",\n            s,\n        )\n\n        self.assertIn(\n            "lane.cv",\n            s,\n        )\n\n    def test_refresh_exact_005_only(self):\n        s=self.fn(\n            "_fast_005_refresh_latest"\n        )\n\n        self.assertIn(\n            "exact_snapshot_opportunities",\n            s,\n        )\n\n        self.assertIn(\n            "0.005",\n            s,\n        )\n\n    def test_refresh_bounded(self):\n        s=self.fn(\n            "_fast_005_refresh_latest"\n        )\n\n        self.assertIn(\n            "refreshes<3",\n            s,\n        )\n\n        self.assertIn(\n            "GENERATION_CHURN_LIMIT",\n            s,\n        )\n\n    def test_negative_latest_holds(self):\n        s=self.fn(\n            "_fast_005_refresh_latest"\n        )\n\n        self.assertIn(\n            "LATEST_NONPOSITIVE",\n            s,\n        )\n\n    def test_fast_attack_uses_refresh(self):\n        s=self.fn(\n            "fast_live_attack"\n        )\n\n        self.assertIn(\n            "_fast_005_refresh_latest(",\n            s,\n        )\n\n        self.assertNotIn(\n            "if lane.newer_waiting(token,generation):\\n        return",\n            s[:900],\n        )\n\n    def test_profit_lock_preserved(self):\n        s=self.fn(\n            "_fast_005_profit_lock_route"\n        )\n\n        self.assertIn(\n            "PUMP_TO_METEORA",\n            s,\n        )\n\n        self.assertIn(\n            "METEORA_TO_PUMP",\n            s,\n        )\n\n    def test_profit_floor_preserved(self):\n        self.assertIn(\n            "FAST_005_MIN_REALIZED_LAMPORTS=10_000",\n            self.src,\n        )\n\n    def test_send_preflight_preserved(self):\n        s=self.fn(\n            "_live_005_send_once"\n        )\n\n        self.assertIn(\n            \'"skipPreflight":False\',\n            s,\n        )\n\n        self.assertIn(\n            \'"maxRetries":0\',\n            s,\n        )\n\n    def test_one_shot_reconciliation_preserved(self):\n        s=self.fn(\n            "_live_005_certify_or_send"\n        )\n\n        self.assertIn(\n            \'state["send_attempted"]=True\',\n            s,\n        )\n\n        self.assertIn(\n            "q96.reconcile",\n            s,\n        )\n\n\nif __name__=="__main__":\n    unittest.main(\n        verbosity=2\n    )\n'


def parse(src,label):
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise RuntimeError(
            f"{label}_SYNTAX_ERROR:{exc}"
        ) from exc


def rows(src,name):
    tree=parse(
        src,
        "TARGET",
    )

    return [
        n for n in tree.body
        if isinstance(
            n,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
        and n.name==name
    ]


def fn_src(src,name):
    found=rows(
        src,
        name,
    )

    if len(found)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:"
            f"{len(found)}"
        )

    return (
        ast.get_source_segment(
            src,
            found[0],
        )
        or ""
    )


def replace_fn(
    src,
    name,
    replacement,
):
    found=rows(
        src,
        name,
    )

    if len(found)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:"
            f"{len(found)}"
        )

    node=found[0]
    lines=src.splitlines(
        keepends=True
    )

    start=sum(
        len(x)
        for x in lines[
            :node.lineno-1
        ]
    )

    end=sum(
        len(x)
        for x in lines[
            :node.end_lineno
        ]
    )

    return (
        src[:start]
        +replacement.rstrip()
        +"\n\n"
        +src[end:]
    )


def remove_existing_refresh(src):
    marker=(
        "def _fast_005_refresh_latest("
    )

    if marker not in src:
        return src

    found=rows(
        src,
        "_fast_005_refresh_latest",
    )

    if len(found)!=1:
        raise RuntimeError(
            "FAST_005_REFRESH_SEAM_COUNT:"
            +str(len(found))
        )

    node=found[0]
    lines=src.splitlines(
        keepends=True
    )

    start=sum(
        len(x)
        for x in lines[
            :node.lineno-1
        ]
    )

    end=sum(
        len(x)
        for x in lines[
            :node.end_lineno
        ]
    )

    return (
        src[:start]
        +src[end:]
    )


def main():
    if not RT.is_file():
        raise RuntimeError(
            "CANONICAL_RUNTIME_MISSING"
        )

    src=RT.read_text(
        encoding="utf-8"
    )

    parse(
        src,
        "BEFORE",
    )

    required=(
        "FAST_005_MIN_REALIZED_LAMPORTS=10_000",
        "def fast_live_attack",
        "def _fast_005_profit_lock_route",
        "def _live_005_send_once",
        '"skipPreflight":False',
        '"maxRetries":0',
        "def _live_005_certify_or_send",
        "q96.reconcile",
    )

    missing=[
        x
        for x in required
        if x not in src
    ]

    if missing:
        raise RuntimeError(
            "FAST_005_REFRESH_EXPECTED_SEAM_MISSING:"
            +repr(missing)
        )

    src=remove_existing_refresh(
        src
    )

    insert_at=src.index(
        "\ndef fast_live_attack"
    )

    src=(
        src[:insert_at]
        +"\n\n"
        +REFRESH_BLOCK
        +"\n\n"
        +src[insert_at:]
    )

    fast=fn_src(
        src,
        "fast_live_attack",
    )

    old=r"""    direction=str(opportunity["direction"])

    if lane.newer_waiting(token,generation):
        return

    if int(opportunity["start"])!=5_000_000:
"""

    if old not in fast:
        raise RuntimeError(
            "FAST_005_INITIAL_SILENT_DROP_SEAM_MISSING"
        )

    new=r"""    refreshed=_fast_005_refresh_latest(
        lane,
        token,
        snap,
        opportunity,
        slot,
        received_ns,
        generation,
    )

    if refreshed is None:
        return

    (
        snap,
        opportunity,
        slot,
        received_ns,
        generation,
    )=refreshed

    direction=str(
        opportunity["direction"]
    )

    if int(opportunity["start"])!=5_000_000:
"""

    fast=fast.replace(
        old,
        new,
        1,
    )

    src=replace_fn(
        src,
        "fast_live_attack",
        fast,
    )

    parse(
        src,
        "AFTER",
    )

    parse(
        TEST_SOURCE,
        "TEST",
    )

    RT.write_text(
        src,
        encoding="utf-8",
    )

    TEST.write_text(
        TEST_SOURCE,
        encoding="utf-8",
    )

    print(
        "[PASS] CANARY-005 latest-generation chase installed"
    )
    print(
        "[PASS] silent top-of-fast-path newer_waiting drop removed"
    )
    print(
        "[PASS] newest queued 0.005 snapshot repriced immediately"
    )
    print(
        "[PASS] bounded to 3 generation refreshes"
    )
    print(
        "[PASS] latest nonpositive state still hard-HOLDs"
    )
    print(
        "[PASS] 10000-lamport atomic profit floor preserved"
    )
    print(
        "[PASS] send preflight + maxRetries=0 preserved"
    )
    print(
        "[PASS] one-shot confirmation/reconciliation preserved"
    )


if __name__=="__main__":
    main()
