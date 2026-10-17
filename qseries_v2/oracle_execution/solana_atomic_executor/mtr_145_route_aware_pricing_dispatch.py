"""MTR-145 route-keyed, read-only latest-state pricing dispatcher.

Pricer is injected: no SDK guesses, REST calls, signing or broadcast.
Price results are observations, NEVER execution authorizations.
"""
from dataclasses import dataclass
from threading import RLock
from math import isfinite
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_144_route_identity_latest_queue import SIZES

DIRECTIONS = ("PUMP_TO_METEORA", "METEORA_TO_PUMP")

@dataclass(frozen=True)
class PriceObservation:
    route: object
    epoch: int
    generation: int
    direction: str
    size: float
    net_raw: int
    bps: float

class RouteAwarePricer:
    def __init__(self, queue, exact_pricer, max_age_ns=2_500_000_000):
        if not callable(exact_pricer):
            raise TypeError("exact snapshot pricer required")
        if not isinstance(max_age_ns, int) or max_age_ns <= 0:
            raise ValueError("positive freshness bound required")
        self.queue = queue
        self.exact_pricer = exact_pricer
        self.max_age_ns = max_age_ns
        self.lock = RLock()
        self.stats = dict(evaluations=0, aborted=0, completed=0, positive=0)

    def sweep(self, route, now_ns):
        """Only evaluate admitted latest snapshots; abort on replacement.

        exact_pricer(snapshot, direction, size) -> (net_raw, bps)
        Caller must inject previously verified official pricing, never
        a fixed-constant-product approximation or unprotected economics.
        """
        if type(now_ns) is not int or now_ns <= 0:
            raise ValueError("monotonic now_ns required")
        with self.lock:
            entry = self.queue.take_if_current(route)
            if entry is None or now_ns < entry.received_ns or now_ns - entry.received_ns > self.max_age_ns:
                self.stats["aborted"] += 1
                return ()
            version = (entry.epoch, entry.generation)
            observations = []
            for direction in DIRECTIONS:
                for size in SIZES:
                    current = self.queue.take_if_current(route)
                    if current is None or (current.epoch, current.generation) != version:
                        self.stats["aborted"] += 1
                        return ()
                    # Admission freshness must remain valid throughout the sweep.
                    if now_ns - current.received_ns > self.max_age_ns:
                        self.stats["aborted"] += 1
                        return ()
                    # A pricing callback may itself cause a new WS generation.
                    result = self.exact_pricer(entry.snapshot, direction, size)
                    newer = self.queue.take_if_current(route)
                    if newer is None or (newer.epoch, newer.generation) != version:
                        self.stats["aborted"] += 1
                        return ()
                    if not (isinstance(result, tuple) and len(result) == 2):
                        raise ValueError("exact pricing must return (net_raw, bps)")
                    net_raw, bps = result
                    if type(net_raw) is not int or isinstance(bps, bool) or not isinstance(bps, (int, float)) or not isfinite(bps):
                        raise ValueError("invalid exact economics")
                    observations.append(PriceObservation(route, *version, direction, size, net_raw, float(bps)))
                    self.stats["evaluations"] += 1
            self.stats["completed"] += 1
            self.stats["positive"] += sum(x.net_raw > 0 and x.bps > 0 for x in observations)
            return tuple(observations)

    @staticmethod
    def candidates(observations):
        return tuple(sorted((x for x in observations if x.net_raw > 0 and x.bps > 0),
                            key=lambda x: (x.net_raw, x.bps), reverse=True))

def main():
    print("[MTR145] ROUTE_AWARE_EXACT_PRICING_DISPATCH_IMPORT_PASS")
    print("[PRICER] REQUIRES_VERIFIED_OFFICIAL_CALLBACK")
    print("[PRODUCTION_CUTOVER] FALSE")
    print("[CANONICAL_SCANNER] FROZEN")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

if __name__ == "__main__":
    main()
