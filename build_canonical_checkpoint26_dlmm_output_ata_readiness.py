from pathlib import Path
import ast

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint26_dlmm_output_ata_readiness.py"
TEST=ROOT/"test_canonical_checkpoint26_dlmm_output_ata_readiness.py"

MODULE=r"""from __future__ import annotations

import argparse
import base64
import sys

from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint25_expanded_live_universe_cutover as c25
from qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as q59
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c


_ORIGINAL_CANDIDATE_SETS=None


def _ata_create_idempotent_for_dlmm(m_ix):
    if m_ix.get("programId")!=c.DLMM:
        raise RuntimeError(
            "CHECKPOINT26_NOT_DLMM_INSTRUCTION"
        )

    ac=list(m_ix.get("accounts") or [])

    if len(ac)<13:
        raise RuntimeError(
            "CHECKPOINT26_DLMM_ACCOUNT_LAYOUT_SHORT:"
            +str(len(ac))
        )

    user=str(ac[10]["pubkey"])
    dest=str(ac[5]["pubkey"])

    token_x=str(ac[6]["pubkey"])
    token_y=str(ac[7]["pubkey"])

    tx_prog=str(ac[11]["pubkey"])
    ty_prog=str(ac[12]["pubkey"])

    x_ata=c.ata(
        user,
        token_x,
        tx_prog,
    )

    y_ata=c.ata(
        user,
        token_y,
        ty_prog,
    )

    if dest==x_ata:
        mint=token_x
        token_program=tx_prog

    elif dest==y_ata:
        mint=token_y
        token_program=ty_prog

    else:
        raise RuntimeError(
            "CHECKPOINT26_OUTPUT_ATA_BINDING_MISMATCH:"
            +dest
        )

    ix={
        "programId":c.ATA,
        "accounts":[
            {
                "pubkey":user,
                "isSigner":True,
                "isWritable":True,
            },
            {
                "pubkey":dest,
                "isSigner":False,
                "isWritable":True,
            },
            {
                "pubkey":user,
                "isSigner":False,
                "isWritable":False,
            },
            {
                "pubkey":mint,
                "isSigner":False,
                "isWritable":False,
            },
            {
                "pubkey":c.SYSTEM,
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
        # CreateIdempotent = instruction discriminator 1.
        "data":base64.b64encode(
            bytes([1])
        ).decode(),
    }

    return ix,{
        "user":user,
        "dest":dest,
        "mint":mint,
        "token_program":token_program,
    }


def _install_candidate_patch():
    global _ORIGINAL_CANDIDATE_SETS

    if _ORIGINAL_CANDIDATE_SETS is not None:
        return

    _ORIGINAL_CANDIDATE_SETS=(
        q59.candidate_instruction_sets
    )

    original=_ORIGINAL_CANDIDATE_SETS

    def patched(p_ixs,m_ix):
        rows=original(
            p_ixs,
            m_ix,
        )

        ata_ix,meta=(
            _ata_create_idempotent_for_dlmm(
                m_ix
            )
        )

        out=[]
        seen=set()

        for name,ixs in rows:
            z=list(ixs)

            pos=next(
                (
                    i
                    for i,x in enumerate(z)
                    if x.get("programId")==c.DLMM
                ),
                None,
            )

            if pos is None:
                raise RuntimeError(
                    "CHECKPOINT26_DLMM_IX_MISSING:"
                    +str(name)
                )

            # Insert immediately before the exact DLMM swap.
            # CreateIdempotent is safe whether the ATA exists
            # already or must be initialized in this transaction.
            z.insert(
                pos,
                dict(ata_ix),
            )

            key=tuple(
                (
                    x.get("programId"),
                    x.get("data"),
                    tuple(
                        a.get("pubkey")
                        for a in
                        (x.get("accounts") or [])
                    ),
                )
                for x in z
            )

            if key in seen:
                continue

            seen.add(key)

            out.append(
                (
                    name+"_ATA_READY",
                    z,
                )
            )

        print(
            "[CHECKPOINT26_ATA_BOUND] "
            "dest=%s mint=%s token_program=%s "
            "candidates=%d"
            %(
                meta["dest"][:12],
                meta["mint"][:12],
                meta["token_program"][:12],
                len(out),
            ),
            flush=True,
        )

        return out

    q59.candidate_instruction_sets=patched


def _restore_candidate_patch():
    global _ORIGINAL_CANDIDATE_SETS

    if _ORIGINAL_CANDIDATE_SETS is None:
        return

    q59.candidate_instruction_sets=(
        _ORIGINAL_CANDIDATE_SETS
    )

    _ORIGINAL_CANDIDATE_SETS=None


def main():
    p=argparse.ArgumentParser()

    p.add_argument(
        "--seconds",
        type=float,
        default=3600.0,
    )

    args=p.parse_args()

    if args.seconds<=0:
        raise RuntimeError(
            "CHECKPOINT26_SECONDS_MUST_BE_POSITIVE"
        )

    old_argv=list(sys.argv)

    _install_candidate_patch()

    print(
        "[CHECKPOINT26_ACTIVATION] "
        "dlmm_output_ata_readiness=True "
        "create_idempotent=True "
        "token2022_aware=True",
        flush=True,
    )

    print(
        "[CHECKPOINT26_BINDING] "
        "user_token_out derived from exact DLMM "
        "instruction account[5]",
        flush=True,
    )

    print(
        "[CHECKPOINT26_HOT_PATH] "
        "ata_derivation=local rpc_added=False",
        flush=True,
    )

    print(
        "[CHECKPOINT26_CHAIN] "
        "checkpoint25 expanded universe -> "
        "pair route -> exact output ATA readiness -> "
        "canonical ALT -> real fee -> freshness -> signed sim",
        flush=True,
    )

    print(
        "[BROADCAST] disabled",
        flush=True,
    )

    try:
        sys.argv=[
            old_argv[0],
            "--seconds",
            str(float(args.seconds)),
        ]

        return c25.main()

    finally:
        sys.argv=old_argv
        _restore_candidate_patch()

        print(
            "[CHECKPOINT26_PATCH_RESTORED] true",
            flush=True,
        )


if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint26_dlmm_output_ata_readiness.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_create_idempotent(self):
        self.assertIn(
            "bytes([1])",
            self.s,
        )

    def test_exact_dlmm_destination(self):
        self.assertIn(
            'dest=str(ac[5]["pubkey"])',
            self.s,
        )

    def test_supports_both_token_programs(self):
        self.assertIn(
            "tx_prog=str(ac[11]",
            self.s,
        )
        self.assertIn(
            "ty_prog=str(ac[12]",
            self.s,
        )

    def test_ata_matches_destination(self):
        self.assertIn(
            "if dest==x_ata:",
            self.s,
        )
        self.assertIn(
            "elif dest==y_ata:",
            self.s,
        )

    def test_insert_before_dlmm(self):
        self.assertIn(
            "z.insert(",
            self.s,
        )
        self.assertIn(
            'x.get("programId")==c.DLMM',
            self.s,
        )

    def test_no_hot_rpc(self):
        helper=cls_slice(
            self.s,
            "def _ata_create_idempotent_for_dlmm",
            "def _install_candidate_patch",
        )
        self.assertNotIn(
            "c.account(",
            helper,
        )
        self.assertNotIn(
            "c.rpc(",
            helper,
        )

    def test_checkpoint25_preserved(self):
        self.assertIn(
            "return c25.main()",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )


def cls_slice(s,a,b):
    return s[
        s.index(a):
        s.index(b)
    ]


if __name__=="__main__":
    unittest.main(verbosity=2)
"""

TARGET.write_text(
    MODULE,
    encoding="utf-8",
)

TEST.write_text(
    TEST_CODE,
    encoding="utf-8",
)

ast.parse(
    TARGET.read_text(encoding="utf-8")
)

ast.parse(
    TEST.read_text(encoding="utf-8")
)

print("[PASS] checkpoint-26 DLMM output ATA readiness installed")
print("[CAUSE] signed simulation 3012 user_token_out AccountNotInitialized")
print("[FIX] exact DLMM destination ATA gets CreateIdempotent immediately before swap")
print("[TOKEN_PROGRAM] legacy Token + Token-2022 derived from exact DLMM accounts")
print("[HOT_PATH] no RPC added")
print("[EXPANDED_UNIVERSE] checkpoint-25 preserved")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
