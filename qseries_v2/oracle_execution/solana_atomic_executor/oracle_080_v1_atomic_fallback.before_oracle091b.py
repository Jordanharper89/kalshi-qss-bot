"""ORACLE-080 official solders MessageV1 compiler. Unsigned only."""
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
