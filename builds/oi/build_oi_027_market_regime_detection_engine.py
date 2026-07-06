from pathlib import Path
import textwrap

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
TEST_FILE = ROOT / "test_oi_027_market_regime_detection_engine.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

ENGINE = OI_DIR / "market_regime_detection_engine.py"

ENGINE.write_text(textwrap.dedent(r'''
"""
OI-027 Market Regime Detection Engine

Read-only Oracle Intelligence module.

Purpose:
- Detect broad market regimes from historical/current market behavior.
- Classify environments such as high-liquidity/high-volatility,
  thin-liquidity, event-driven, expiration-compression, overnight drift,
  weekend behavior, and normal baseline.
- Track regime transitions.
- Provide context only.
- No execution.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Dict, List, Optional


DEFAULT_DB_CANDIDATES = [
    Path("qseries_v2/ops/qseries_history.sqlite3"),
    Path("qseries_v2/data/qseries_history.sqlite3"),
    Path("qseries_history.sqlite3"),
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except Exception:
        return None


def _avg(values: List[float]) -> float:
    clean = [_safe_float(v) for v in values if v is not None]
    return round(mean(clean), 6) if clean else 0.0


def _std(values: List[float]) -> float:
    clean = [_safe_float(v) for v in values if v is not None]
    return round(pstdev(clean), 6) if len(clean) > 1 else 0.0


@dataclass
class RegimePacket:
    module: str
    status: str
    generated_at: str
    database: Optional[str]
    rows_analyzed: int
    current_regime: Dict[str, Any]
    regime_scores: Dict[str, Any]
    regime_features: Dict[str, Any]
    transition_history: List[Dict[str, Any]]
    oracle_context: Dict[str, Any]
    notes: List[str]
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketRegimeDetectionEngine:
    """
    Detects broad prediction-market regimes.

    This module is context-only. It never executes trades.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = self._resolve_db(db_path)
        self.last_packet: Optional[Dict[str, Any]] = None
        self.transition_history: List[Dict[str, Any]] = []

    def diagnostics(self) -> Dict[str, Any]:
        exists = bool(self.db_path and self.db_path.exists())
        return {
            "module": "OI-027 Market Regime Detection Engine",
            "status": "ok" if exists else "waiting_for_history_db",
            "database": str(self.db_path) if self.db_path else None,
            "database_exists": exists,
            "last_packet_ready": self.last_packet is not None,
            "transition_count": len(self.transition_history),
            "read_only": True,
            "execution_allowed": False,
        }

    def detect_regime(self, live_market: Optional[Dict[str, Any]] = None, limit: int = 100000) -> Dict[str, Any]:
        notes: List[str] = []

        if not self.db_path or not self.db_path.exists():
            packet = self._empty_packet("waiting_for_history_db", "Historical database not found yet.")
            self.last_packet = packet
            return packet

        rows = self._load_rows(limit=limit, notes=notes)

        if not rows:
            packet = self._empty_packet("waiting_for_history_rows", "Historical database exists but no usable rows were found.")
            self.last_packet = packet
            return packet

        features = self._features(rows, live_market)
        scores = self._score_regimes(features)
        current = self._select_regime(scores, features)
        self._record_transition(current)

        packet = RegimePacket(
            module="OI-027 Market Regime Detection Engine",
            status="ok",
            generated_at=self._now(),
            database=str(self.db_path),
            rows_analyzed=len(rows),
            current_regime=current,
            regime_scores=scores,
            regime_features=features,
            transition_history=self.transition_history[-25:],
            oracle_context=self._oracle_context(current, features),
            notes=notes or ["Market regime detection completed successfully."],
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        self.last_packet = packet
        return packet

    def get_regime(self) -> Dict[str, Any]:
        if self.last_packet is None:
            return self.detect_regime()
        return self.last_packet

    def regime_context(self) -> Dict[str, Any]:
        packet = self.get_regime()
        return packet.get("oracle_context", {})

    def transition_summary(self) -> Dict[str, Any]:
        return {
            "module": "OI-027 Market Regime Detection Engine",
            "status": "ok",
            "transitions": self.transition_history[-50:],
            "transition_count": len(self.transition_history),
            "read_only": True,
            "execution_allowed": False,
        }

    def _resolve_db(self, db_path: Optional[str]) -> Optional[Path]:
        if db_path:
            return Path(db_path)

        for candidate in DEFAULT_DB_CANDIDATES:
            if candidate.exists():
                return candidate

        return DEFAULT_DB_CANDIDATES[0]

    def _load_rows(self, limit: int, notes: List[str]) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        rows: List[Dict[str, Any]] = []

        try:
            tables = [
                r["name"]
                for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            ]

            candidate_tables = [
                t for t in tables
                if any(k in t.lower() for k in ["market", "history", "snapshot", "record"])
            ] or tables

            for table in candidate_tables:
                try:
                    columns = [c["name"] for c in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                    time_col = self._pick(columns, ["timestamp", "created_at", "recorded_at", "time", "updated_at"])
                    if not time_col:
                        continue

                    query = f"SELECT * FROM {table} ORDER BY {time_col} DESC LIMIT ?"
                    for row in conn.execute(query, (limit,)).fetchall():
                        normalized = self._normalize_row(dict(row), table)
                        if normalized:
                            rows.append(normalized)

                    if rows:
                        notes.append(f"Loaded regime rows from table: {table}")
                        break

                except Exception as exc:
                    notes.append(f"Skipped table {table}: {exc}")

        finally:
            conn.close()

        return rows[:limit]

    def _normalize_row(self, row: Dict[str, Any], table: str) -> Optional[Dict[str, Any]]:
        keys = list(row.keys())

        ts_key = self._pick(keys, ["timestamp", "created_at", "recorded_at", "time", "updated_at"])
        dt = _parse_dt(row.get(ts_key))
        if not dt:
            return None

        bid = _safe_float(row.get(self._pick(keys, ["bid", "best_bid", "yes_bid"])))
        ask = _safe_float(row.get(self._pick(keys, ["ask", "best_ask", "yes_ask"])))

        spread = _safe_float(row.get(self._pick(keys, ["spread", "bid_ask_spread"])))
        if spread == 0.0 and bid and ask:
            spread = abs(ask - bid)

        yes_price = _safe_float(row.get(self._pick(keys, ["yes_price", "yes_bid", "yes_ask", "price", "last_price"])))
        expiration = _parse_dt(row.get(self._pick(keys, ["expiration", "expiration_time", "close_time", "end_time"])))

        return {
            "source_table": table,
            "timestamp": dt,
            "ticker": str(row.get(self._pick(keys, ["ticker", "market_ticker", "symbol"])) or ""),
            "category": str(row.get(self._pick(keys, ["category", "market_category", "event_category", "type"])) or "unknown"),
            "hour": dt.hour,
            "weekday": dt.strftime("%A"),
            "is_weekend": dt.weekday() >= 5,
            "is_overnight": dt.hour < 7 or dt.hour >= 22,
            "expiration_hours": self._expiration_hours(dt, expiration),
            "liquidity": _safe_float(row.get(self._pick(keys, ["liquidity", "open_interest", "oi", "depth"]))),
            "spread": spread,
            "volume": _safe_float(row.get(self._pick(keys, ["volume", "volume_24h", "total_volume"]))),
            "price": yes_price,
        }

    def _features(self, rows: List[Dict[str, Any]], live_market: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        recent = rows[:min(len(rows), 250)]

        liquidity_values = [r["liquidity"] for r in recent]
        spread_values = [r["spread"] for r in recent]
        volume_values = [r["volume"] for r in recent]
        price_values = [r["price"] for r in recent]

        features = {
            "avg_liquidity": _avg(liquidity_values),
            "avg_spread": _avg(spread_values),
            "avg_volume": _avg(volume_values),
            "price_volatility": _std(price_values),
            "spread_volatility": _std(spread_values),
            "volume_volatility": _std(volume_values),
            "liquidity_volatility": _std(liquidity_values),
            "weekend_ratio": round(len([r for r in recent if r["is_weekend"]]) / max(len(recent), 1), 6),
            "overnight_ratio": round(len([r for r in recent if r["is_overnight"]]) / max(len(recent), 1), 6),
            "near_expiration_ratio": round(
                len([r for r in recent if r["expiration_hours"] is not None and r["expiration_hours"] < 6]) / max(len(recent), 1),
                6,
            ),
            "category_mix": self._category_mix(recent),
            "sample_size": len(recent),
        }

        if live_market:
            live = self._normalize_live(live_market)
            features["live_market"] = live
            features["live_liquidity_ratio"] = self._ratio(live["liquidity"], features["avg_liquidity"])
            features["live_spread_ratio"] = self._ratio(live["spread"], features["avg_spread"])
            features["live_volume_ratio"] = self._ratio(live["volume"], features["avg_volume"])
            features["live_price_extreme"] = live["price"] <= 15 or live["price"] >= 85
            features["live_near_expiration"] = live["expiration_hours"] is not None and live["expiration_hours"] < 6
            features["live_is_weekend"] = live["is_weekend"]
            features["live_is_overnight"] = live["is_overnight"]

        return features

    def _score_regimes(self, f: Dict[str, Any]) -> Dict[str, Any]:
        liq = _safe_float(f.get("avg_liquidity"))
        spread = _safe_float(f.get("avg_spread"))
        vol = _safe_float(f.get("avg_volume"))
        price_vol = _safe_float(f.get("price_volatility"))

        live_liq_ratio = _safe_float(f.get("live_liquidity_ratio"), 1.0)
        live_spread_ratio = _safe_float(f.get("live_spread_ratio"), 1.0)
        live_volume_ratio = _safe_float(f.get("live_volume_ratio"), 1.0)

        scores = {
            "high_liquidity_low_volatility": self._clamp((min(liq / 2500, 1) * 55) + (max(0, 1 - price_vol / 20) * 45)),
            "high_liquidity_high_volatility": self._clamp((min(liq / 2500, 1) * 45) + (min(price_vol / 20, 1) * 55)),
            "thin_liquidity": self._clamp(max(0, 1 - liq / 1500) * 100),
            "event_driven": self._clamp((min(live_volume_ratio / 2.5, 1) * 45) + (min(live_liq_ratio / 2.0, 1) * 35) + (min(price_vol / 25, 1) * 20)),
            "news_shock": self._clamp((min(live_volume_ratio / 3.0, 1) * 40) + (min(live_spread_ratio / 2.5, 1) * 30) + (min(price_vol / 30, 1) * 30)),
            "trend_expansion": self._clamp((min(vol / 2000, 1) * 35) + (min(price_vol / 18, 1) * 45) + (min(liq / 2500, 1) * 20)),
            "mean_reversion": self._clamp((max(0, 1 - price_vol / 15) * 40) + (max(0, 1 - live_spread_ratio / 2) * 30) + (min(liq / 2000, 1) * 30)),
            "expiration_compression": self._clamp((_safe_float(f.get("near_expiration_ratio")) * 70) + (35 if f.get("live_near_expiration") else 0)),
            "overnight_drift": self._clamp((_safe_float(f.get("overnight_ratio")) * 80) + (25 if f.get("live_is_overnight") else 0)),
            "weekend_behavior": self._clamp((_safe_float(f.get("weekend_ratio")) * 80) + (25 if f.get("live_is_weekend") else 0)),
            "normal_baseline": 45.0,
        }

        return {
            name: {
                "score": round(score, 4),
                "label": self._score_label(score),
            }
            for name, score in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        }

    def _select_regime(self, scores: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        name, data = next(iter(scores.items()))
        score = data["score"]

        return {
            "name": name,
            "score": score,
            "label": data["label"],
            "confidence": self._confidence(score, features),
            "description": self._description(name),
        }

    def _record_transition(self, current: Dict[str, Any]) -> None:
        previous = self.transition_history[-1]["regime"] if self.transition_history else None

        if previous != current["name"]:
            self.transition_history.append({
                "timestamp": self._now(),
                "from": previous,
                "to": current["name"],
                "regime": current["name"],
                "score": current["score"],
            })

    def _oracle_context(self, current: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "context_type": "market_regime",
            "module": "oracle_market_regime_context",
            "status": "ok",
            "current_regime": current,
            "feature_summary": {
                "avg_liquidity": features.get("avg_liquidity"),
                "avg_spread": features.get("avg_spread"),
                "avg_volume": features.get("avg_volume"),
                "price_volatility": features.get("price_volatility"),
                "sample_size": features.get("sample_size"),
            },
            "read_only": True,
            "execution_allowed": False,
        }

    def _empty_packet(self, status: str, note: str) -> Dict[str, Any]:
        return RegimePacket(
            module="OI-027 Market Regime Detection Engine",
            status=status,
            generated_at=self._now(),
            database=str(self.db_path) if self.db_path else None,
            rows_analyzed=0,
            current_regime={},
            regime_scores={},
            regime_features={},
            transition_history=self.transition_history[-25:],
            oracle_context={
                "context_type": "market_regime",
                "status": status,
                "read_only": True,
                "execution_allowed": False,
            },
            notes=[note],
            read_only=True,
            execution_allowed=False,
        ).to_dict()

    def _normalize_live(self, market: Dict[str, Any]) -> Dict[str, Any]:
        ts = _parse_dt(market.get("timestamp")) or datetime.now(timezone.utc)
        exp = _parse_dt(market.get("expiration") or market.get("expiration_time") or market.get("close_time") or market.get("end_time"))

        bid = _safe_float(market.get("bid") or market.get("best_bid") or market.get("yes_bid"))
        ask = _safe_float(market.get("ask") or market.get("best_ask") or market.get("yes_ask"))

        spread = _safe_float(market.get("spread") or market.get("bid_ask_spread"))
        if spread == 0.0 and bid and ask:
            spread = abs(ask - bid)

        price = _safe_float(market.get("yes_price") or market.get("price") or market.get("last_price") or market.get("yes_bid"))

        return {
            "timestamp": ts.isoformat(),
            "hour": ts.hour,
            "weekday": ts.strftime("%A"),
            "is_weekend": ts.weekday() >= 5,
            "is_overnight": ts.hour < 7 or ts.hour >= 22,
            "expiration_hours": self._expiration_hours(ts, exp),
            "liquidity": _safe_float(market.get("liquidity") or market.get("open_interest") or market.get("oi") or market.get("depth")),
            "spread": spread,
            "volume": _safe_float(market.get("volume") or market.get("volume_24h") or market.get("total_volume")),
            "price": price,
        }

    def _expiration_hours(self, timestamp: datetime, expiration: Optional[datetime]) -> Optional[float]:
        if not expiration:
            return None
        return round((expiration - timestamp).total_seconds() / 3600.0, 6)

    def _category_mix(self, rows: List[Dict[str, Any]]) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for row in rows:
            out[row["category"]] = out.get(row["category"], 0) + 1
        return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))

    def _ratio(self, value: float, base: float) -> float:
        if base == 0:
            return 1.0
        return round(value / base, 6)

    def _confidence(self, score: float, features: Dict[str, Any]) -> Dict[str, Any]:
        sample_size = _safe_float(features.get("sample_size"))
        sample_component = min(sample_size / 250.0, 1.0) * 100
        confidence = round((score * 0.7) + (sample_component * 0.3), 4)

        return {
            "score": confidence,
            "label": self._score_label(confidence),
            "sample_size": int(sample_size),
        }

    def _description(self, name: str) -> str:
        descriptions = {
            "high_liquidity_low_volatility": "Deep liquidity with controlled price movement.",
            "high_liquidity_high_volatility": "Deep liquidity with elevated price movement.",
            "thin_liquidity": "Low participation environment with weaker market depth.",
            "event_driven": "Activity suggests event-driven market attention.",
            "news_shock": "Volume, spreads, or volatility suggest shock-like behavior.",
            "trend_expansion": "Volume and volatility suggest directional expansion.",
            "mean_reversion": "Controlled volatility and tighter behavior suggest reversion conditions.",
            "expiration_compression": "Market behavior is dominated by time-to-expiration pressure.",
            "overnight_drift": "Behavior resembles overnight low-attention drift.",
            "weekend_behavior": "Behavior reflects weekend market structure.",
            "normal_baseline": "Market environment is near broad historical baseline.",
        }
        return descriptions.get(name, "Unknown market regime.")

    def _score_label(self, score: float) -> str:
        if score >= 85:
            return "very_high"
        if score >= 70:
            return "high"
        if score >= 50:
            return "moderate"
        if score >= 25:
            return "low"
        return "thin"

    def _clamp(self, value: float) -> float:
        return max(0.0, min(100.0, round(value, 6)))

    def _pick(self, keys: List[str], candidates: List[str]) -> Optional[str]:
        lower = {k.lower(): k for k in keys}
        for candidate in candidates:
            if candidate.lower() in lower:
                return lower[candidate.lower()]
        return None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_regime_engine = MarketRegimeDetectionEngine()
''').strip() + "\n", encoding="utf-8")

TEST_FILE.write_text(textwrap.dedent(r'''
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_intelligence.market_regime_detection_engine import MarketRegimeDetectionEngine


def build_test_db(path: Path):
    if path.exists():
        path.unlink()

    conn = sqlite3.connect(str(path))
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE market_history (
            timestamp TEXT,
            ticker TEXT,
            category TEXT,
            yes_price REAL,
            bid REAL,
            ask REAL,
            volume REAL,
            liquidity REAL,
            expiration TEXT
        )
    """)

    base = datetime(2026, 6, 29, 14, 0, tzinfo=timezone.utc)

    rows = []
    for i in range(300):
        ts = base - timedelta(minutes=i * 10)
        exp = ts + timedelta(hours=(i % 10) + 1)

        rows.append((
            ts.isoformat(),
            f"REGIME-{i}",
            "crypto" if i % 2 == 0 else "sports",
            45 + (i % 20),
            43 + (i % 10),
            47 + (i % 10),
            1500 + (i * 8),
            3000 + (i * 12),
            exp.isoformat(),
        ))

    cur.executemany("""
        INSERT INTO market_history
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def test_oi_027_market_regime_detection_engine():
    db_path = Path("test_oi_027_history.sqlite3")
    build_test_db(db_path)

    engine = MarketRegimeDetectionEngine(str(db_path))

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["database_exists"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "LIVE-REGIME",
        "category": "crypto",
        "timestamp": datetime(2026, 6, 29, 14, 30, tzinfo=timezone.utc).isoformat(),
        "expiration": datetime(2026, 6, 29, 17, 30, tzinfo=timezone.utc).isoformat(),
        "yes_price": 88,
        "bid": 86,
        "ask": 91,
        "volume": 9000,
        "liquidity": 12000,
    }

    packet = engine.detect_regime(live_market)
    assert packet["status"] == "ok"
    assert packet["rows_analyzed"] == 300
    assert packet["current_regime"]["name"]
    assert packet["current_regime"]["score"] >= 0
    assert packet["regime_scores"]
    assert packet["regime_features"]["sample_size"] > 0
    assert packet["oracle_context"]["context_type"] == "market_regime"
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    context = engine.regime_context()
    assert context["status"] == "ok"
    assert context["current_regime"]["name"] == packet["current_regime"]["name"]
    assert context["read_only"] is True
    assert context["execution_allowed"] is False

    summary = engine.transition_summary()
    assert summary["transition_count"] >= 1
    assert summary["read_only"] is True
    assert summary["execution_allowed"] is False

    db_path.unlink(missing_ok=True)

    print("[PASS] OI-027 Market Regime Detection Engine")
    print({
        "regime": packet["current_regime"]["name"],
        "score": packet["current_regime"]["score"],
        "confidence": packet["current_regime"]["confidence"],
        "transitions": summary["transition_count"],
    })


if __name__ == "__main__":
    test_oi_027_market_regime_detection_engine()
''').strip() + "\n", encoding="utf-8")

INIT = OI_DIR / "__init__.py"
content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""

line = "from .market_regime_detection_engine import MarketRegimeDetectionEngine, oracle_regime_engine\n"
if line not in content:
    content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")

print("========================================")
print(" OI-027 INSTALLER")
print(" Market Regime Detection Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT}")
print("")
print("[DONE] OI-027 installed")
print("")
print("Run:")
print("python test_oi_027_market_regime_detection_engine.py")