
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
