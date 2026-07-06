from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
TARGET = ROOT / "oracle_portfolio_exposure_manager.py"
CONTINUOUS = ROOT / "oracle_continuous_intelligence.py"

CODE = r'''
"""
ORACLE-054 Portfolio Exposure Manager

Purpose:
- Track theoretical/pending exposure across Oracle opportunities.
- Prevent over-concentration by ticker, event family, category, side, and risk.
- Does NOT place trades.
"""

from datetime import datetime, UTC
from pathlib import Path
import json
import re

STATE_FILE = Path("oracle_portfolio_exposure_state.json")

DEFAULT_LIMITS = {
    "max_total_open_ideas": 25,
    "max_per_event_family": 4,
    "max_per_category": 8,
    "max_per_side": 15,
    "max_high_risk": 3,
    "max_blocked_watch": 10,
}


def _txt(v):
    return str(v or "").strip()


def _num(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


class OraclePortfolioExposureManager:
    def __init__(self):
        self.version = "ORACLE-054"
        self.state = {
            "limits": DEFAULT_LIMITS,
            "last_exposure": {},
            "history": [],
        }
        self._load()

    def analyze(self, ranked):
        ranked = ranked if isinstance(ranked, list) else []

        exposure = {
            "total": 0,
            "by_event_family": {},
            "by_category": {},
            "by_side": {},
            "by_risk": {},
            "by_execution": {},
            "blocked_watch_count": 0,
            "high_risk_count": 0,
            "items": [],
        }

        enriched = []

        for item in ranked:
            if not isinstance(item, dict):
                continue

            profile = self._profile(item)
            exposure["total"] += 1
            self._inc(exposure["by_event_family"], profile["event_family"])
            self._inc(exposure["by_category"], profile["category"])
            self._inc(exposure["by_side"], profile["side"])
            self._inc(exposure["by_risk"], profile["risk"])
            self._inc(exposure["by_execution"], profile["execution_decision"])

            if profile["risk"] == "HIGH":
                exposure["high_risk_count"] += 1

            if profile["execution_decision"] == "BLOCK" and profile["consensus"] == "WATCH":
                exposure["blocked_watch_count"] += 1

            exposure["items"].append(profile)

        limits = self.state.get("limits", DEFAULT_LIMITS)
        portfolio_alerts = self._portfolio_alerts(exposure, limits)

        for item in ranked:
            if not isinstance(item, dict):
                enriched.append(item)
                continue

            profile = self._profile(item)
            decision = self._exposure_decision(profile, exposure, limits)

            item["portfolio_exposure"] = {
                "module": "oracle_portfolio_exposure_manager",
                "version": self.version,
                "status": "ok",
                "profile": profile,
                "decision": decision["decision"],
                "score": decision["score"],
                "reason": decision["reason"],
                "flags": decision["flags"],
                "compact_card": self._card(profile, decision),
            }
            item["portfolio_decision"] = decision["decision"]
            item["portfolio_exposure_score"] = decision["score"]
            item["portfolio_card"] = item["portfolio_exposure"]["compact_card"]

            enriched.append(item)

        result = {
            "module": "oracle_portfolio_exposure_manager",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "limits": limits,
            "exposure": exposure,
            "portfolio_alerts": portfolio_alerts,
            "top": enriched[:10],
            "state_file": str(STATE_FILE),
        }

        self.state["last_exposure"] = result
        self.state["history"].append({
            "timestamp": result["timestamp"],
            "total": exposure["total"],
            "alerts": portfolio_alerts,
        })
        self.state["history"] = self.state["history"][-200:]
        self._save()

        return result

    def _profile(self, item):
        ticker = _txt(item.get("ticker"))
        title = _txt(item.get("title"))

        raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}
        raw_raw = raw.get("raw") if isinstance(raw.get("raw"), dict) else {}

        kind = _txt(raw_raw.get("kind") or raw.get("kind") or item.get("kind"))
        category = self._category(ticker, title, kind)
        event_family = self._event_family(ticker, title)
        side = _txt(item.get("side") or item.get("consensus_final_recommendation") or "WATCH").upper()
        risk = _txt(item.get("risk") or "UNKNOWN").upper()
        execution = _txt(item.get("execution_decision") or "UNKNOWN").upper()
        lifecycle = _txt(item.get("lifecycle_state") or "UNKNOWN").upper()
        consensus = _txt(item.get("consensus_final_recommendation") or "UNKNOWN").upper()

        return {
            "ticker": ticker,
            "title": title,
            "event_family": event_family,
            "category": category,
            "kind": kind,
            "side": side,
            "risk": risk,
            "execution_decision": execution,
            "lifecycle_state": lifecycle,
            "consensus": consensus,
            "consensus_confidence": _num(item.get("consensus_confidence"), 0),
            "adaptive_score": _num(item.get("adaptive_score") or item.get("overall_score"), 0),
            "tradability": _txt(item.get("tradability")).upper(),
            "order_book_rating": _txt(item.get("order_book_rating")).upper(),
            "flow_signal": _txt(item.get("flow_signal")).upper(),
            "tradable_edge": _num(item.get("tradable_edge"), 0),
        }

    def _category(self, ticker, title, kind):
        text = f"{ticker} {title} {kind}".lower()

        rules = [
            ("POLITICS", ["president", "senate", "house", "election", "democratic", "republican", "prime minister", "pope", "dnc"]),
            ("MACRO", ["fed", "inflation", "cpi", "gdp", "recession", "rates", "unemployment"]),
            ("AI_TECH", ["agi", "artificial intelligence", "openai", "ai "]),
            ("WEATHER", ["temperature", "hurricane", "rain", "snow", "weather"]),
            ("SPORTS", ["nba", "nfl", "mlb", "nhl", "championship", "game"]),
            ("CRYPTO", ["bitcoin", "btc", "ethereum", "eth", "crypto"]),
            ("ARBITRAGE", ["arbitrage", "time_ladder", "mutually_exclusive", "related_market"]),
        ]

        for cat, keys in rules:
            if any(k in text for k in keys):
                return cat

        return "GENERAL"

    def _event_family(self, ticker, title):
        ticker = ticker or "UNKNOWN"
        parts = ticker.split("-")
        if len(parts) >= 1 and parts[0]:
            return parts[0]

        clean = re.sub(r"[^A-Z0-9]+", "_", title.upper())[:32]
        return clean or "UNKNOWN"

    def _portfolio_alerts(self, exposure, limits):
        alerts = []

        if exposure["total"] > limits["max_total_open_ideas"]:
            alerts.append("Total open opportunity count exceeds limit")

        if exposure["high_risk_count"] > limits["max_high_risk"]:
            alerts.append("Too many high-risk opportunities")

        if exposure["blocked_watch_count"] > limits["max_blocked_watch"]:
            alerts.append("Too many blocked WATCH opportunities creating noise")

        for fam, count in exposure["by_event_family"].items():
            if count > limits["max_per_event_family"]:
                alerts.append(f"Event family concentration: {fam} has {count}")

        for cat, count in exposure["by_category"].items():
            if count > limits["max_per_category"]:
                alerts.append(f"Category concentration: {cat} has {count}")

        for side, count in exposure["by_side"].items():
            if count > limits["max_per_side"]:
                alerts.append(f"Side concentration: {side} has {count}")

        return alerts

    def _exposure_decision(self, profile, exposure, limits):
        score = 100.0
        flags = []

        fam_count = exposure["by_event_family"].get(profile["event_family"], 0)
        cat_count = exposure["by_category"].get(profile["category"], 0)
        side_count = exposure["by_side"].get(profile["side"], 0)

        if fam_count > limits["max_per_event_family"]:
            score -= 30
            flags.append("event_family_concentration")

        if cat_count > limits["max_per_category"]:
            score -= 20
            flags.append("category_concentration")

        if side_count > limits["max_per_side"]:
            score -= 15
            flags.append("side_concentration")

        if profile["risk"] == "HIGH":
            score -= 25
            flags.append("high_risk")

        if profile["execution_decision"] == "BLOCK":
            score -= 20
            flags.append("blocked_by_gatekeeper")

        if profile["tradability"] in ("POOR", "UNTRADABLE"):
            score -= 20
            flags.append("weak_tradability")

        if profile["order_book_rating"] in ("WEAK", "UNUSABLE"):
            score -= 15
            flags.append("weak_order_book")

        if profile["flow_signal"] in ("AVOID_FLOW", "DETERIORATING_FLOW"):
            score -= 10
            flags.append("weak_flow")

        if profile["execution_decision"] == "EXECUTE":
            score += 20
            flags.append("execution_candidate")

        score = max(0.0, min(100.0, score))

        if score >= 75:
            decision = "ALLOW"
        elif score >= 55:
            decision = "LIMIT_SIZE"
        elif score >= 35:
            decision = "REVIEW"
        else:
            decision = "BLOCK_EXPOSURE"

        return {
            "decision": decision,
            "score": round(score, 2),
            "flags": flags,
            "reason": (
                f"Portfolio decision {decision}. "
                f"family_count={fam_count}, category_count={cat_count}, side_count={side_count}."
            ),
        }

    def _card(self, profile, decision):
        return "\n".join([
            "🧺 ORACLE PORTFOLIO EXPOSURE",
            f"Ticker: {profile.get('ticker')}",
            f"Market: {profile.get('title')}",
            "",
            f"Decision: {decision.get('decision')}",
            f"Score: {decision.get('score')}",
            f"Category: {profile.get('category')}",
            f"Event Family: {profile.get('event_family')}",
            f"Side: {profile.get('side')}",
            f"Risk: {profile.get('risk')}",
            "",
            f"Reason: {decision.get('reason')}",
            "Flags:",
            *[f"- {f}" for f in decision.get("flags", [])[:8]],
        ])

    def _inc(self, d, k):
        k = k or "UNKNOWN"
        d[k] = d.get(k, 0) + 1

    def diagnostics(self):
        return {
            "module": "oracle_portfolio_exposure_manager",
            "version": self.version,
            "status": "ok",
            "limits": self.state.get("limits", DEFAULT_LIMITS),
            "state_file": str(STATE_FILE),
        }

    def _load(self):
        try:
            if STATE_FILE.exists():
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.state.update(data)
        except Exception:
            pass

    def _save(self):
        try:
            STATE_FILE.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        except Exception:
            pass


oracle_portfolio_exposure_manager = OraclePortfolioExposureManager()


if __name__ == "__main__":
    sample = [{
        "ticker": "TEST-MACRO-CPI",
        "title": "Sample CPI opportunity",
        "side": "BUY YES",
        "grade": "A-",
        "risk": "MEDIUM",
        "adaptive_score": 82,
        "consensus_final_recommendation": "BUY YES",
        "consensus_confidence": 84,
        "execution_decision": "WATCH_ONLY",
        "tradability": "CAUTION",
        "order_book_rating": "FAIR",
        "flow_signal": "IMPROVING_FLOW",
        "tradable_edge": 0.08,
    }]

    import pprint
    pprint.pp(oracle_portfolio_exposure_manager.analyze(sample))
'''

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-054 Portfolio Exposure Manager Integration
# ============================================================

try:
    from oracle_portfolio_exposure_manager import oracle_portfolio_exposure_manager
except Exception:
    oracle_portfolio_exposure_manager = None


def _oracle054_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            if oracle_portfolio_exposure_manager is None:
                _state["portfolio_exposure_status"] = {"status": "missing"}
                return

            if isinstance(ranked, list):
                result = oracle_portfolio_exposure_manager.analyze(ranked)
                _state["portfolio_exposure_status"] = result
                _state["last_ranked"] = ranked
            else:
                _state["portfolio_exposure_status"] = {"status": "no_ranked_data"}
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["portfolio_exposure_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle054_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle054_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle054_original_run_cycle(*args, **kwargs)
        _oracle054_enrich_state()
        return result


if "_oracle054_original_status" not in globals() and "status" in globals():
    _oracle054_original_status = status

    def status(*args, **kwargs):
        result = _oracle054_original_status(*args, **kwargs)
        _oracle054_enrich_state()

        if isinstance(result, dict):
            result["portfolio_exposure_status"] = (
                globals().get("_state", {}).get("portfolio_exposure_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-054
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle054_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-054 INSTALLER")
    print(" Portfolio Exposure Manager")
    print("===================================")

    backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")
    print("[OK] Created oracle_portfolio_exposure_manager.py")

    if not CONTINUOUS.exists():
        print("[WARN] oracle_continuous_intelligence.py not found; integration skipped")
    else:
        text = CONTINUOUS.read_text(encoding="utf-8", errors="ignore")
        if "ORACLE-054 Portfolio Exposure Manager Integration" in text:
            print("[SKIP] Continuous Intelligence already patched")
        else:
            b = backup(CONTINUOUS)
            marker = 'if __name__ == "__main__":'
            if marker in text:
                text = text.replace(marker, PATCH_BLOCK + "\n\n" + marker, 1)
            else:
                text += "\n\n" + PATCH_BLOCK + "\n"
            CONTINUOUS.write_text(text, encoding="utf-8")
            print("[OK] Patched oracle_continuous_intelligence.py")
            print(f"[OK] Backup created: {b}")

    print("")
    print("Tests:")
    print(" python oracle_portfolio_exposure_manager.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('portfolio_exposure_status',{}).get('portfolio_alerts')); print(s.get('last_ranked',[{}])[0].get('portfolio_card'))\"")
    print("")
    print("[DONE] ORACLE-054 Portfolio Exposure Manager installed")


if __name__ == "__main__":
    main()