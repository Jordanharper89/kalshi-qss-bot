"""MTR-139: fail-closed, reusable HOT admission gate. No network or trading I/O."""
from dataclasses import dataclass
from types import MappingProxyType
from threading import RLock
import time

SIZES = (0.010, 0.015, 0.020, 0.025, 0.030)

@dataclass(frozen=True)
class HotRoute:
    route_id: str
    token: str
    pump_pool: str
    dlmm_pool: str
    epoch: int
    accounts: tuple
    snapshot_slots: tuple
    state_generation: int
    admitted_ns: int
    sizes: tuple = SIZES

class AdmissionGate:
    """Control-plane admission only; scanner retains exclusive pricing authority."""
    def __init__(self, freshness_ms=2500, clock=time.monotonic_ns):
        if freshness_ms <= 0:
            raise ValueError('freshness_ms must be positive')
        self._clock = clock
        self._ttl_ns = int(freshness_ms * 1_000_000)
        self._lock = RLock()
        self._entries = {}
        self._generation = 0

    @staticmethod
    def _identity(token, pump_pool, dlmm_pool, accounts):
        vals = (token, pump_pool, dlmm_pool)
        if not all(isinstance(x, str) and x.strip() for x in vals):
            raise ValueError('all three exact binding identifiers required')
        acc = tuple(accounts)
        if not acc or len(set(acc)) != len(acc) or not all(isinstance(x, str) and x.strip() for x in acc):
            raise ValueError('unique nonempty required websocket accounts')
        if pump_pool == dlmm_pool:
            raise ValueError('pump and dlmm pools must differ')
        return acc

    def discover(self, route_id, token, pump_pool, dlmm_pool, accounts):
        """Re-discovery invalidates prior epoch and all prior WS proofs."""
        if not isinstance(route_id, str) or not route_id.strip():
            raise ValueError('route id required')
        acc = self._identity(token, pump_pool, dlmm_pool, accounts)
        with self._lock:
            epoch = self._entries.get(route_id, {}).get('epoch', 0) + 1
            self._entries[route_id] = dict(epoch=epoch, token=token,
                pump_pool=pump_pool, dlmm_pool=dlmm_pool, accounts=acc,
                exact=False, warm=False, subscribed=False,
                proofs={}, admitted=None)
            return epoch

    def mark_exact(self, route_id, epoch):
        with self._lock:
            e = self._entry(route_id, epoch)
            e['exact'] = True

    def mark_warm(self, route_id, epoch):
        """Caller certifies hydration completed outside the HOT critical path."""
        with self._lock:
            e = self._entry(route_id, epoch)
            if not e['exact']:
                raise ValueError('exact binding must be certified first')
            e['warm'] = True

    def mark_subscribed(self, route_id, epoch):
        """Caller certifies WS subscription of every required account."""
        with self._lock:
            e = self._entry(route_id, epoch)
            if not e['warm']:
                raise ValueError('off-path warm hydration is required')
            e['subscribed'] = True

    def observe_ws(self, route_id, epoch, account, slot, observed_ns=None):
        """Take transport-delivered evidence, never REST state or timestamps."""
        with self._lock:
            e = self._entry(route_id, epoch)
            if not e['subscribed'] or account not in e['accounts']:
                raise ValueError('account is not an active subscribed account')
            if isinstance(slot, bool) or not isinstance(slot, int) or slot < 0:
                raise ValueError('invalid Solana slot')
            now = self._clock()
            if observed_ns is not None and observed_ns != now:
                raise ValueError('caller timestamps forbidden; prevent fabricated freshness')
            old = e['proofs'].get(account)
            if old and slot < old[0]:
                return False
            e['proofs'][account] = (slot, now)
            e['admitted'] = None  # every new update invalidates previous immutable snapshot
            return True

    def _entry(self, route_id, epoch):
        e = self._entries.get(route_id)
        if e is None or e['epoch'] != epoch:
            raise ValueError('unknown or superseded route epoch')
        return e

    def publish(self, route_id, epoch):
        """Publish immutable route/slot vector only when ALL WS proofs are fresh."""
        with self._lock:
            e = self._entry(route_id, epoch)
            if not (e['exact'] and e['warm'] and e['subscribed']):
                raise ValueError('route lifecycle incomplete')
            now = self._clock()
            if set(e['proofs']) != set(e['accounts']):
                raise ValueError('missing required live WS account evidence')
            if any(now - tick > self._ttl_ns or now < tick for _, tick in e['proofs'].values()):
                raise ValueError('stale or future WS state')
            self._generation += 1
            proof = HotRoute(route_id, e['token'], e['pump_pool'], e['dlmm_pool'],
                epoch, e['accounts'], tuple((a, e['proofs'][a][0]) for a in e['accounts']),
                self._generation, now)
            e['admitted'] = proof
            return proof

    def current(self, route_id):
        """Fail-closed on stale proofs without touching scanner/network."""
        with self._lock:
            e = self._entries.get(route_id)
            if not e or not e['admitted']:
                return None
            p = e['admitted']
            now = self._clock()
            if any(now < tick or now - tick > self._ttl_ns for _, tick in e['proofs'].values()):
                e['admitted'] = None
                return None
            return p

    def hot_inventory(self):
        """Atomic copy for a future canonical-scanner handoff (no live cutover here)."""
        with self._lock:
            return MappingProxyType({k: p for k in tuple(self._entries)
                if (p := self.current(k)) is not None})

    def revoke(self, route_id):
        with self._lock:
            e = self._entries.get(route_id)
            if e:
                e['admitted'] = None
                e['subscribed'] = False
                e['proofs'].clear()

if __name__ == '__main__':
    print('[MTR139] REUSABLE_ADMISSION_GATE_IMPORT_PASS')
    print('[CANONICAL_SCANNER] UNMODIFIED_NOT_CONNECTED')
    print('[HOT_REST] NONE')
    print('[PRIVATE_KEY] NOT_USED')
    print('[SIGNING] FALSE')
    print('[BROADCAST] FALSE')
