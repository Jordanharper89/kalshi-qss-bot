"""ORACLE-080 full installer: official Solana v1 fallback after oversized v0.
Original scanner unchanged. No signing, broadcast or private key access.
Requires solders>=0.29.
"""
import ast
import shutil
import sys
from pathlib import Path

PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
V77 = PKG / "oracle_077_native_executor.py"
V54 = PKG / "oracle_054_reverse_native_handoff.py"
V80 = PKG / "oracle_080_v1_atomic_fallback.py"
MARK = "ORACLE080_V1_SIZE_FALLBACK"

ANCHOR77 = """    result = compile_existing_alt(
        user, route, core, q87, root, extra_alt, v51=v51
    )
"""

HOOK = """    # ORACLE080_V1_SIZE_FALLBACK
    if (not result.get('ok') and any(
            'ATOMIC_TX_TOO_LARGE:' in str(a.get('detail', ''))
            for a in (result.get('attempts') or []))):
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_080_v1_atomic_fallback as v80
        result = v80.compile_v1(user, route, core, q87, v51)
"""

MODULE = r'''"""ORACLE-080 official solders MessageV1 compiler. Unsigned only."""
import base64
import struct

MAX_V1 = 4096
MAX_PRIORITY_LAMPORTS = 100000
COMPUTE_PROGRAM = "ComputeBudget111111111111111111111111111111"


def compile_v1(user, route, core, q87, v51):
    from solders.hash import Hash
    from solders.pubkey import Pubkey
    from solders.instruction import Instruction, AccountMeta
    from solders.message import MessageV1, TransactionConfig
    from solders.signature import Signature
    from solders.transaction import VersionedTransaction
    from qseries_v2.oracle_execution.solana_atomic_executor.oracle_072_route_contract import validate_route

    out = {"ok": False, "reason": "HOLD_V1_NOT_LEGAL",
           "attempts": [], "used_alts": [], "version": 1}

    if (not isinstance(route, dict)
            or type(route.get("start_lamports")) is not int
            or route["start_lamports"] < 10000000):
        out["reason"] = "HOLD_BELOW_010_SOL_MINIMUM"
        return out

    token = route.get("token")
    if not isinstance(token, str) or not token:
        out["reason"] = "HOLD_TOKEN_MISSING"
        return out

    try:
        candidates = [
            x for x in q87.repaired_candidates(route)
            if v51.candidate_is_safe(x)
        ]
        if not candidates:
            out["reason"] = "HOLD_NO_NATIVE_CANDIDATE"
            return out

        bh = core.rpc(
            "getLatestBlockhash",
            [{"commitment": "processed"}]
        )["value"]["blockhash"]

        blockhash = Hash.from_string(bh)
        payer = Pubkey.from_string(user)

    except Exception as exc:
        out["reason"] = "HOLD_V1_PREPARE_" + type(exc).__name__
        return out

    for candidate in candidates:
        name = str(candidate.get("name", "UNKNOWN"))
        rows = candidate.get("instructions")

        gate = validate_route(route, core.PUMP, core.DLMM, rows)
        if gate != "ADMITTED":
            out["attempts"].append({
                "candidate": name, "error": gate
            })
            continue

        try:
            instructions = []
            compute_limit = 1400000
            micro_price = 0
            loaded_limit = 64 * 1024 * 1024
            heap = 32768
            seen_budget = set()

            for row in rows:
                program = row["programId"]
                data = base64.b64decode(
                    row["data"], validate=True
                )

                if program == COMPUTE_PROGRAM:
                    if not data:
                        raise ValueError("EMPTY_COMPUTE_BUDGET")

                    kind = data[0]
                    if kind in seen_budget:
                        raise ValueError("DUPLICATE_COMPUTE_BUDGET")
                    seen_budget.add(kind)

                    if kind == 2 and len(data) == 5:
                        compute_limit = struct.unpack_from(
                            "<I", data, 1
                        )[0]
                    elif kind == 3 and len(data) == 9:
                        micro_price = struct.unpack_from(
                            "<Q", data, 1
                        )[0]
                    elif kind == 4 and len(data) == 5:
                        loaded_limit = struct.unpack_from(
                            "<I", data, 1
                        )[0]
                    elif kind == 1 and len(data) == 5:
                        heap = struct.unpack_from(
                            "<I", data, 1
                        )[0]
                    else:
                        raise ValueError(
                            "UNSUPPORTED_COMPUTE_BUDGET_INSTRUCTION"
                        )
                    continue

                accounts = [
                    AccountMeta(
                        Pubkey.from_string(a["pubkey"]),
                        a["isSigner"],
                        a["isWritable"]
                    )
                    for a in row["accounts"]
                ]

                instructions.append(
                    Instruction(
                        Pubkey.from_string(program),
                        data,
                        accounts
                    )
                )

            priority_fee = (
                micro_price * compute_limit + 999999
            ) // 1000000

            if (
                not 1 <= compute_limit <= 1400000
                or not 1 <= loaded_limit <= 64 * 1024 * 1024
                or not 32768 <= heap <= 262144
                or priority_fee > MAX_PRIORITY_LAMPORTS
            ):
                raise ValueError(
                    "INVALID_OR_EXCESSIVE_V1_RESOURCE_BUDGET"
                )

            config = TransactionConfig(
                priority_fee=priority_fee,
                compute_unit_limit=compute_limit,
                loaded_accounts_data_size_limit=loaded_limit,
                heap_size=heap
            )

            message = MessageV1.try_compile(
                payer, instructions, blockhash, config
            )

            unsigned = VersionedTransaction.populate(
                message, [Signature.default()]
            )
            raw = bytes(unsigned)

            if (
                not 1 <= len(raw) <= MAX_V1
                or raw[0] != 0x81
                or raw[-64:] != bytes(64)
            ):
                raise ValueError(
                    "V1_WIRE_SIGNATURE_OR_SIZE_INVALID"
                )

            decoded = VersionedTransaction.from_bytes(raw)
            if not isinstance(decoded.message, MessageV1):
                raise ValueError("V1_WIRE_ROUNDTRIP_INVALID")

            out["attempts"].append({
                "candidate": name,
                "bytes": len(raw),
                "ok": True
            })

            out.update({
                "ok": True,
                "reason": "LEGAL_UNSIGNED_V1",
                "msg": message,
                "raw": raw,
                "bytes": len(raw),
                "candidate": name,
                "start_lamports": route["start_lamports"],
                "token": token,
                "priority_fee_lamports": priority_fee
            })

            print(
                "[ORACLE080_V1_COMPILED] candidate=%s "
                "bytes=%d priority_lamports=%d" % (
                    name, len(raw), priority_fee
                ),
                flush=True
            )
            return out

        except Exception as exc:
            out["attempts"].append({
                "candidate": name,
                "error": type(exc).__name__
            })

    print(
        "[ORACLE080_V1_HOLD] attempted=%d" %
        len(out["attempts"]),
        flush=True
    )
    return out
'''


def preflight():
    from importlib.metadata import version

    installed = version("solders")
    pieces = tuple(int(x) for x in installed.split(".")[:2])

    if pieces < (0, 29):
        raise RuntimeError("SOLDERS_029_OR_NEWER_REQUIRED")

    from solders.message import MessageV1, TransactionConfig
    from solders.transaction import VersionedTransaction

    assert MessageV1 and TransactionConfig and VersionedTransaction
    print("[PASS] OFFICIAL_SOLDERS_V1_SDK", installed)


def transform(source77, source54):
    if source77.count(ANCHOR77) != 1:
        raise RuntimeError("ORACLE077_NATIVE_ANCHOR_MISMATCH")

    old_guard = "assert len(bytes(result.get('raw') or b'')) <= 1232"
    if source77.count(old_guard) != 1:
        raise RuntimeError("ORACLE077_SIZE_GUARD_MISMATCH")

    old54 = 'if int(compiled["bytes"]) > LIMIT:'
    if source54.count(old54) != 1:
        raise RuntimeError("ORACLE054_SIZE_GUARD_MISMATCH")

    new77 = source77.replace(
        ANCHOR77, ANCHOR77 + HOOK, 1
    )
    new77 = new77.replace(
        old_guard,
        "assert len(bytes(result.get('raw') or b'')) <= "
        "(4096 if result.get('version') == 1 else 1232)",
        1
    )

    new54 = source54.replace(
        old54,
        'if int(compiled["bytes"]) > '
        '(4096 if compiled.get("version") == 1 else LIMIT):',
        1
    )

    ast.parse(new77)
    ast.parse(new54)
    ast.parse(MODULE)
    return new77, new54


def check():
    preflight()

    for path in (V77, V54, V80):
        ast.parse(path.read_text(encoding="utf-8"))

    if MARK not in V77.read_text(encoding="utf-8"):
        raise RuntimeError("ORACLE080_NOT_INSTALLED")

    from types import SimpleNamespace
    from qseries_v2.oracle_execution.solana_atomic_executor.oracle_080_v1_atomic_fallback import compile_v1

    program_a = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    program_b = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"

    rows = [
        {"programId": p, "accounts": [], "data": ""}
        for p in (program_a, program_b)
    ]

    class FakeCore:
        PUMP, DLMM = program_a, program_b

        def rpc(self, method, params):
            assert method == "getLatestBlockhash"
            return {
                "value": {
                    "blockhash": "11111111111111111111111111111111"
                }
            }

    q87 = SimpleNamespace(
        repaired_candidates=lambda route: [
            {"name": "FULL", "instructions": rows}
        ]
    )
    v51 = SimpleNamespace(
        candidate_is_safe=lambda row: True
    )

    result = compile_v1(
        "11111111111111111111111111111111",
        {"start_lamports": 10000000, "token": "fixture"},
        FakeCore(), q87, v51
    )

    if not result.get("ok") or result.get("version") != 1:
        raise RuntimeError("ORACLE080_OFFICIAL_SDK_WIRE_TEST_FAILED")

    print(
        "[PASS] ORACLE080_OFFICIAL_SDK_V1_UNSIGNED_PACKET",
        result["bytes"]
    )
    print("[BOUNDARY] NO_RPC_NO_SIGNING_NO_BROADCAST_IN_TEST")


def install():
    dependencies = (
        V77,
        V54,
        PKG / "oracle_072_route_contract.py"
    )
    if not all(p.is_file() for p in dependencies):
        raise RuntimeError("MISSING_ORACLE079_DEPENDENCY")

    if MARK in V77.read_text(encoding="utf-8"):
        check()
        return

    preflight()

    originals = {
        p: p.read_text(encoding="utf-8")
        for p in (V77, V54)
    }
    new77, new54 = transform(
        originals[V77], originals[V54]
    )

    if V80.exists() and V80.read_text(encoding="utf-8") != MODULE:
        raise RuntimeError("ORACLE080_MODULE_CONFLICT")

    for path in (V77, V54):
        backup = path.with_name(
            path.stem + ".before_oracle080.py"
        )
        if (
            backup.exists()
            and backup.read_text(encoding="utf-8") != originals[path]
        ):
            raise RuntimeError("ORACLE080_BACKUP_CONFLICT")
        if not backup.exists():
            shutil.copy2(path, backup)

    created = not V80.exists()

    try:
        V80.write_text(MODULE, encoding="utf-8")
        V77.write_text(new77, encoding="utf-8")
        V54.write_text(new54, encoding="utf-8")
        check()
    except Exception:
        for path, original in originals.items():
            path.write_text(original, encoding="utf-8")
        if created:
            V80.unlink(missing_ok=True)
        print("[ROLLBACK] ORACLE080_RESTORED")
        raise

    print("[PASS] ORACLE080_V0_FIRST_V1_FALLBACK_INSTALLED")
    print("[PATH] ORIGINAL_SCANNER -> ORACLE077 -> V0_OR_V1 -> UNSIGNED_SIM")
    print("[BOUNDARY] SIGNING_FALSE_BROADCAST_FALSE")


if __name__ == "__main__":
    if "--test" in sys.argv:
        check()
    else:
        install()