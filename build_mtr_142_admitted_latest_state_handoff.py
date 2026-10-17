from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2/oracle_execution/solana_atomic_executor"
DEST = PKG / "mtr_142_admitted_latest_state_handoff.py"
TEST = ROOT / "test_mtr_142_admitted_latest_state_handoff.py"
MODULE = r'''
"""MTR-142 staged admission-to-canonical-submit handoff.

This module never subscribes, hydrates, signs or broadcasts.
The canonical producer must supply snapshots and a strict extraction function.
"""
from threading import RLock
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_139_ws_warm_admission_gate import SIZES

class AdmittedLatestHandoff:
    def __init__(self, admission, lane, describe_snapshot):
        if not callable(getattr(admission, "current", None)):
            raise TypeError("AdmissionGate.current required")
        if not callable(getattr(lane, "submit", None)):
            raise TypeError("LatestStateLane.submit required")
        if not callable(describe_snapshot):
            raise TypeError("trusted snapshot descriptor required")
        self.admission, self.lane = admission, lane
        self.describe = describe_snapshot
        self._lock = RLock()
        self._latest = {}
        self.submitted = 0
        self.rejected = 0

    def offer(self, route_id, snapshot, slot, received_ns):
        """Offer a snapshot already emitted by the canonical WS producer.

        describe_snapshot(snapshot) must return a dict containing:
          token, pump_pool, dlmm_pool, account_slots (dict), sizes.
        Caller is responsible for correct trusted WS provenance.
        No REST fallback and no construction of synthetic price state.
        """
        with self._lock:
            proof = self.admission.current(route_id)
            if proof is None:
                self.rejected += 1
                return False
            if type(slot) is not int or slot < 0:
                raise ValueError("invalid canonical slot")
            if type(received_ns) is not int or received_ns <= 0:
                raise ValueError("invalid canonical monotonic timestamp")
            info = self.describe(snapshot)
            if not isinstance(info, dict):
                raise ValueError("snapshot descriptor must be a dict")
            if (info.get("token"), info.get("pump_pool"), info.get("dlmm_pool")) != (
                proof.token, proof.pump_pool, proof.dlmm_pool
            ):
                raise ValueError("exact binding mismatch")
            accounts = info.get("account_slots")
            if not isinstance(accounts, dict):
                raise ValueError("account slot vector required")
            if accounts != dict(proof.snapshot_slots):
                self.rejected += 1
                return False
            if tuple(info.get("sizes", ())) != tuple(SIZES):
                raise ValueError("canonical five-size policy required")
            if slot < max(accounts.values()):
                self.rejected += 1
                return False
            # Never carry an older generation/epoch across rediscovery.
            prev = self._latest.get(route_id)
            if prev is not None and (proof.epoch < prev[0] or
                    (proof.epoch == prev[0] and
                     proof.state_generation <= prev[1])):
                self.rejected += 1
                return False
            # This is an in-process boundary. No private key, RPC or signer.
            # Keep admission check next to handoff; canonical lane handles
            # newer-state-wins and mid-scan invalidation.
            if self.admission.current(route_id) != proof:
                self.rejected += 1
                return False
            self.lane.submit(proof.token, snapshot, slot, received_ns)
            self._latest[route_id] = (proof.epoch, proof.state_generation)
            self.submitted += 1
            return True

if __name__ == "__main__":
    print("[MTR142] STAGED_HANDOFF_IMPORT_PASS")
    print("[CANONICAL_SCANNER] UNMODIFIED")
    print("[PRODUCTION_CUTOVER] FALSE")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
'''
TEST_SOURCE = r'''
import unittest
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_139_ws_warm_admission_gate import AdmissionGate, SIZES
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_142_admitted_latest_state_handoff import AdmittedLatestHandoff

class Lane:
    def __init__(self):
        self.calls = []
    def submit(self, *args):
        self.calls.append(args)

class Tests(unittest.TestCase):
    def setUp(self):
        self.now = 1_000_000_000
        self.g = AdmissionGate(100, clock=lambda: self.now)
        self.l = Lane()
        self.h = AdmittedLatestHandoff(self.g, self.l, lambda s: s)
        self.epoch = self.g.discover("r", "token", "pump", "dlmm", ("p", "d"))
        self.snap = {"token": "token", "pump_pool": "pump", "dlmm_pool": "dlmm",
                     "account_slots": {"p": 10, "d": 10}, "sizes": SIZES}
    def ready(self):
        self.g.mark_exact("r", self.epoch)
        self.g.mark_warm("r", self.epoch)
        self.g.mark_subscribed("r", self.epoch)
        self.g.observe_ws("r", self.epoch, "p", 10)
        self.g.observe_ws("r", self.epoch, "d", 10)
        self.g.publish("r", self.epoch)
    def test_missing_proof_does_not_forward(self):
        self.assertFalse(self.h.offer("r", self.snap, 10, self.now))
        self.assertEqual(self.l.calls, [])
    def test_exact_admitted_handoff_only_once(self):
        self.ready()
        self.assertTrue(self.h.offer("r", self.snap, 10, self.now))
        self.assertFalse(self.h.offer("r", self.snap, 10, self.now))
        self.assertEqual(self.l.calls, [("token", self.snap, 10, self.now)])
    def test_wrong_binding_and_size_fail_closed(self):
        self.ready()
        for field, bad in (("token", "other"), ("dlmm_pool", "wrong"), ("sizes", (0.001,))):
            with self.subTest(field=field):
                item = dict(self.snap, **{field: bad})
                with self.assertRaises(ValueError):
                    self.h.offer("r", item, 10, self.now)
        self.assertEqual(self.l.calls, [])
    def test_stale_or_changed_ws_vector_rejected(self):
        self.ready()
        item = dict(self.snap, account_slots={"p": 11, "d": 10})
        self.assertFalse(self.h.offer("r", item, 11, self.now))
        self.now += 101_000_000
        self.assertFalse(self.h.offer("r", self.snap, 10, self.now))
        self.assertEqual(self.l.calls, [])
    def test_new_state_needs_readmission(self):
        self.ready()
        self.assertTrue(self.h.offer("r", self.snap, 10, self.now))
        self.g.observe_ws("r", self.epoch, "p", 11)
        new_snap = dict(self.snap, account_slots={"p": 11, "d": 10})
        self.assertFalse(self.h.offer("r", new_snap, 11, self.now))
        self.g.publish("r", self.epoch)
        self.assertTrue(self.h.offer("r", new_snap, 11, self.now))
        self.assertEqual(len(self.l.calls), 2)
    def test_revoke_prevents_handoff(self):
        self.ready()
        self.g.revoke("r")
        self.assertFalse(self.h.offer("r", self.snap, 10, self.now))
        self.assertEqual(self.l.calls, [])

if __name__ == "__main__":
    unittest.main(verbosity=2)
'''
for name in ("mtr_139_ws_warm_admission_gate.py",):
    if not (PKG / name).is_file():
        raise SystemExit("[HOLD] Missing certified dependency " + name)
for code in (MODULE, TEST_SOURCE):
    ast.parse(code)
DEST.write_text(MODULE, encoding="utf-8")
TEST.write_text(TEST_SOURCE, encoding="utf-8")
print("[PASS] installed", DEST.relative_to(ROOT))
print("[PASS] installed", TEST.name)
print("[SCOPE] ADMISSION_TO_CANONICAL_SUBMIT_STAGING; not wired to production")
print("[SCANNER] FROZEN")
print("[PRIVATE_KEY] NOT_USED")
print("[SIGNING] FALSE")
print("[BROADCAST] FALSE")
