"""MTR-156 transaction-specific ALT proof binding. Read-only; no RPC in default mode."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from .mtr_153_v0_alt_account_resolver import _parse_v0
from .mtr_154_trusted_alt_rpc_evidence import verify_transaction_tables, rpc_table, ALTProofError

CANONICAL_ALT = "HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r"

class LinkError(ValueError):
    pass

def bind(raw, read_table, expected_table=CANONICAL_ALT):
    if not isinstance(raw, bytes):
        raise LinkError("RAW_TRANSACTION_REQUIRED")
    try:
        _, instructions, refs = _parse_v0(raw)
        if not refs:
            raise LinkError("NO_LOOKUP_REFERENCES")
        if expected_table not in [key for key, _, _ in refs]:
            raise LinkError("CANONICAL_ALT_NOT_REFERENCED")
        proof = verify_transaction_tables(raw, read_table)
        rows = proof["rpc_proofs"]
        if len(rows) != len(refs):
            raise LinkError("INCOMPLETE_PROOF")
        if any(p["table"] != ref[0] for p, ref in zip(rows, refs)):
            raise LinkError("LOOKUP_PROOF_ORDER_MISMATCH")
        if any(not p["owner_checked"] or not p["active_at_rpc_slot"] for p in rows):
            raise LinkError("INVALID_ALT_PROOF")
        slots = tuple(p["rpc_slot"] for p in rows)
        if any(type(x) is not int or x <= 0 for x in slots):
            raise LinkError("INVALID_RPC_SLOT")
        if any(p["last_extended_slot"] >= p["rpc_slot"] for p in rows):
            raise LinkError("ALT_EXTENSION_NOT_MATURE")
        if len(proof["resolved"]["instructions"]) != len(instructions):
            raise LinkError("INSTRUCTION_COUNT_MISMATCH")
        return MappingProxyType({
            "status": "TRANSACTION_ALT_LINKED_RPC_CONDITIONAL",
            "transaction_sha256": hashlib.sha256(raw).hexdigest(),
            "table_ids": tuple(p["table"] for p in rows),
            "table_hashes": tuple(p["raw_sha256"] for p in rows),
            "finalized_slots": slots,
            "resolved_instruction_count": len(instructions),
            "atomic_two_leg_proven": False,
            "protected_profit_certified": False,
            "signing_authorized": False,
            "broadcast_authorized": False
        })
    except LinkError:
        raise
    except Exception as exc:
        raise LinkError("TRANSACTION_ALT_VERIFICATION_FAILED") from exc

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--transaction-base64-file", type=Path)
    ap.add_argument("--rpc", default="https://api.mainnet-beta.solana.com")
    args=ap.parse_args(argv)
    if args.transaction_base64_file:
        encoded=args.transaction_base64_file.read_text(encoding="ascii").strip()
        try:
            raw=base64.b64decode(encoded, validate=True)
        except Exception as exc:
            raise SystemExit("[HOLD] Invalid base64 transaction file") from exc
        if len(raw)>1232:
            raise SystemExit("[HOLD] Transaction exceeds Solana size limit")
        try:
            proof=bind(raw, lambda table: rpc_table(args.rpc, table))
        except LinkError as exc:
            raise SystemExit("[HOLD] "+str(exc)) from exc
        print("[MTR156_TX_SHA256]", proof["transaction_sha256"])
        print("[MTR156_TABLES]", ",".join(proof["table_ids"]))
        print("[MTR156_FINALIZED_SLOTS]", ",".join(map(str,proof["finalized_slots"])))
        print("[MTR156_LOOKUP_LINK]", proof["status"])
    else:
        print("[MTR156] TRANSACTION_SPECIFIC_ALT_LINKER_READY")
        print("[MTR156_LINK] NOT_RUN_NO_COMPILED_TRANSACTION")
    print("[ATOMIC_TWO_LEG_PROOF] FALSE")
    print("[PROTECTED_PROFIT] FALSE")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

if __name__=="__main__":
    main()
