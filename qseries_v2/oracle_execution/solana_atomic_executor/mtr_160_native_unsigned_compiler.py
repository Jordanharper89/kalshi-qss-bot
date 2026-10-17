"""MTR-160: use original core.compile_v0 with offline ALT injection.

No secret access, signing, broadcasting or market RPC. Fixture results do not
certify real two-leg atomic protection or on-chain ALT freshness.
"""
import base64
import json
import types
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
from .mtr_158_unsigned_compiled_handoff import validate, HandoffHold

CANONICAL = "HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r"

class UnsignedCompileHold(ValueError):
    pass

def compile_unsigned(payer, instructions, blockhash, alt_snapshot):
    """alt_snapshot maps public table IDs to ordered lists of public account IDs."""
    if not isinstance(alt_snapshot, dict) or CANONICAL not in alt_snapshot:
        raise UnsignedCompileHold("CANONICAL_ALT_SNAPSHOT_REQUIRED")
    if not isinstance(instructions, (list, tuple)) or not instructions:
        raise UnsignedCompileHold("NATIVE_INSTRUCTIONS_REQUIRED")
    if not isinstance(payer, str) or not isinstance(blockhash, str):
        raise UnsignedCompileHold("PUBLIC_PAYER_AND_BLOCKHASH_REQUIRED")
    if not callable(getattr(core, "compile_v0", None)):
        raise UnsignedCompileHold("OFFICIAL_NATIVE_COMPILER_MISSING")
    # Fail closed if original compiler has changed in its trusted call structure.
    code = core.compile_v0.__code__
    if ("alt_accounts" not in code.co_names or
        "signed_tx" in code.co_names or
        "keypair" in code.co_names or
        "rpc" in code.co_names):
        raise UnsignedCompileHold("COMPILER_SAFETY_CONTRACT_CHANGED")
    frozen = {}
    try:
        for table, addresses in alt_snapshot.items():
            if not isinstance(table, str) or not isinstance(addresses, (list, tuple)):
                raise ValueError("invalid lookup table snapshot")
            if len(addresses) > 256 or len(set(addresses)) != len(addresses):
                raise ValueError("duplicate or oversized ALT")
            frozen[table] = tuple(core.b58d(a) for a in addresses)
            if any(len(a) != 32 for a in frozen[table]):
                raise ValueError("invalid ALT pubkey")
        # Independent per-call function globals: does not monkeypatch core.
        isolated_globals = dict(core.compile_v0.__globals__)
        isolated_globals["alt_accounts"] = lambda keys: {
            k: frozen[k] for k in keys if k in frozen
        }
        # Explicitly make any accidental future sensitive dependency unusable.
        for name in ("keypair", "signed_tx", "send", "simulate", "rpc"):
            isolated_globals[name] = lambda *a, **kw: (
                _raise_forbidden(name))
        original = types.FunctionType(code, isolated_globals,
                                      name=core.compile_v0.__name__,
                                      argdefs=core.compile_v0.__defaults__,
                                      closure=core.compile_v0.__closure__)
        msg, raw = original(payer, list(instructions), [CANONICAL], blockhash)
        if not isinstance(msg, bytes) or not isinstance(raw, bytes):
            raise ValueError("invalid compiled result")
        if not raw.endswith(msg):
            raise ValueError("message byte mismatch")
        details = validate(raw)
        return {"message": msg, "raw": raw,
                "sha256": details["sha256"], "details": details}
    except UnsignedCompileHold:
        raise
    except (Exception,) as exc:
        raise UnsignedCompileHold("OFFLINE_UNSIGNED_COMPILATION_FAILED") from exc

def _raise_forbidden(_name):
    raise UnsignedCompileHold("FORBIDDEN_EXECUTION_DEPENDENCY")

def main():
    print("[MTR160] ORIGINAL_NATIVE_COMPILE_V0_OFFLINE_ADAPTER_READY")
    print("[OFFLINE_ALT_INPUT] REQUIRED")
    print("[UNSIGNED_REAL_TRANSACTION] NOT_YET_PRODUCED")
    print("[ACTUAL_ALT_FRESHNESS] NOT_VERIFIED_BY_THIS_BUILD")
    print("[ATOMIC_TWO_LEG_PROOF] FALSE")
    print("[PROTECTED_PROFIT] FALSE")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

if __name__ == "__main__":
    main()
