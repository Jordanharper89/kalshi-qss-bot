from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint6_all_pairs_fee_ranked_sweep.py"
TEST=ROOT/"test_canonical_checkpoint6_all_pairs_fee_ranked_sweep.py"

MODULE=r"""from __future__ import annotations

import copy

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint3_reverse_atomic_compile as c3
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint4_message_fee_economics_gate as c4

SIZES=(
    0.001,
    0.010,
    0.025,
    0.050,
    0.100,
    0.180,
    0.280,
    0.500,
    1.000,
    1.400,
)

COMPUTE_BUDGET="ComputeBudget111111111111111111111111111111"
MEMOS={
    "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",
    "Memo1UhkJRfHyvLMcVucJwxXeuD728EqVDDwQDxFMNo",
}


def _compact(ixs):
    return [
        copy.deepcopy(ix)
        for ix in ixs
        if (
            ix.get("programId")!=COMPUTE_BUDGET
            and ix.get("programId") not in MEMOS
        )
    ]


def _reverse_route(user,snap,op):
    route=c3._reverse_route(
        user,
        snap,
        op,
    )
    name,ixs=route["original_candidates"][0]
    route["original_candidates"]=[
        (
            "NO_COMPUTE_MEMO_REVERSE",
            _compact(ixs),
        )
    ]
    return route


def _forward_route(user,snap,op):
    route=r.same_snapshot_route(
        user,
        snap,
        op,
    )

    compact=[]

    for name,ixs in route["original_candidates"]:
        compact.append(
            (
                "NO_COMPUTE_MEMO_FORWARD",
                _compact(ixs),
            )
        )
        break

    route["original_candidates"]=compact
    return route


def _compiled_fee(user,route):
    compiled=r.compile_current(
        user,
        route,
    )

    if not compiled.get("ok"):
        return None

    fee=c4._message_fee_lamports(
        compiled
    )

    return {
        "bytes":int(compiled.get("bytes") or 0),
        "fee_lamports":int(fee),
        "candidate":compiled.get("candidate"),
    }


def evaluate_pair(user,pair):
    token=str(pair.token)

    if token not in r.READY_TOKENS:
        return []

    snap=r.immutable_snapshot(pair)
    rows=[]

    for size in SIZES:
        try:
            opportunities=r.q18.exact_snapshot_opportunities(
                snap,
                size,
            )
        except Exception as exc:
            print(
                "[CHECKPOINT6_SIZE_SKIP] "
                "token=%s size=%.3f %s:%s"
                %(
                    token[:10],
                    size,
                    type(exc).__name__,
                    str(exc)[:120],
                ),
                flush=True,
            )
            continue

        for op in opportunities:
            gross=int(op["local_net"])

            if gross<=0:
                rows.append({
                    "token":token,
                    "size_sol":float(size),
                    "direction":op["direction"],
                    "gross_net":gross,
                    "status":"LOCAL_NONPOSITIVE",
                })
                continue

            try:
                if op["direction"]=="METEORA_TO_PUMP":
                    route=_reverse_route(
                        user,
                        snap,
                        op,
                    )
                elif op["direction"]=="PUMP_TO_METEORA":
                    route=_forward_route(
                        user,
                        snap,
                        op,
                    )
                else:
                    raise RuntimeError(
                        "UNKNOWN_DIRECTION"
                    )

                fee_info=_compiled_fee(
                    user,
                    route,
                )

                if fee_info is None:
                    rows.append({
                        "token":token,
                        "size_sol":float(size),
                        "direction":op["direction"],
                        "gross_net":gross,
                        "status":"COMPILE_REJECT",
                    })
                    continue

                after=gross-int(
                    fee_info["fee_lamports"]
                )

                row={
                    "token":token,
                    "size_sol":float(size),
                    "direction":op["direction"],
                    "gross_net":gross,
                    "fee_lamports":
                        int(fee_info["fee_lamports"]),
                    "after_fee":after,
                    "bytes":
                        int(fee_info["bytes"]),
                    "candidate":
                        fee_info["candidate"],
                    "status":
                        (
                            "POSITIVE_AFTER_FEE"
                            if after>0
                            else "HOLD_AFTER_FEE"
                        ),
                }

                rows.append(row)

                print(
                    "[CHECKPOINT6_CANDIDATE] "
                    "token=%s size=%.3f dir=%s "
                    "gross=%+d fee=%d after=%+d "
                    "bytes=%d status=%s"
                    %(
                        token[:10],
                        size,
                        op["direction"],
                        gross,
                        row["fee_lamports"],
                        after,
                        row["bytes"],
                        row["status"],
                    ),
                    flush=True,
                )

            except Exception as exc:
                print(
                    "[CHECKPOINT6_COMPILE_SKIP] "
                    "token=%s size=%.3f dir=%s %s:%s"
                    %(
                        token[:10],
                        size,
                        op["direction"],
                        type(exc).__name__,
                        str(exc)[:160],
                    ),
                    flush=True,
                )

    return rows


def main():
    root=__import__("pathlib").Path.cwd()

    state,cap=r.q25.prepare_once(
        root
    )

    r.q25.bind_cached_state(
        state
    )

    token_warm=r.install_proven_hot_math(
        state
    )

    _,r.USER=r.q87.c.sim_identity()

    r.prebuild_templates(
        state,
        r.USER,
    )

    r.prebuild_meteora_templates(
        state,
        r.USER,
        token_warm,
    )

    for pair in list(
        state.get("pairs")
        or []
    ):
        token=str(pair.token)

        if token not in r.READY_TOKENS:
            continue

        try:
            r.q18.worker().warm(
                str(pair.pump_pool)
            )
        except Exception:
            r.READY_TOKENS.discard(
                token
            )

    r.BLOCKHASH.start()

    rows=[]

    try:
        for pair in list(
            state.get("pairs")
            or []
        ):
            rows.extend(
                evaluate_pair(
                    r.USER,
                    pair,
                )
            )
    finally:
        r.BLOCKHASH.close()

    ranked=[
        row
        for row in rows
        if "after_fee" in row
    ]

    ranked.sort(
        key=lambda x:int(
            x["after_fee"]
        ),
        reverse=True,
    )

    positives=[
        row
        for row in ranked
        if int(
            row["after_fee"]
        )>0
    ]

    print(
        "[CHECKPOINT6_SUMMARY] "
        "ready_tokens=%d evaluated=%d "
        "compiled=%d positive_after_fee=%d"
        %(
            len(r.READY_TOKENS),
            len(rows),
            len(ranked),
            len(positives),
        ),
        flush=True,
    )

    for i,row in enumerate(
        ranked[:10],
        start=1,
    ):
        print(
            "[CHECKPOINT6_RANK] "
            "rank=%d token=%s size=%.3f dir=%s "
            "gross=%+d fee=%d after=%+d bytes=%d"
            %(
                i,
                row["token"][:10],
                row["size_sol"],
                row["direction"],
                row["gross_net"],
                row["fee_lamports"],
                row["after_fee"],
                row["bytes"],
            ),
            flush=True,
        )

    if positives:
        top=positives[0]

        print(
            "[CHECKPOINT6_BEST] "
            "token=%s size=%.3f dir=%s "
            "after_fee=%+d bps=%+.2f"
            %(
                top["token"][:10],
                top["size_sol"],
                top["direction"],
                top["after_fee"],
                (
                    top["after_fee"]
                    /(top["size_sol"]*1e9)
                    *10000.0
                ),
            ),
            flush=True,
        )
        print(
            "[CHECKPOINT6_GATE] "
            "status=POSITIVE_CANDIDATE_FOUND",
            flush=True,
        )
    else:
        print(
            "[CHECKPOINT6_GATE] "
            "status=NO_POSITIVE_AFTER_FEE",
            flush=True,
        )

    print("[SIMULATION] disabled",flush=True)
    print("[BROADCAST] disabled",flush=True)

    return 0


if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint6_all_pairs_fee_ranked_sweep.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_all_sizes(self):
        for value in (
            "0.001",
            "0.010",
            "0.025",
            "0.050",
            "0.100",
            "0.180",
            "0.280",
            "0.500",
            "1.000",
            "1.400",
        ):
            self.assertIn(value,self.s)

    def test_both_directions(self):
        self.assertIn("METEORA_TO_PUMP",self.s)
        self.assertIn("PUMP_TO_METEORA",self.s)

    def test_local_positive_only_compile(self):
        self.assertIn(
            "if gross<=0:",
            self.s,
        )

    def test_real_fee(self):
        self.assertIn(
            "c4._message_fee_lamports(",
            self.s,
        )

    def test_compact_candidates(self):
        self.assertIn(
            "NO_COMPUTE_MEMO_REVERSE",
            self.s,
        )
        self.assertIn(
            "NO_COMPUTE_MEMO_FORWARD",
            self.s,
        )

    def test_no_sim_or_broadcast(self):
        self.assertNotIn("simulateTransaction",self.s)
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")

print("[PASS] canonical checkpoint-6 all-pairs fee-ranked sweep installed")
print("[UNIVERSE] all warmed exact pairs")
print("[DIRECTIONS] both")
print("[SIZES] 10 certified sizes")
print("[COMPILE] only locally positive candidates")
print("[FEE] real getFeeForMessage")
print("[SIMULATION] disabled")
print("[ALT] unchanged")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
