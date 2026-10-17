"""MTR-158: unsigned compiled-v0 transaction artifact handoff. Offline only."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from .mtr_153_v0_alt_account_resolver import _parse_v0
from .mtr_157_canonical_compiled_v0_handoff import CANONICAL

class HandoffHold(ValueError):
    pass

def validate(raw):
    if type(raw) is not bytes or not 1 <= len(raw) <= 1232:
        raise HandoffHold("INVALID_TRANSACTION_SIZE")
    # Only an unsigned placeholder-signature envelope may be exported.
    try:
        from .mtr_152_native_envelope_inspector import _short
        n, offset = _short(raw, 0)
        if not 1 <= n <= 64 or offset + n * 64 >= len(raw):
            raise HandoffHold("INVALID_SIGNATURE_SECTION")
        if any(raw[offset:offset + n * 64]):
            raise HandoffHold("SIGNED_TRANSACTION_REJECTED")
        static, ins, lookups = _parse_v0(raw)
    except HandoffHold:
        raise
    except Exception as exc:
        raise HandoffHold("INVALID_V0_ENVELOPE") from exc
    if not lookups or CANONICAL not in [t for t, _, _ in lookups]:
        raise HandoffHold("CANONICAL_ALT_NOT_REFERENCED")
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "instruction_count": len(ins),
        "table_ids": [t for t, _, _ in lookups],
        "unsigned_placeholder": True,
        "protected_bounds_verified": False,
        "atomic_two_leg_proven": False,
        "broadcast_authorized": False,
    }

def stage(source, output_dir):
    source = Path(source)
    # Explicit source only; never search folders or invoke compiler/signer.
    if not source.is_file() or source.stat().st_size > 4096:
        raise HandoffHold("SOURCE_MISSING_OR_TOO_LARGE")
    try:
        raw = base64.b64decode(source.read_text(encoding="ascii").strip(), validate=True)
    except Exception as exc:
        raise HandoffHold("INVALID_BASE64") from exc
    report = validate(raw)
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    tx = directory / "mtr_158_unsigned_compiled_v0.b64"
    evidence = directory / "mtr_158_unsigned_compiled_v0.json"
    tx.write_text(base64.b64encode(raw).decode("ascii") + "\n", encoding="ascii")
    evidence.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report, tx, evidence

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-base64-file", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path.cwd() / "runtime_state/oracle/oracle_live_execution")
    args = parser.parse_args(argv)
    if args.input_base64_file:
        try:
            report, tx, evidence = stage(args.input_base64_file, args.output_dir)
        except HandoffHold as exc:
            raise SystemExit("[HOLD] " + str(exc)) from exc
        print("[MTR158_TX_SHA256]", report["sha256"])
        print("[MTR158_ARTIFACT]", tx)
        print("[MTR158_EVIDENCE]", evidence)
        print("[MTR158_ALT_REF]", ",".join(report["table_ids"]))
        print("[MTR158_LINK] OFFLINE_ARTIFACT_READY")
    else:
        print("[MTR158] UNSIGNED_COMPILED_ARTIFACT_HANDOFF_READY")
        print("[MTR158_LINK] HOLD_NO_COMPILED_INPUT")
    print("[COMPILER_INVOKED] FALSE")
    print("[RPC] NOT_CALLED")
    print("[PROTECTED_PROFIT] FALSE")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

if __name__ == "__main__":
    main()
