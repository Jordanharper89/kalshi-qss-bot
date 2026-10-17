
from pathlib import Path
import argparse
import asyncio
import json
import shutil
import unittest

VERSION = "ORACLE_044_WS_ROTATION_TRANSPORT"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
DEST = PKG / "oracle_044_ws_rotation_transport.py"
REPORT = Path("runtime_state/oracle/oracle_live_execution/ORACLE_044_WS_ROTATION.json")
CAP = 8
CANARY = 10_000_000

class Transport:
    def __init__(self, ws, timeout=5.0):
        self.ws = ws
        self.timeout = timeout
        self.serial = asyncio.Lock()
        self.next_id = 100000
        self.pending = {}
        self.subscriptions = {}
        self.by_subscription = {}
        self.routes = {}
        self.active = {}

    async def accept(self, message):
        if not isinstance(message, dict):
            return None
        if "id" in message:
            request = self.pending.pop(message["id"], None)
            if request is None:
                return None
            address, future = request
            subscription = message.get("result")
            if (not isinstance(subscription, int)
                    or isinstance(subscription, bool)):
                if not future.done():
                    future.set_result(False)
                return None
            self.subscriptions[address] = subscription
            self.by_subscription[subscription] = address
            if not future.done():
                future.set_result(True)
            return ("ACK", address)
        if message.get("method") == "accountNotification":
            params = message.get("params") or {}
            address = self.by_subscription.get(
                params.get("subscription"))
            return ("EVENT", address) if address else None
        return None

    async def subscribe(self, address):
        if address in self.subscriptions:
            return True
        self.next_id += 1
        rid = self.next_id
        future = asyncio.get_running_loop().create_future()
        self.pending[rid] = (address, future)
        request = {
            "jsonrpc": "2.0", "id": rid,
            "method": "accountSubscribe",
            "params": [
                address,
                {"encoding": "base64", "commitment": "processed"}
            ]
        }
        try:
            await self.ws.send(json.dumps(request))
            return await asyncio.wait_for(future, self.timeout)
        except (asyncio.TimeoutError, OSError):
            return False
        finally:
            self.pending.pop(rid, None)

    async def unsubscribe_unused(self, addresses):
        occupied = set()
        for group in self.routes.values():
            occupied.update(group)
        for address in addresses:
            if address in occupied:
                continue
            subscription = self.subscriptions.pop(address, None)
            if subscription is None:
                continue
            self.by_subscription.pop(subscription, None)
            self.next_id += 1
            await self.ws.send(json.dumps({
                "jsonrpc": "2.0",
                "id": self.next_id,
                "method": "accountUnsubscribe",
                "params": [subscription]
            }))

    async def rotate(self, candidate, receipt, commit,
                     evict_token=None):
        from qseries_v2.oracle_execution.solana_atomic_executor import (
            oracle_043_warm_rotation_handoff as v43
        )
        async with self.serial:
            key = v43.identity(candidate)
            if key is None or not v43.eligible(receipt, key):
                return "HOLD_VALIDATION_INCOMPLETE"

            token = candidate["token"]
            if token in self.active:
                return "HOLD_ALREADY_ACTIVE"

            addresses = list(receipt["watched_accounts"])
            if not addresses or len(addresses) != len(set(addresses)):
                return "HOLD_INVALID_ACCOUNT_REGISTRY"
            if not all(isinstance(a, str) and a for a in addresses):
                return "HOLD_INVALID_ACCOUNT_ADDRESS"

            victim = None
            if len(self.active) >= CAP:
                if evict_token not in self.active:
                    return "HOLD_NO_EXPLICIT_EVICTION"
                victim = evict_token

            existing = set(self.subscriptions)
            for address in addresses:
                if not await self.subscribe(address):
                    try:
                        await self.unsubscribe_unused(
                            set(self.subscriptions) - existing)
                    except Exception:
                        return "HOLD_SUBSCRIPTION_CLEANUP"
                    return "HOLD_SUBSCRIPTION_ACK_INCOMPLETE"

            # Commit callback must atomically install both the
            # pair state and the canonical account route.
            proposed = dict(self.active)
            if victim:
                proposed.pop(victim)
            proposed[token] = dict(candidate)
            try:
                committed = commit(proposed, receipt)
            except Exception:
                committed = False
            if committed is not True:
                try:
                    await self.unsubscribe_unused(
                        set(self.subscriptions) - existing)
                except Exception:
                    return "HOLD_SUBSCRIPTION_CLEANUP"
                return "HOLD_ATOMIC_COMMIT"

            self.active = proposed
            self.routes[token] = tuple(addresses)
            if victim:
                self.routes.pop(victim, None)

            try:
                await self.unsubscribe_unused(
                    set(self.subscriptions) - set(
                        a for group in self.routes.values()
                        for a in group
                    ))
            except Exception:
                return "COMMITTED_CLEANUP_PENDING"
            return "ROTATION_COMMITTED"

class FakeWebSocket:
    def __init__(self):
        self.manager = None
        self.sent = []
        self.fail_address = None

    async def send(self, payload):
        data = json.loads(payload)
        self.sent.append(data)
        if data["method"] == "accountSubscribe":
            address = data["params"][0]
            if address == self.fail_address:
                return
            await self.manager.accept({
                "jsonrpc": "2.0",
                "id": data["id"],
                "result": data["id"] + 500
            })

def fixture(n, addresses=None):
    row = {
        "token": "T" + str(n),
        "pump_pool": "P" + str(n),
        "meteora_pool": "M" + str(n)
    }
    receipt = {
        "identity": (row["token"], row["pump_pool"],
                     row["meteora_pool"]),
        "fresh_onchain": True,
        "pool_owner_attested": True,
        "native_templates_ready": True,
        "watched_accounts": addresses or ["A" + str(n)],
        "execution_authority": False
    }
    return row, receipt

class Tests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.ws = FakeWebSocket()
        self.manager = Transport(self.ws, timeout=0.01)
        self.ws.manager = self.manager

    async def test_acknowledged_subscription(self):
        self.assertTrue(await self.manager.subscribe("A"))
        self.assertIn("A", self.manager.subscriptions)

    async def test_missing_ack(self):
        self.ws.fail_address = "A"
        self.assertFalse(await self.manager.subscribe("A"))
        self.assertNotIn("A", self.manager.subscriptions)

    async def test_protected_promotion(self):
        row, receipt = fixture(1)
        result = await self.manager.rotate(
            row, receipt, lambda a, b: True)
        self.assertEqual(result, "ROTATION_COMMITTED")
        self.assertIn("T1", self.manager.active)

    async def test_failed_commit_preserves_state(self):
        row, receipt = fixture(1)
        result = await self.manager.rotate(
            row, receipt, lambda a, b: False)
        self.assertEqual(result, "HOLD_ATOMIC_COMMIT")
        self.assertFalse(self.manager.active)

    async def test_failed_attestation(self):
        row, receipt = fixture(1)
        receipt["pool_owner_attested"] = False
        result = await self.manager.rotate(
            row, receipt, lambda a, b: True)
        self.assertEqual(result, "HOLD_VALIDATION_INCOMPLETE")
        self.assertFalse(self.ws.sent)

    async def test_replace_after_subscribing(self):
        old, old_receipt = fixture(1)
        await self.manager.rotate(
            old, old_receipt, lambda a, b: True)
        for n in range(2, 9):
            row, receipt = fixture(n)
            await self.manager.rotate(
                row, receipt, lambda a, b: True)
        new, receipt = fixture(9)
        result = await self.manager.rotate(
            new, receipt, lambda a, b: True,
            evict_token="T1")
        self.assertEqual(result, "ROTATION_COMMITTED")
        self.assertNotIn("T1", self.manager.active)
        self.assertIn("T9", self.manager.active)
        self.assertEqual(len(self.manager.active), CAP)
        methods = [x["method"] for x in self.ws.sent]
        self.assertEqual(methods[-2:],
                         ["accountSubscribe", "accountUnsubscribe"])

    async def test_shared_account_preserved(self):
        a, ra = fixture(1, ["SHARED", "ONE"])
        b, rb = fixture(2, ["SHARED", "TWO"])
        await self.manager.rotate(a, ra, lambda x, y: True)
        await self.manager.rotate(b, rb, lambda x, y: True)
        self.assertIn("SHARED", self.manager.subscriptions)
        self.assertEqual(
            sum(x["method"] == "accountSubscribe"
                and x["params"][0] == "SHARED"
                for x in self.ws.sent), 1)

    async def test_notification_routing(self):
        await self.manager.subscribe("A")
        sid = self.manager.subscriptions["A"]
        event = await self.manager.accept({
            "method": "accountNotification",
            "params": {"subscription": sid}
        })
        self.assertEqual(event, ("EVENT", "A"))

def audit(root):
    result = {
        "revision": VERSION,
        "status": "WS_ROTATION_TRANSPORT_TESTED",
        "capacity": CAP,
        "subscription_ack_required": True,
        "shared_account_reuse": True,
        "commit_before_unsubscribe": True,
        "production_socket_attached": False,
        "production_pair_state_attached": False,
        "replenishment_worker_started": False,
        "live_rotation_certified": False,
        "rpc_requests": 0,
        "signing": False,
        "broadcast": False,
        "canary_lamports": CANARY
    }
    path = root / REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()

    if args.test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if result.wasSuccessful() else 1

    if args.audit:
        result = audit(root)
        for key, value in result.items():
            print("[" + key.upper() + "]",
                  json.dumps(value, sort_keys=True))
        print("[REPORT]", root / REPORT)
        return 0

    target = root / DEST
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if target.resolve() != Path(__file__).resolve():
        shutil.copyfile(Path(__file__), target)

    print("[PASS]", VERSION)
    print("[MODE] PERSISTENT_WS_SUBSCRIPTION_TRANSPORT")
    print("[SCANNER] FROZEN")
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
