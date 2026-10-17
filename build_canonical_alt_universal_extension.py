from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "oracle_execution" / "solana_atomic_executor"
TARGET = PKG / "canonical_alt_universal_extension.py"
TEST = ROOT / "test_canonical_alt_universal_extension.py"

MODULE = r"""from __future__ import annotations

import argparse
import base64
import json
import os
import struct
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

ALT_PROGRAM = "AddressLookupTab1e1111111111111111111111111"
SYSTEM_PROGRAM = "11111111111111111111111111111111"

STATE = Path("runtime_state/oracle/solana_atomic_executor/canonical_alt.json")
AUDIT = Path("runtime_state/oracle/solana_atomic_executor/canonical_alt_universal_extension.json")

EXPECTED_ALT = "HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r"

UNIVERSAL_SHARED = [
    "8axdqvEoZ5YkV1yGw5Cmsx9pkeVve4cM9wAkZfhPcRDp",
    "Hvb4rCzCrUHxijoopBfN8q4SRmVeeKfPSEKKWGKMAfHZ",
    "5PHirr8joyTMp9JMm6nW7hNDVyEYdkzDqazxPD7RaTjx",
    "C2aFPdENg4A2HQsmrd5rTw5TaYBX5Ku887cWjbFKtZpw",
    "D1ZN9Wj1fRSUQfCjhvnu1hqDMT7hzjzBBpi12nVniYD6",
    "GS4CU59F31iL7aR2Q8zVS8DRrcRnXX1yjQ66TqNVQnaR",
    "pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ",
    "GAFuhgcd328SkkBYHpfadzmef9hTGAFRCi9QoCnsZQug",
    "9M4giFFMxmFGXtc3feFzRai56WbBqehoSeRE5GK7gf7",
]

ARM_VALUE = "EXTEND_CANONICAL_ALT_UNIVERSAL"


def _save(payload):
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    tmp = AUDIT.with_suffix(AUDIT.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(AUDIT)


def _state_alt():
    if not STATE.exists():
        raise RuntimeError("CANONICAL_ALT_STATE_MISSING")

    obj = json.loads(STATE.read_text(encoding="utf-8"))

    for key in (
        "address",
        "alt_address",
        "lookup_table",
        "lookup_table_address",
        "table",
    ):
        value = obj.get(key) if isinstance(obj, dict) else None
        if isinstance(value, str) and value.strip():
            return value.strip()

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                z = walk(v)
                if z:
                    return z
        elif isinstance(x, list):
            for v in x:
                z = walk(v)
                if z:
                    return z
        elif isinstance(x, str):
            try:
                if len(c.b58d(x.strip())) == 32:
                    return x.strip()
            except Exception:
                pass
        return None

    found = walk(obj)
    if not found:
        raise RuntimeError("CANONICAL_ALT_ADDRESS_NOT_FOUND")
    return found


def _read_alt(address):
    row = c.rpc(
        "getAccountInfo",
        [address, {"encoding": "base64", "commitment": "processed"}],
    )
    value = row.get("value") if isinstance(row, dict) else None

    if not isinstance(value, dict):
        raise RuntimeError("ALT_ACCOUNT_MISSING:" + address)

    if str(value.get("owner") or "") != ALT_PROGRAM:
        raise RuntimeError("ALT_OWNER_MISMATCH:" + str(value.get("owner")))

    data = value.get("data") or []
    if not isinstance(data, list) or not data:
        raise RuntimeError("ALT_BAD_DATA")

    raw = base64.b64decode(data[0])
    if len(raw) < 56 or (len(raw) - 56) % 32:
        raise RuntimeError("ALT_BAD_BINARY_LENGTH:" + str(len(raw)))

    addresses = [
        c.b58e(raw[i:i + 32])
        for i in range(56, len(raw), 32)
    ]

    return addresses


def _extend_ix(table, authority, addresses):
    # Solana Address Lookup Table program:
    # enum discriminant ExtendLookupTable = 2 (u32 LE)
    # Vec<Pubkey> = u64 LE count + packed pubkeys.
    data = (
        struct.pack("<I", 2)
        + struct.pack("<Q", len(addresses))
        + b"".join(c.b58d(x) for x in addresses)
    )

    return {
        "programId": ALT_PROGRAM,
        "accounts": [
            {
                "pubkey": table,
                "isSigner": False,
                "isWritable": True,
            },
            {
                "pubkey": authority,
                "isSigner": True,
                "isWritable": False,
            },
            {
                "pubkey": authority,
                "isSigner": True,
                "isWritable": True,
            },
            {
                "pubkey": SYSTEM_PROGRAM,
                "isSigner": False,
                "isWritable": False,
            },
        ],
        "data": base64.b64encode(data).decode(),
    }


def _latest_blockhash():
    row = c.rpc(
        "getLatestBlockhash",
        [{"commitment": "processed"}],
    )
    value = row.get("value") if isinstance(row, dict) else None
    if not isinstance(value, dict) or not value.get("blockhash"):
        raise RuntimeError("BAD_BLOCKHASH")
    return str(value["blockhash"])


def _simulate(raw, user):
    row = c.rpc(
        "simulateTransaction",
        [
            base64.b64encode(raw).decode(),
            {
                "encoding": "base64",
                "sigVerify": True,
                "commitment": "processed",
                "accounts": {
                    "encoding": "base64",
                    "addresses": [user],
                },
            },
        ],
    )

    value = row.get("value") if isinstance(row, dict) else None
    if not isinstance(value, dict):
        raise RuntimeError("SIM_VALUE_MISSING")

    return {
        "err": value.get("err"),
        "units": value.get("unitsConsumed"),
        "logs": list(value.get("logs") or []),
    }


def _confirm(signature, timeout_s=40.0):
    deadline = time.monotonic() + float(timeout_s)

    while time.monotonic() < deadline:
        row = c.rpc(
            "getSignatureStatuses",
            [[signature], {"searchTransactionHistory": True}],
        )
        value = row.get("value") if isinstance(row, dict) else None
        status = value[0] if isinstance(value, list) and value else None

        if isinstance(status, dict):
            if status.get("err") is not None:
                raise RuntimeError("ALT_EXTENSION_CHAIN_ERROR:" + str(status["err"]))

            confirmation = status.get("confirmationStatus")
            if confirmation in ("confirmed", "finalized"):
                return confirmation

        time.sleep(0.5)

    raise RuntimeError("ALT_EXTENSION_CONFIRM_TIMEOUT")


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--extend", action="store_true")
    args = p.parse_args(argv)

    table = _state_alt()
    if table != EXPECTED_ALT:
        raise RuntimeError(
            "CANONICAL_ALT_IDENTITY_MISMATCH:%s!=%s"
            % (table, EXPECTED_ALT)
        )

    before = _read_alt(table)
    missing = [x for x in UNIVERSAL_SHARED if x not in before]

    print(
        "[CANONICAL_ALT_EXTENSION_PLAN] table=%s existing=%d target_shared=%d missing=%d"
        % (table, len(before), len(UNIVERSAL_SHARED), len(missing)),
        flush=True,
    )

    for x in UNIVERSAL_SHARED:
        print(
            "[CANONICAL_ALT_SHARED] present=%s pubkey=%s"
            % (x in before, x),
            flush=True,
        )

    if not missing:
        payload = {
            "status": "ALREADY_EXTENDED",
            "table": table,
            "before_count": len(before),
            "after_count": len(before),
            "missing_before": [],
            "target_shared": UNIVERSAL_SHARED,
            "broadcast": False,
        }
        _save(payload)
        print("[CANONICAL_ALT_UNIVERSAL_READY] already_present=True", flush=True)
        print("[STATE] %s" % AUDIT, flush=True)
        return 0

    kp = c.keypair()
    user = str(kp.pubkey())

    ix = _extend_ix(table, user, missing)
    msg, unsigned = c.compile_v0(
        user,
        [ix],
        [],
        _latest_blockhash(),
    )
    raw = c.signed_tx(msg, kp)

    sim = _simulate(raw, user)

    print(
        "[CANONICAL_ALT_EXTEND_SIM] err=%s units=%s bytes=%d"
        % (sim["err"], sim["units"], len(raw)),
        flush=True,
    )

    if sim["err"] is not None:
        for line in sim["logs"][-20:]:
            print("[CANONICAL_ALT_EXTEND_LOG] %s" % line, flush=True)
        raise RuntimeError("CANONICAL_ALT_EXTEND_SIM_FAILED")

    print("[CANONICAL_ALT_EXTEND_SIM_PASS]", flush=True)

    armed = (
        args.extend
        and os.getenv("ORACLE_CANONICAL_ALT_EXTEND", "").strip() == ARM_VALUE
    )

    if not armed:
        payload = {
            "status": "SIMULATION_PASS_NOT_BROADCAST",
            "table": table,
            "before_count": len(before),
            "missing_before": missing,
            "target_shared": UNIVERSAL_SHARED,
            "simulation_err": None,
            "simulation_units": sim["units"],
            "tx_bytes": len(raw),
            "broadcast": False,
        }
        _save(payload)
        print(
            "[BROADCAST] disabled -- arm ORACLE_CANONICAL_ALT_EXTEND=%s and rerun with --extend"
            % ARM_VALUE,
            flush=True,
        )
        print("[STATE] %s" % AUDIT, flush=True)
        return 0

    signature = c.send(raw)
    print("[CANONICAL_ALT_EXTEND_SENT] signature=%s" % signature, flush=True)

    confirmation = _confirm(signature)
    print(
        "[CANONICAL_ALT_EXTEND_CONFIRMED] status=%s" % confirmation,
        flush=True,
    )

    after = _read_alt(table)
    still_missing = [x for x in UNIVERSAL_SHARED if x not in after]

    if still_missing:
        raise RuntimeError(
            "CANONICAL_ALT_EXTENSION_VERIFY_FAILED:" + ",".join(still_missing)
        )

    payload = {
        "status": "UNIVERSAL_EXTENSION_CONFIRMED",
        "table": table,
        "before_count": len(before),
        "after_count": len(after),
        "added": missing,
        "target_shared": UNIVERSAL_SHARED,
        "signature": signature,
        "confirmation": confirmation,
        "broadcast": True,
        "verified_all_shared_present": True,
    }
    _save(payload)

    print(
        "[CANONICAL_ALT_UNIVERSAL_READY] before=%d after=%d added=%d"
        % (len(before), len(after), len(missing)),
        flush=True,
    )
    print("[STATE] %s" % AUDIT, flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

TEST_CODE = r"""import unittest
from pathlib import Path

TARGET = Path(
    "qseries_v2/oracle_execution/solana_atomic_executor/"
    "canonical_alt_universal_extension.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = TARGET.read_text(encoding="utf-8")

    def test_existing_table_only(self):
        self.assertIn(
            "HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r",
            self.s,
        )
        self.assertNotIn("CreateLookupTable", self.s)

    def test_exact_nine_shared(self):
        rows = (
            "8axdqvEoZ5YkV1yGw5Cmsx9pkeVve4cM9wAkZfhPcRDp",
            "Hvb4rCzCrUHxijoopBfN8q4SRmVeeKfPSEKKWGKMAfHZ",
            "5PHirr8joyTMp9JMm6nW7hNDVyEYdkzDqazxPD7RaTjx",
            "C2aFPdENg4A2HQsmrd5rTw5TaYBX5Ku887cWjbFKtZpw",
            "D1ZN9Wj1fRSUQfCjhvnu1hqDMT7hzjzBBpi12nVniYD6",
            "GS4CU59F31iL7aR2Q8zVS8DRrcRnXX1yjQ66TqNVQnaR",
            "pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ",
            "GAFuhgcd328SkkBYHpfadzmef9hTGAFRCi9QoCnsZQug",
            "9M4giFFMxmFGXtc3feFzRai56WbBqehoSeRE5GK7gf7",
        )
        for row in rows:
            self.assertIn(row, self.s)

    def test_guarded_broadcast(self):
        self.assertIn("ORACLE_CANONICAL_ALT_EXTEND", self.s)
        self.assertIn("EXTEND_CANONICAL_ALT_UNIVERSAL", self.s)
        self.assertIn("args.extend", self.s)

    def test_simulation_before_send(self):
        self.assertLess(
            self.s.index("[CANONICAL_ALT_EXTEND_SIM_PASS]"),
            self.s.index("signature = c.send(raw)"),
        )

    def test_onchain_verify(self):
        self.assertIn("verified_all_shared_present", self.s)
        self.assertIn("still_missing", self.s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
"""

PKG.mkdir(parents=True, exist_ok=True)
TARGET.write_text(MODULE, encoding="utf-8")
TEST.write_text(TEST_CODE, encoding="utf-8")

print("[PASS] canonical universal ALT extension installed")
print("[TABLE] existing HSEM canonical ALT only")
print("[ADDRESSES] exact 9 shared/static projection winners")
print("[SIMULATION] mandatory before broadcast")
print("[BROADCAST] guarded by explicit env arm + --extend")
print("[VERIFY] on-chain reread required after confirmation")
print("[TEST]", TEST.name)
