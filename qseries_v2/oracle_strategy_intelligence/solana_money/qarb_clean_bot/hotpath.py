from dataclasses import dataclass
from queue import SimpleQueue, Empty
from time import perf_counter_ns

MAX_ROUTE_AGE_MS = 750.0
MIN_NET_BPS = 20.0

@dataclass(frozen=True)
class QuoteUpdate:
    token: str
    pump_pool: str
    meteora_pool: str
    venue: str
    direction: str
    size_sol: float
    end_sol: float
    observed_ns: int
    sequence: int = 0

@dataclass(frozen=True)
class HotSignal:
    token: str
    direction: str
    size_sol: float
    end_sol: float
    net_sol: float
    net_bps: float
    route_age_ms: float
    decision_us: float
    execution_authority: bool = False

class HotBook:
    def __init__(self, max_age_ms=MAX_ROUTE_AGE_MS, min_net_bps=MIN_NET_BPS, clock_ns=perf_counter_ns):
        self.max_age_ms = float(max_age_ms)
        self.min_net_bps = float(min_net_bps)
        self.clock_ns = clock_ns
        self.pump = {}
        self.meteora = {}
        self.queue = SimpleQueue()

    def publish(self, update):
        self.queue.put(update)

    def drain_once(self):
        try:
            return self.ingest(self.queue.get_nowait())
        except Empty:
            return None

    def ingest(self, update):
        key = (
            update.token,
            update.pump_pool,
            update.meteora_pool,
            update.direction,
            float(update.size_sol),
        )
        if update.venue == "PUMPSWAP":
            self.pump[key] = update
        elif update.venue == "METEORA_DLMM":
            self.meteora[key] = update
        else:
            return None

        p = self.pump.get(key)
        m = self.meteora.get(key)
        if p is None or m is None:
            return None

        start_ns = self.clock_ns()
        now_ns = self.clock_ns()
        age_ms = max(now_ns - p.observed_ns, now_ns - m.observed_ns) / 1_000_000.0
        if age_ms > self.max_age_ms:
            return None

        start_sol = float(update.size_sol)
        end_sol = float(m.end_sol if update.direction == "PUMP_TO_METEORA" else p.end_sol)
        net_sol = end_sol - start_sol
        net_bps = (net_sol / start_sol) * 10000.0 if start_sol > 0 else -1e18
        if net_bps < self.min_net_bps:
            return None

        return HotSignal(
            token=update.token,
            direction=update.direction,
            size_sol=start_sol,
            end_sol=end_sol,
            net_sol=net_sol,
            net_bps=net_bps,
            route_age_ms=age_ms,
            decision_us=(self.clock_ns() - start_ns) / 1000.0,
            execution_authority=False,
        )

def benchmark(iterations=5000):
    book = HotBook()
    now = book.clock_ns()
    book.ingest(QuoteUpdate("T","P","M","PUMPSWAP","PUMP_TO_METEORA",0.05,0.054,now,1))
    samples = []
    last = None
    for i in range(int(iterations)):
        t = book.clock_ns()
        u = QuoteUpdate("T","P","M","METEORA_DLMM","PUMP_TO_METEORA",0.05,0.054,t,i+2)
        t0 = book.clock_ns()
        last = book.ingest(u)
        samples.append((book.clock_ns()-t0)/1000.0)
    samples.sort()
    return {
        "iterations": len(samples),
        "p50_us": samples[len(samples)//2],
        "p99_us": samples[min(len(samples)-1, int(len(samples)*0.99))],
        "under_750ms": bool(last is not None and last.route_age_ms <= 750.0),
    }
