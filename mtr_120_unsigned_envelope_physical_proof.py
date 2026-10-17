from __future__ import annotations
import base64, hashlib, json
from pathlib import Path

import mtr_119_canonical_alt_atomic_preflight as m119

OUT = Path("mtr_120_unsigned_envelope_physical_proof.json")
ORIG = m119.sae.simulate_current
ST = {"calls": 0, "zero_before": 0, "dummy_after": 0}

def simulate_nonsecret_envelope(compiled, user):
    raw = bytearray(compiled["raw"])

    # Canonical compile_v0 format:
    # byte 0 = shortvec signature count (1)
    # bytes 1:65 = one 64-byte signature.
    if len(raw) < 66:
        raise RuntimeError("MTR120_TX_TOO_SHORT")

    if raw[0] != 1:
        raise RuntimeError("MTR120_SIGNATURE_COUNT_NOT_ONE:%d" % raw[0])

    ST["calls"] += 1

    if bytes(raw[1:65]) == b"\0" * 64:
        ST["zero_before"] += 1
    else:
        raise RuntimeError("MTR120_EXPECTED_ZERO_UNSIGNED_SIGNATURE")

    # Deterministic, non-secret, deliberately invalid cryptographic signature.
    # sigVerify=False means it is NEVER treated as execution authorization.
    dummy = hashlib.sha512(
        b"Q_SERIES_MTR120_UNSIGNED_SIMULATION_ENVELOPE"
        + bytes(compiled["msg"])
    ).digest()

    raw[1:65] = dummy

    if bytes(raw[1:65]) != b"\0" * 64:
        ST["dummy_after"] += 1

    result = m119.sae.q87.c.rpc(
        "simulateTransaction",
        [
            base64.b64encode(bytes(raw)).decode(),
            {
                "encoding": "base64",
                "sigVerify": False,
                "commitment": "processed",
                "accounts": {
                    "encoding": "base64",
                    "addresses": [user],
                },
            },
        ],
    )

    if not isinstance(result, dict):
        raise RuntimeError("MTR120_SIM_RESULT_NOT_MAPPING")

    value = result.get("value")
    if not isinstance(value, dict):
        raise RuntimeError("MTR120_SIM_VALUE_NOT_MAPPING")

    sim = {
        "err": value.get("err"),
        "units": value.get("unitsConsumed"),
        "logs": list(value.get("logs") or []),
        "accounts": list(value.get("accounts") or []),
        "context": result.get("context"),
    }

    print(
        "[MTR120_ENVELOPE] bytes=%d zero_before=True "
        "dummy_nonsecret=True sigVerify=False err=%s units=%s"
        % (len(raw), sim["err"], sim["units"]),
        flush=True,
    )

    return sim

def main():
    print("[MTR-120] START", flush=True)
    print("[BOUNDARY] unsigned simulation envelope only", flush=True)
    print("[SIGNATURE] deterministic non-secret dummy", flush=True)
    print("[SIGVERIFY] FALSE", flush=True)
    print("[PRIVATE_KEY] NOT_USED", flush=True)
    print("[BROADCAST] FALSE", flush=True)

    m119.sae.simulate_current = simulate_nonsecret_envelope
    m119.OUT = Path("mtr_120_underlying_atomic_preflight.json")

    m119.main()

    src = json.loads(m119.OUT.read_text(encoding="utf-8"))

    passed = int(src.get("atomic_pass") or 0) > 0

    report = {
        "mtr": "MTR-120",
        "simulation_calls": ST["calls"],
        "zero_signatures_observed": ST["zero_before"],
        "dummy_envelopes_built": ST["dummy_after"],
        "atomic_attempts": src.get("atomic_attempts"),
        "compiled": src.get("compiled"),
        "simulated": src.get("simulated"),
        "atomic_pass": src.get("atomic_pass"),
        "atomic_rows": src.get("atomic_rows"),
        "execution_authority": False,
        "private_key_used": False,
        "signing": False,
        "broadcast": False,
    }

    OUT.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )

    print(
        "[MTR120_SUMMARY] calls=%d zero_before=%d dummy_after=%d "
        "attempts=%s compiled=%s simulated=%s atomic_pass=%s"
        % (
            ST["calls"], ST["zero_before"], ST["dummy_after"],
            report["atomic_attempts"], report["compiled"],
            report["simulated"], report["atomic_pass"],
        ),
        flush=True,
    )

    if passed:
        print("[RESULT] UNSIGNED_ENVELOPE_ATOMIC_TWO_LEG_PASS", flush=True)
    elif ST["calls"]:
        print("[RESULT] ENVELOPE_ACCEPTED_OR_NEXT_PHYSICAL_BLOCKER_EXPOSED", flush=True)
    else:
        print("[RESULT] NO_FRESH_P2M_010_POSITIVE_IN_WINDOW", flush=True)

    print("[OUTPUT] %s" % OUT, flush=True)
    print("[PRIVATE_KEY] NOT_USED", flush=True)
    print("[SIGNING] FALSE", flush=True)
    print("[BROADCAST] FALSE", flush=True)
    print("[MTR-120] COMPLETE", flush=True)

if __name__ == "__main__":
    main()
