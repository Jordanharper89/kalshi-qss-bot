from pathlib import Path

P=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
s=P.read_text(encoding="utf-8")

old='''            comp=(
                q87.compile_candidate(
                    user,
                    candidate[
                        "instructions"
                    ],
                    [[]],
                    blockhash,
                )
            )
'''

new='''            alt_options=[[]]

            alt_state=Path(
                "runtime_state/oracle/solana_atomic_executor/"
                "canonical_alt.json"
            )

            if alt_state.is_file():
                try:
                    import json
                    row=json.loads(
                        alt_state.read_text(encoding="utf-8")
                    )
                    address=str(row.get("address") or "")
                    if address:
                        alt_options=q87.alt_sets(
                            route.get("base_alts",[]),
                            [address],
                        )
                        print(
                            "[CANONICAL_ALT_REUSE] address=%s"
                            %address,
                            flush=True,
                        )
                except Exception as exc:
                    print(
                        "[CANONICAL_ALT_REUSE_SKIP] %s:%s"
                        %(type(exc).__name__,str(exc)),
                        flush=True,
                    )

            comp=q87.compile_candidate(
                user,
                candidate["instructions"],
                alt_options,
                blockhash,
            )
'''

if old not in s:
    raise RuntimeError("CANONICAL_COMPILE_SEAM_NOT_FOUND")

P.write_text(s.replace(old,new,1),encoding="utf-8")

print("[PASS] canonical runtime ALT reuse installed")
print("[SOURCE] persisted canonical_alt.json")
print("[FALLBACK] no-ALT compile preserved")
print("[BROADCAST] unchanged / disabled")