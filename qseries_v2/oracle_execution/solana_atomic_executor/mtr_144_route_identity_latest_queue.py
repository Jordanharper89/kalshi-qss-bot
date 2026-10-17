"""MTR-144: route-keyed latest-state queue, isolated from production.

Does not invoke ORACLE-020 (token-keyed) until per-route pricing is supported.
Inputs are already-warm canonical snapshots from a trusted WS producer.
"""
from dataclasses import dataclass
from threading import RLock
from types import MappingProxyType

SIZES = (0.010, 0.015, 0.020, 0.025, 0.030)

@dataclass(frozen=True)
class RouteKey:
    token: str
    pump_pool: str
    dlmm_pool: str

@dataclass(frozen=True)
class Queued:
    route: RouteKey
    epoch: int
    generation: int
    slot: int
    received_ns: int
    snapshot: object

class RouteLatestQueue:
    def __init__(self, gate, descriptor):
        if not callable(getattr(gate, 'current', None)):
            raise TypeError('admission gate required')
        if not callable(descriptor):
            raise TypeError('trusted WS snapshot descriptor required')
        self.gate = gate
        self.describe = descriptor
        self.lock = RLock()
        self.latest = {}
        self.stats = {'accepted': 0, 'rejected': 0, 'replaced': 0,
                      'token_collisions': 0, 'forwarded': 0}

    def offer(self, route_id, snapshot, slot, received_ns):
        # Immutable published admission proof must be current at handoff.
        with self.lock:
            proof = self.gate.current(route_id)
            if proof is None:
                self.stats['rejected'] += 1
                return False
            if type(slot) is not int or slot < 0 or type(received_ns) is not int or received_ns <= 0:
                raise ValueError('invalid slot/time')
            x = self.describe(snapshot)
            if not isinstance(x, dict):
                raise ValueError('snapshot descriptor required')
            key = RouteKey(proof.token, proof.pump_pool, proof.dlmm_pool)
            if (x.get('token'), x.get('pump_pool'), x.get('dlmm_pool')) != (
                    key.token, key.pump_pool, key.dlmm_pool):
                raise ValueError('route identity mismatch')
            if tuple(x.get('sizes', ())) != SIZES:
                raise ValueError('size policy mismatch')
            account_slots = x.get('account_slots')
            if not isinstance(account_slots, dict) or account_slots != dict(proof.snapshot_slots):
                self.stats['rejected'] += 1
                return False
            if not account_slots or slot < max(account_slots.values()):
                self.stats['rejected'] += 1
                return False
            current = self.latest.get(key)
            new = (proof.epoch, proof.state_generation)
            if current and new <= (current.epoch, current.generation):
                self.stats['rejected'] += 1
                return False
            if self.gate.current(route_id) != proof:
                self.stats['rejected'] += 1
                return False
            if current:
                self.stats['replaced'] += 1
            self.latest[key] = Queued(key, *new, slot, received_ns, snapshot)
            self.stats['accepted'] += 1
            return True

    def inventory(self):
        with self.lock:
            return MappingProxyType(dict(self.latest))

    def take_if_current(self, route):
        with self.lock:
            return self.latest.get(route)

    def forward_to_legacy_token_lane(self, *args, **kwargs):
        # This would silently overwrite alternate DLMM routes with same token.
        raise RuntimeError('HOLD_ROUTE_KEY_REQUIRED_IN_PRICING_WORKER')

    def collision_tokens(self):
        with self.lock:
            pools = {}
            for k in self.latest:
                pools.setdefault(k.token, set()).add((k.pump_pool, k.dlmm_pool))
            return tuple(sorted(t for t, ps in pools.items() if len(ps) > 1))

def main():
    print('[MTR144] ROUTE_KEYED_QUEUE_IMPORT_PASS')
    print('[LEGACY_TOKEN_LANE] FORWARDING_BLOCKED')
    print('[CANONICAL_SCANNER] FROZEN')
    print('[PRODUCTION_CUTOVER] FALSE')
    print('[HOT_REST] NONE')
    print('[PRIVATE_KEY] NOT_USED')
    print('[SIGNING] FALSE')
    print('[BROADCAST] FALSE')

if __name__ == '__main__':
    main()
