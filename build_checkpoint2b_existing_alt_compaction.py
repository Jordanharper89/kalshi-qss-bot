from pathlib import Path

ROOT=Path.cwd()
P=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/checkpoint2b_existing_alt_compaction.py"
T=ROOT/"test_checkpoint2b_existing_alt_compaction.py"

P.write_text(r'''
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r

def main():
    root=Path.cwd()

    state,_=r.q25.prepare_once(root)
    r.q25.bind_cached_state(state)

    warmed=r.install_proven_hot_math(state)

    _,r.USER=r.q87.c.sim_identity()

    r.prebuild_templates(state,r.USER)
    r.prebuild_meteora_templates(state,r.USER,warmed)

    for pair in state.get("pairs") or []:
        token=str(pair.token)

        if token not in r.READY_TOKENS:
            continue

        r.q18.worker().warm(
            str(pair.pump_pool)
        )

    try:
        extra_alts=list(
            r.q87.las.q59.recent_mriya_alt_keys()
            or []
        )
    except Exception as exc:
        print(
            "[CHECKPOINT2B_ALT_DISCOVERY_ERROR]",
            type(exc).__name__,
            str(exc),
            flush=True,
        )
        extra_alts=[]

    print(
        "[CHECKPOINT2B_EXISTING_ALTS]",
        len(extra_alts),
        flush=True,
    )

    r.BLOCKHASH.start()

    try:
        for pair in state.get("pairs") or []:

            token=str(pair.token)

            if token not in r.READY_TOKENS:
                continue

            snap=r.immutable_snapshot(pair)

            rows=r.q18.exact_snapshot_opportunities(
                snap,
                0.001
            )

            forward=next(
                (
                    x for x in rows
                    if x["direction"]=="PUMP_TO_METEORA"
                ),
                None
            )

            if forward is None:
                continue

            route=r.same_snapshot_route(
                r.USER,
                snap,
                forward,
            )

            candidates=list(
                r.q87.repaired_candidates(
                    route
                )
            )

            blockhash=r.BLOCKHASH.get()

            for candidate in candidates:

                name=str(
                    candidate.get("name","UNKNOWN")
                )

                if "PUMP_METEORA_ONLY" in name:
                    continue

                comp=r.q87.compile_candidate(
                    r.USER,
                    candidate["instructions"],
                    r.q87.alt_sets(
                        route.get("base_alts",[]),
                        extra_alts,
                    ),
                    blockhash,
                )

                print(
                    "[CHECKPOINT2B_COMPILE] "
                    "token=%s candidate=%s ok=%s attempts=%s"
                    %(
                        token[:10],
                        name,
                        comp.get("ok"),
                        comp.get("attempts"),
                    ),
                    flush=True,
                )

                if not comp.get("ok"):
                    continue

                print(
                    "[CHECKPOINT2B_COMPILED] "
                    "token=%s candidate=%s bytes=%d alt_count=%d"
                    %(
                        token[:10],
                        name,
                        len(comp["unsigned"]),
                        len(comp["alts"]),
                    ),
                    flush=True,
                )

                sim=r.simulate_current(
                    {
                        "raw":comp["unsigned"]
                    },
                    r.USER,
                )

                if sim.get("err") is None:
                    print(
                        "[CHECKPOINT2B_FORWARD_ATOMIC_SIM_PASS] "
                        "token=%s candidate=%s bytes=%d alt_count=%d"
                        %(
                            token[:10],
                            name,
                            len(comp["unsigned"]),
                            len(comp["alts"]),
                        ),
                        flush=True,
                    )
                    return 0

                print(
                    "[CHECKPOINT2B_SIM_REJECT] "
                    "token=%s err=%s"
                    %(
                        token[:10],
                        sim.get("err"),
                    ),
                    flush=True,
                )

                r._canonical_sim_logs(sim)

                return 2

            return 2

        raise RuntimeError(
            "NO_READY_FORWARD_PAIR"
        )

    finally:
        r.BLOCKHASH.close()

        if getattr(r.q18,"_worker",None) is not None:
            r.q18._worker.close()
            r.q18._worker=None

        try:
            r.q25.q23.worker().close()
        except Exception:
            pass


if __name__=="__main__":
    raise SystemExit(main())
'''.lstrip(),encoding="utf-8")

T.write_text(r'''
from pathlib import Path
import unittest

P=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/"
    "checkpoint2b_existing_alt_compaction.py"
)

class T(unittest.TestCase):

    def test_existing_alt_only(self):
        s=P.read_text(encoding="utf-8")

        self.assertIn(
            "recent_mriya_alt_keys",
            s
        )

        self.assertIn(
            "alt_sets",
            s
        )

        self.assertIn(
            "CHECKPOINT2B_FORWARD_ATOMIC_SIM_PASS",
            s
        )

    def test_no_broadcast(self):
        s=P.read_text(encoding="utf-8")

        self.assertNotIn(
            "sendTransaction(",
            s
        )

        self.assertNotIn(
            "bootstrap_micro_alt",
            s
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
'''.lstrip(),encoding="utf-8")

print("[PASS] Checkpoint-2B existing ALT compaction installed")
print("[TARGET] compress 1328-byte forward atomic route below 1232")
print("[ALT] existing tables only")
print("[PRIVATE_KEY] not required")
print("[BROADCAST] disabled")