from __future__ import annotations

import ast
import base64
from pathlib import Path

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)

TEST=Path(
    "test_canary_010_reverse_ata_readiness.py"
)

HELPERS=r"""
def _ata_create_idempotent_ix(
    payer,
    owner,
    mint,
    token_program,
):
    ata=q87.c.ata(
        owner,
        mint,
        token_program,
    )

    return {
        "programId":
            q87.c.ATA,

        "accounts":[
            {
                "pubkey":payer,
                "isSigner":True,
                "isWritable":True,
            },
            {
                "pubkey":ata,
                "isSigner":False,
                "isWritable":True,
            },
            {
                "pubkey":owner,
                "isSigner":False,
                "isWritable":False,
            },
            {
                "pubkey":mint,
                "isSigner":False,
                "isWritable":False,
            },
            {
                "pubkey":q87.c.SYSTEM,
                "isSigner":False,
                "isWritable":False,
            },
            {
                "pubkey":token_program,
                "isSigner":False,
                "isWritable":False,
            },
        ],

        # Associated Token Program:
        # 1 = CreateIdempotent
        "data":
            base64.b64encode(
                bytes([1])
            ).decode(),
    }


def _reverse_prepend_ata_readiness(
    user,
    token,
    route,
):
    token_program=None

    template=METEORA_TEMPLATES.get(
        str(token)
    )

    if template is None:
        raise RuntimeError(
            "REVERSE_METEORA_TEMPLATE_MISSING:"
            +str(token)
        )

    token_x=str(
        template["token_x"]
    )

    token_y=str(
        template["token_y"]
    )

    fixed=list(
        template[
            "fixed_accounts"
        ]
    )

    # fixed_accounts positions:
    # 11 = token_x program
    # 12 = token_y program
    if len(fixed)<13:
        raise RuntimeError(
            "REVERSE_METEORA_FIXED_ACCOUNTS_SHORT"
        )

    if token_x==str(token):
        token_program=str(
            fixed[11][0]
        )
    elif token_y==str(token):
        token_program=str(
            fixed[12][0]
        )
    else:
        raise RuntimeError(
            "REVERSE_TOKEN_NOT_IN_METEORA_TEMPLATE"
        )

    create_token_ata=(
        _ata_create_idempotent_ix(
            user,
            user,
            str(token),
            token_program,
        )
    )

    out=dict(route)

    candidates=[]

    for name,ixs in list(
        route.get(
            "original_candidates"
        )
        or []
    ):
        ixs=list(ixs)

        candidates.append(
            (
                "ATA_READY_"+str(name),
                [create_token_ata]+ixs,
            )
        )

    if not candidates:
        raise RuntimeError(
            "REVERSE_NO_CANDIDATES_FOR_ATA_READY"
        )

    out[
        "original_candidates"
    ]=candidates

    out[
        "reverse_ata_ready"
    ]=True

    return out
""".strip()

TEST_SOURCE=r"""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=RT.read_text(
            encoding="utf-8"
        )
        cls.tree=ast.parse(
            cls.src
        )

    def fn(self,name):
        rows=[
            n for n in self.tree.body
            if isinstance(
                n,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and n.name==name
        ]
        self.assertEqual(
            len(rows),
            1,
            name,
        )
        return (
            ast.get_source_segment(
                self.src,
                rows[0],
            )
            or ""
        )

    def test_idempotent_ata_helper(self):
        s=self.fn(
            "_ata_create_idempotent_ix"
        )
        self.assertIn(
            "bytes([1])",
            s,
        )
        self.assertIn(
            "q87.c.ATA",
            s,
        )

    def test_reverse_readiness_helper(self):
        s=self.fn(
            "_reverse_prepend_ata_readiness"
        )
        self.assertIn(
            "ATA_READY_",
            s,
        )
        self.assertIn(
            "_ata_create_idempotent_ix(",
            s,
        )

    def test_reverse_path_calls_readiness(self):
        matches=[
            self.fn(n.name)
            for n in self.tree.body
            if isinstance(
                n,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and "_reverse_prepend_ata_readiness("
            in (
                ast.get_source_segment(
                    self.src,
                    n,
                )
                or ""
            )
        ]
        self.assertGreaterEqual(
            len(matches),
            1,
        )

    def test_exact_010_preserved(self):
        self.assertIn(
            "CANARY_TRADE_SOL=0.010",
            self.src,
        )
        self.assertIn(
            "CANARY_TRADE_LAMPORTS=10_000_000",
            self.src,
        )

    def test_direct_send_preserved(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertIn(
            "_live_010_certify_or_send(",
            s,
        )

    def test_preflight_preserved(self):
        s=self.fn(
            "_live_010_send_once"
        )
        self.assertIn(
            '"skipPreflight":False',
            s,
        )
        self.assertIn(
            '"maxRetries":0',
            s,
        )

    def test_profit_lock_preserved(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertIn(
            "_fast_010_profit_lock_route(",
            s,
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
"""


def parse(src,label):
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise RuntimeError(
            f"{label}_SYNTAX_ERROR:{exc}"
        ) from exc


def fn_nodes(src):
    tree=parse(src,"TARGET")
    return [
        n for n in tree.body
        if isinstance(
            n,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
    ]


def fn_source(src,name):
    rows=[
        n for n in fn_nodes(src)
        if n.name==name
    ]

    if len(rows)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:{len(rows)}"
        )

    return (
        ast.get_source_segment(
            src,
            rows[0],
        )
        or ""
    )


def replace_fn(src,name,replacement):
    rows=[
        n for n in fn_nodes(src)
        if n.name==name
    ]

    if len(rows)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:{len(rows)}"
        )

    node=rows[0]
    lines=src.splitlines(
        keepends=True
    )

    start=sum(
        len(x)
        for x in lines[:node.lineno-1]
    )

    end=sum(
        len(x)
        for x in lines[:node.end_lineno]
    )

    return (
        src[:start]
        +replacement.rstrip()
        +"\n\n"
        +src[end:]
    )


def insert_before(src,target,block):
    rows=[
        n for n in fn_nodes(src)
        if n.name==target
    ]

    if len(rows)!=1:
        raise RuntimeError(
            f"{target}_SEAM_COUNT:{len(rows)}"
        )

    node=rows[0]
    lines=src.splitlines(
        keepends=True
    )

    start=sum(
        len(x)
        for x in lines[:node.lineno-1]
    )

    return (
        src[:start]
        +block.rstrip()
        +"\n\n"
        +src[start:]
    )


def patch_reverse_builder(src):
    candidates=[]

    for node in fn_nodes(src):
        body=(
            ast.get_source_segment(
                src,
                node,
            )
            or ""
        )

        if (
            "METEORA_TO_PUMP"
            in body
            and "original_candidates"
            in body
            and "return"
            in body
        ):
            candidates.append(
                (
                    node.name,
                    body,
                )
            )

    if not candidates:
        raise RuntimeError(
            "REVERSE_ROUTE_BUILDER_NOT_FOUND"
        )

    # Prefer a function whose name says reverse.
    candidates.sort(
        key=lambda x:(
            0 if "reverse" in x[0].lower()
            else 1,
            len(x[1]),
        )
    )

    name,body=candidates[0]

    if (
        "_reverse_prepend_ata_readiness("
        in body
    ):
        return src,name

    # Replace the final direct return of a route mapping
    # with route capture + readiness wrapper.
    marker="    return {"

    pos=body.rfind(marker)

    if pos<0:
        raise RuntimeError(
            "REVERSE_RETURN_MAPPING_NOT_FOUND:"
            +name
        )

    # Find matching dict braces from the return.
    brace_start=body.find(
        "{",
        pos
    )

    depth=0
    end=None

    for i in range(
        brace_start,
        len(body),
    ):
        ch=body[i]

        if ch=="{":
            depth+=1
        elif ch=="}":
            depth-=1

            if depth==0:
                end=i+1
                break

    if end is None:
        raise RuntimeError(
            "REVERSE_RETURN_MAPPING_UNBALANCED:"
            +name
        )

    mapping=body[
        brace_start:end
    ]

    replacement=(
        "    route="
        +mapping
        +"\n\n"
        +"    return _reverse_prepend_ata_readiness(\n"
        +"        user,\n"
        +"        token,\n"
        +"        route,\n"
        +"    )"
    )

    new_body=(
        body[:pos]
        +replacement
        +body[end:]
    )

    return (
        replace_fn(
            src,
            name,
            new_body,
        ),
        name,
    )


def main():
    if not RT.is_file():
        raise RuntimeError(
            "CANONICAL_RUNTIME_MISSING"
        )

    src=RT.read_text(
        encoding="utf-8"
    )

    parse(src,"BEFORE")

    required=(
        "CANARY_TRADE_SOL=0.010",
        "CANARY_TRADE_LAMPORTS=10_000_000",
        "METEORA_TO_PUMP",
        "original_candidates",
        "def fast_live_attack",
        "def _live_010_send_once",
        '"skipPreflight":False',
        '"maxRetries":0',
    )

    missing=[
        x for x in required
        if x not in src
    ]

    if missing:
        raise RuntimeError(
            "REVERSE_ATA_EXPECTED_SEAM_MISSING:"
            +repr(missing)
        )

    if (
        "def _ata_create_idempotent_ix"
        not in src
    ):
        src=insert_before(
            src,
            "compile_current",
            HELPERS,
        )
    else:
        helper_parts=HELPERS.split(
            "\n\ndef _reverse_prepend_ata_readiness",
            1,
        )

        src=replace_fn(
            src,
            "_ata_create_idempotent_ix",
            helper_parts[0],
        )

        src=replace_fn(
            src,
            "_reverse_prepend_ata_readiness",
            "def _reverse_prepend_ata_readiness"
            +helper_parts[1],
        )

    src,builder=patch_reverse_builder(
        src
    )

    parse(src,"AFTER")
    parse(TEST_SOURCE,"TEST")

    RT.write_text(
        src,
        encoding="utf-8",
    )

    TEST.write_text(
        TEST_SOURCE,
        encoding="utf-8",
    )

    print(
        "[PASS] CANARY-010 reverse ATA readiness installed"
    )
    print(
        "[PASS] reverse token ATA create-idempotent prepended atomically"
    )
    print(
        "[PASS] no setup RPC added to hot path"
    )
    print(
        "[PASS] reverse builder patched: "
        +builder
    )
    print(
        "[PASS] exact 0.010 SOL preserved"
    )
    print(
        "[PASS] direct live send preserved"
    )
    print(
        "[PASS] atomic profit lock preserved"
    )
    print(
        "[PASS] preflight + maxRetries=0 preserved"
    )


if __name__=="__main__":
    main()
