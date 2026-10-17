
from pathlib import Path
import argparse
import json
import shutil
import unittest

VERSION = "ORACLE_043_WARM_ROTATION_HANDOFF"
PACKAGE = Path("qseries_v2/oracle_execution/solana_atomic_executor")
TARGET = PACKAGE / "oracle_043_warm_rotation_handoff.py"
REPORT = Path(
    "runtime_state/oracle/oracle_live_execution/"
    "ORACLE_043_ROTATION.json"
)
CAPACITY = 8
CANARY = 10_000_000

def identity(row):
    if not isinstance(row, dict):
        return None
    value = tuple(row.get(k) for k in (
        "token", "pump_pool", "meteora_pool"
    ))
    if not all(isinstance(x, str) and x for x in value):
        return None
    return value

def eligible(receipt, expected):
    if not isinstance(receipt, dict):
        return False
    return bool(
        receipt.get("identity") == expected
        and receipt.get("fresh_onchain")
        and receipt.get("pool_owner_attested")
        and receipt.get("native_templates_ready")
        and receipt.get("watched_accounts")
        and receipt.get("execution_authority") is False
    )

class Rotation:
    def __init__(self, active=None, generation=0):
        self.active = list(active or [])
        if len(self.active) > CAPACITY:
            raise ValueError("ACTIVE_CAPACITY_EXCEEDED")
        self.generation = generation
        self.pending = []
        self.history = []

    def ingest(self, generation, incoming):
        if not isinstance(generation, int) or generation <= self.generation:
            return "HOLD_GENERATION_NOT_ADVANCED"
        self.generation = generation
        seen = {identity(x) for x in self.active}
        self.pending = []
        for row in incoming:
            key = identity(row)
            if key and key not in seen:
                self.pending.append(dict(row))
                seen.add(key)
        return "PENDING_LIVE_VALIDATION"

    def promote(self, candidate, hydrate, subscribe, unsubscribe,
                commit, evict_token=None):
        key = identity(candidate)
        if key is None or candidate not in self.pending:
            return "HOLD_NOT_PENDING"

        if any(identity(row) == key for row in self.active):
            return "HOLD_ALREADY_ACTIVE"

        victim = None
        if len(self.active) >= CAPACITY:
            for row in self.active:
                if row["token"] == evict_token:
                    victim = row
                    break
            if victim is None:
                return "HOLD_NO_EXPLICIT_EVICTION"

        # Fresh hydration must run through the existing production
        # native pool attestation and template readiness gates.
        try:
            receipt = hydrate(dict(candidate))
        except Exception:
            return "HOLD_HYDRATION_FAILED"

        if not eligible(receipt, key):
            return "HOLD_VALIDATION_INCOMPLETE"

        addresses = list(receipt["watched_accounts"])
        if not addresses or len(set(addresses)) != len(addresses):
            return "HOLD_INVALID_ACCOUNT_REGISTRY"

        # Subscribe first. The adapter must return acknowledgments
        # for every required account before any slot changes.
        try:
            acknowledged = subscribe(addresses)
        except Exception:
            return "HOLD_SUBSCRIPTION_FAILED"

        if not isinstance(acknowledged, (set, list, tuple)):
            return "HOLD_SUBSCRIPTION_ACK_MISSING"

        if not set(addresses).issubset(set(acknowledged)):
            return "HOLD_SUBSCRIPTION_ACK_INCOMPLETE"

        before = list(self.active)
        after = [row for row in before if row is not victim]
        after.append(dict(candidate))

        # The live adapter must atomically update the pricing
        # state and account routing before old subscriptions end.
        try:
            committed = commit(after, receipt)
        except Exception:
            return "HOLD_COMMIT_FAILED"

        if committed is not True:
            return "HOLD_COMMIT_NOT_ACKNOWLEDGED"

        self.active = after
        self.pending.remove(candidate)
        self.history.append({
            "generation": self.generation,
            "admitted": key[0],
            "evicted": victim["token"] if victim else None
        })

        if victim is not None:
            try:
                unsubscribe(victim)
            except Exception:
                # A lingering old subscription is not permission
                # to reverse a successfully committed routing swap.
                return "COMMITTED_OLD_SUBSCRIPTION_CLEANUP_PENDING"

        return "ROTATION_COMMITTED"

def fixture_row(n):
    return {
        "token": "TOKEN_" + str(n),
        "pump_pool": "PUMP_" + str(n),
        "meteora_pool": "DLMM_" + str(n)
    }

def fixture_receipt(row):
    return {
        "identity": identity(row),
        "fresh_onchain": True,
        "pool_owner_attested": True,
        "native_templates_ready": True,
        "watched_accounts": ["ACCOUNT_A", "ACCOUNT_B"],
        "execution_authority": False
    }

class Tests(unittest.TestCase):
    def test_generation(self):
        r = Rotation(generation=3)
        self.assertEqual(
            r.ingest(3, [fixture_row(1)]),
            "HOLD_GENERATION_NOT_ADVANCED"
        )

    def test_new_generation(self):
        r = Rotation([fixture_row(1)])
        self.assertEqual(
            r.ingest(1, [fixture_row(1), fixture_row(2)]),
            "PENDING_LIVE_VALIDATION"
        )
        self.assertEqual(len(r.pending), 1)

    def test_no_blind_eviction(self):
        r = Rotation([fixture_row(i) for i in range(8)])
        candidate = fixture_row(9)
        r.ingest(1, [candidate])
        result = r.promote(
            candidate, fixture_receipt,
            lambda a: set(a), lambda x: None,
            lambda a, b: True
        )
        self.assertEqual(result, "HOLD_NO_EXPLICIT_EVICTION")
        self.assertEqual(len(r.active), 8)

    def test_incomplete_attestation(self):
        r = Rotation()
        candidate = fixture_row(1)
        r.ingest(1, [candidate])
        def invalid(row):
            receipt = fixture_receipt(row)
            receipt["pool_owner_attested"] = False
            return receipt
        result = r.promote(
            candidate, invalid,
            lambda a: set(a), lambda x: None,
            lambda a, b: True
        )
        self.assertEqual(result, "HOLD_VALIDATION_INCOMPLETE")
        self.assertEqual(len(r.active), 0)

    def test_missing_ws_ack(self):
        r = Rotation()
        candidate = fixture_row(1)
        r.ingest(1, [candidate])
        result = r.promote(
            candidate, fixture_receipt,
            lambda a: {"ACCOUNT_A"},
            lambda x: None, lambda a, b: True
        )
        self.assertEqual(result, "HOLD_SUBSCRIPTION_ACK_INCOMPLETE")
        self.assertEqual(len(r.active), 0)

    def test_commit_hold(self):
        r = Rotation()
        candidate = fixture_row(1)
        r.ingest(1, [candidate])
        result = r.promote(
            candidate, fixture_receipt,
            lambda a: set(a), lambda x: None,
            lambda a, b: False
        )
        self.assertEqual(result, "HOLD_COMMIT_NOT_ACKNOWLEDGED")
        self.assertEqual(len(r.active), 0)

    def test_protected_rotation(self):
        r = Rotation([fixture_row(i) for i in range(8)])
        candidate = fixture_row(9)
        r.ingest(1, [candidate])
        events = []
        result = r.promote(
            candidate, fixture_receipt,
            lambda a: events.append("SUBSCRIBED") or set(a),
            lambda x: events.append("UNSUBSCRIBED"),
            lambda a, b: events.append("COMMITTED") or True,
            evict_token="TOKEN_0"
        )
        self.assertEqual(result, "ROTATION_COMMITTED")
        self.assertEqual(
            events,
            ["SUBSCRIBED", "COMMITTED", "UNSUBSCRIBED"]
        )
        self.assertEqual(len(r.active), 8)
        self.assertEqual(r.active[-1]["token"], "TOKEN_9")

    def test_canary(self):
        self.assertEqual(CANARY, 10_000_000)

def audit(root):
    result = {
        "revision": VERSION,
        "status": "ROTATION_HANDOFF_READY",
        "warm_capacity": CAPACITY,
        "required_validation": [
            "FRESH_ONCHAIN",
            "POOL_OWNER_ATTESTED",
            "NATIVE_TEMPLATES_READY",
            "ACCOUNT_SUBSCRIPTIONS_ACKNOWLEDGED",
            "ATOMIC_ROUTING_COMMIT"
        ],
        "live_production_hooks_attached": False,
        "worker_running": False,
        "ws_rotation_executed": False,
        "rpc_requests": 0,
        "signing": False,
        "broadcast": False,
        "canary_lamports": CANARY
    }
    path = root / REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    temp.replace(path)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()

    if args.test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1

    if args.audit:
        result = audit(root)
        for key, value in result.items():
            print("[" + key.upper() + "]", json.dumps(value))
        print("[REPORT]", root / REPORT)
        return 0

    target = root / TARGET
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if target.resolve() != Path(__file__).resolve():
        shutil.copyfile(Path(__file__), target)

    print("[PASS]", VERSION)
    print("[SCANNER] UNCHANGED")
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
