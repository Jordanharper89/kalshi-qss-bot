try:
    from oracle_consensus_engine import oracle_consensus_engine
except Exception:
    oracle_consensus_engine = None

"""
ORACLE-037 — Continuous Intelligence Pipeline

Purpose:
- Run Oracle intelligence cycles in the background
- Pull opportunities from available Oracle sources
- Rank opportunities through ORACLE-033
- Save memory through ORACLE-029
- Detect events through ORACLE-034
- Maintain a live pipeline status snapshot

Safe module:
- Does not execute trades
- Does not place orders
"""

import time
import threading
import traceback

from oracle_event_pipeline import process_opportunities


DEFAULT_INTERVAL_SECONDS = 10.0

_lock = threading.Lock()
_thread = None
_running = False

_state = {
    "running": False,
    "started_at": None,
    "last_cycle_at": None,
    "last_error": None,
    "cycles_completed": 0,
    "opportunities_seen": 0,
    "ranked_count": 0,
    "events_detected": 0,
    "high_priority_events": 0,
    "last_ranked": [],
    "last_events": [],
}


def _now():
    return time.time()


def _safe_import_opportunities():
    """
    ORACLE-040.5:
    Primary source is now Market Intelligence.

    Flow:
    Kalshi event loader / universe file
        -> oracle_market_intelligence.analyze_universe()
        -> actionable intelligence cards
        -> continuous pipeline
    """
    # 1) Arbitrage alerts — highest priority inefficiency source
    try:
        from oracle_cross_market_arbitrage import run_arbitrage_scan, get_top_arbitrage

        run_arbitrage_scan()
        arb = get_top_arbitrage(limit=20)

        if isinstance(arb, list) and arb:
            converted = []
            for item in arb:
                converted.append({
                    "ticker": "ARBITRAGE-" + str(item.get("kind", "UNKNOWN")).upper(),
                    "title": item.get("title") or "Cross-market arbitrage alert",
                    "side": "WATCH",
                    "edge": item.get("edge"),
                    "confidence": item.get("confidence"),
                    "fair_value": 0,
                    "market_price": 0,
                    "volume": 0,
                    "age_seconds": 0,
                    "providers": ["oracle_arbitrage", "kalshi_universe"],
                    "recommendation": item.get("recommendation"),
                    "reason": item.get("reason"),
                    "raw": item,
                })

            return converted

    except Exception as e:
        print(f"[ORACLE-045.4] arbitrage source error: {e}")

    # 2) Alpha Discovery cards — final Oracle research layer
    try:
        from oracle_alpha_discovery import run_alpha_discovery, get_top_alpha

        run_alpha_discovery(limit=50)
        cards = get_top_alpha(limit=50)

        if isinstance(cards, list) and cards:
            return cards

    except Exception as e:
        print(f"[ORACLE-045.4] alpha discovery fallback error: {e}")

    # 2) Final Fusion fallback
    try:
        from oracle_final_fusion import run_final_fusion, get_top_final

        run_final_fusion(limit=50)
        cards = get_top_final(limit=50)

        if isinstance(cards, list) and cards:
            return cards

    except Exception as e:
        print(f"[ORACLE-044.4] final fusion fallback error: {e}")

    # 3) Market Intelligence fallback
    try:
        from oracle_market_intelligence import analyze_universe, get_top_intelligence

        analyze_universe(limit=500, top=50)
        cards = get_top_intelligence(limit=50)

        if isinstance(cards, list) and cards:
            return cards

    except Exception as e:
        print(f"[ORACLE-044.4] market intelligence fallback error: {e}")

    # 2) Live research adapter fallback
    try:
        from oracle_live_research_adapter import get_live_opportunities

        opportunities = get_live_opportunities(limit=100)
        if isinstance(opportunities, list) and opportunities:
            return opportunities

    except Exception as e:
        print(f"[ORACLE-040.5] live research adapter fallback error: {e}")

    # 3) Existing opportunity feed fallback
    try:
        from oracle_opportunity_feed import build_oracle_opportunity_feed

        try:
            opportunities = build_oracle_opportunity_feed(
                watched_markets=[],
                min_grade="C",
                min_edge=0,
                min_confidence=0,
                max_items=50,
            )
        except TypeError:
            opportunities = build_oracle_opportunity_feed()

        if isinstance(opportunities, list) and opportunities:
            return opportunities

    except Exception:
        pass

    # 4) Research engine snapshot fallback
    try:
        from oracle_research_engine import oracle_research_engine

        snap = oracle_research_engine.get_snapshot()

        if isinstance(snap, dict):
            for key in ("opportunities", "ranked", "signals", "markets"):
                value = snap.get(key)
                if isinstance(value, list) and value:
                    return value

    except Exception:
        pass

    return []


def run_cycle(opportunities=None):
    """
    Run one complete intelligence cycle.
    Can be called manually for testing.
    """
    global _state

    started = _now()

    try:
        if opportunities is None:
            opportunities = _safe_import_opportunities()

        opportunities = opportunities or []

        result = process_opportunities(
            opportunities,
            limit=25,
            remember=True,
            detect_events=True,
        )

        ranked = result.get("ranked", [])
        events = result.get("events", [])
        high_events = [e for e in events if str(e.get("priority", "")).upper() == "HIGH"]

        with _lock:
            _state["running"] = _running
            _state["last_cycle_at"] = started
            _state["last_error"] = None
            _state["cycles_completed"] += 1
            _state["opportunities_seen"] = len(opportunities)
            _state["ranked_count"] = len(ranked)
            _state["events_detected"] = len(events)
            _state["high_priority_events"] = len(high_events)
            _state["last_ranked"] = ranked[:10]
            _state["last_events"] = events[:10]

        return {
            "ok": True,
            "opportunities_seen": len(opportunities),
            "ranked": len(ranked),
            "events": len(events),
            "high_priority_events": len(high_events),
        }

    except Exception as e:
        err = traceback.format_exc()

        with _lock:
            _state["last_cycle_at"] = started
            _state["last_error"] = str(e)

        print("[ORACLE-037] Continuous intelligence cycle error:")
        print(err)

        return {
            "ok": False,
            "error": str(e),
        }


def _loop(interval_seconds):
    global _running

    while _running:
        run_cycle()
        time.sleep(interval_seconds)


def start(interval_seconds=DEFAULT_INTERVAL_SECONDS):
    """
    Start the continuous intelligence pipeline.
    Safe to call multiple times.
    """
    global _thread, _running, _state

    if _running:
        return {
            "ok": True,
            "already_running": True,
        }

    _running = True

    with _lock:
        _state["running"] = True
        _state["started_at"] = _now()
        _state["last_error"] = None

    _thread = threading.Thread(
        target=_loop,
        args=(float(interval_seconds),),
        daemon=True,
        name="OracleContinuousIntelligence",
    )
    _thread.start()

    print(f"[ORACLE-037] Continuous Intelligence Pipeline started interval={interval_seconds}s")

    return {
        "ok": True,
        "started": True,
        "interval_seconds": float(interval_seconds),
    }


def stop():
    global _running

    _running = False

    with _lock:
        _state["running"] = False

    print("[ORACLE-037] Continuous Intelligence Pipeline stopped")

    return {
        "ok": True,
        "stopped": True,
    }


def status():
    with _lock:
        snap = dict(_state)

    if snap.get("last_cycle_at"):
        snap["age_seconds"] = round(_now() - snap["last_cycle_at"], 2)
    else:
        snap["age_seconds"] = None

    return snap


def format_status():
    s = status()

    return f"""
🧠 ORACLE CONTINUOUS INTELLIGENCE

Running:
{s.get("running")}

Cycles Completed:
{s.get("cycles_completed")}

Last Cycle Age:
{s.get("age_seconds")}

Opportunities Seen:
{s.get("opportunities_seen")}

Ranked:
{s.get("ranked_count")}

Events Detected:
{s.get("events_detected")}

High Priority Events:
{s.get("high_priority_events")}

Last Error:
{s.get("last_error")}

Status:
Continuous Intelligence Pipeline installed.
""".strip()


def diagnostics():
    """
    ORACLE-040.6:
    Diagnostics now tests the real live Market Intelligence source,
    not the old hardcoded sample opportunity.
    """
    result = run_cycle(opportunities=None)

    return {
        "module": "oracle_continuous_intelligence",
        "status": "ok",
        "cycle_result": result,
        "pipeline_status": status(),
    }




# ============================================================
# ORACLE-046.0.2 Architecture-Aware Consensus Integration
# ============================================================

try:
    from oracle_consensus_engine import oracle_consensus_engine
except Exception:
    oracle_consensus_engine = None


def _oracle046_apply_consensus_to_ranked(ranked):
    if oracle_consensus_engine is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            consensus = oracle_consensus_engine.calculate_consensus(item)

            item["consensus"] = consensus
            item["consensus_confidence"] = consensus.get("consensus_confidence", 0)
            item["consensus_strength"] = consensus.get("consensus_strength", "UNKNOWN")
            item["consensus_final_recommendation"] = consensus.get("final_recommendation", "WATCH")
            item["engine_agreement_pct"] = consensus.get("engine_agreement_pct", 0)
            item["weighted_agreement"] = consensus.get("weighted_agreement", 0)
            item["consensus_conflicts"] = consensus.get("conflicts", [])

            base_score = float(item.get("adaptive_score", item.get("overall_score", 0)) or 0)
            consensus_conf = float(consensus.get("consensus_confidence", 0) or 0)
            weighted_agreement = float(consensus.get("weighted_agreement", 0) or 0)

            item["consensus_rank_score"] = round(
                (base_score * 0.45)
                + (consensus_conf * 0.40)
                + (weighted_agreement * 0.15),
                2,
            )

        except Exception as exc:
            item["consensus"] = {
                "status": "error",
                "error": str(exc),
                "final_recommendation": "WATCH",
            }
            item["consensus_confidence"] = 0
            item["consensus_strength"] = "ERROR"
            item["consensus_final_recommendation"] = "WATCH"
            item["consensus_rank_score"] = float(item.get("adaptive_score", item.get("overall_score", 0)) or 0)

        enriched.append(item)

    enriched.sort(
        key=lambda x: x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0)))
        if isinstance(x, dict) else 0,
        reverse=True,
    )

    return enriched


def _oracle046_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            if isinstance(_state.get("last_ranked"), list):
                _state["last_ranked"] = _oracle046_apply_consensus_to_ranked(_state["last_ranked"])

            _state["consensus_status"] = {
                "status": "ok" if oracle_consensus_engine is not None else "missing",
                "ranked_with_consensus": len(_state.get("last_ranked") or []),
                "top_consensus": (_state.get("last_ranked") or [])[:5],
            }
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["consensus_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle046_original_process_opportunities" not in globals() and "process_opportunities" in globals():
    _oracle046_original_process_opportunities = process_opportunities

    def process_opportunities(*args, **kwargs):
        result = _oracle046_original_process_opportunities(*args, **kwargs)

        if isinstance(result, list):
            result = _oracle046_apply_consensus_to_ranked(result)

        if isinstance(result, dict):
            for key in ("ranked", "last_ranked", "opportunities"):
                if isinstance(result.get(key), list):
                    result[key] = _oracle046_apply_consensus_to_ranked(result[key])

        _oracle046_enrich_state()
        return result


if "_oracle046_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle046_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle046_original_run_cycle(*args, **kwargs)
        _oracle046_enrich_state()
        return result


if "_oracle046_original_status" not in globals() and "status" in globals():
    _oracle046_original_status = status

    def status(*args, **kwargs):
        result = _oracle046_original_status(*args, **kwargs)
        _oracle046_enrich_state()

        if isinstance(result, dict):
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = _oracle046_apply_consensus_to_ranked(result["last_ranked"])

            if isinstance(result.get("pipeline_status"), dict):
                ps = result["pipeline_status"]
                if isinstance(ps.get("last_ranked"), list):
                    ps["last_ranked"] = _oracle046_apply_consensus_to_ranked(ps["last_ranked"])

            result["consensus_status"] = {
                "status": "ok" if oracle_consensus_engine is not None else "missing",
                "ranked_with_consensus": len(result.get("last_ranked") or result.get("pipeline_status", {}).get("last_ranked") or []),
            }

        return result


if "_oracle046_original_diagnostics" not in globals() and "diagnostics" in globals():
    _oracle046_original_diagnostics = diagnostics

    def diagnostics(*args, **kwargs):
        result = _oracle046_original_diagnostics(*args, **kwargs)
        if isinstance(result, dict):
            result["oracle_046_consensus_integration"] = {
                "status": "installed",
                "engine_available": oracle_consensus_engine is not None,
            }
        return result

# ============================================================
# END ORACLE-046.0.2
# ============================================================




# ============================================================
# ORACLE-047 Execution Gatekeeper Integration
# ============================================================

try:
    from oracle_execution_gatekeeper import oracle_execution_gatekeeper
except Exception:
    oracle_execution_gatekeeper = None


def _oracle047_apply_execution_gatekeeper(ranked):
    if oracle_execution_gatekeeper is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            gate = oracle_execution_gatekeeper.evaluate(item)
            item["execution_gate"] = gate
            item["execution_decision"] = gate.get("execution_decision")
            item["execution_reason"] = gate.get("reason")
            item["execution_card"] = gate.get("compact_card")
        except Exception as exc:
            item["execution_gate"] = {
                "status": "error",
                "execution_decision": "BLOCK",
                "reason": str(exc),
            }
            item["execution_decision"] = "BLOCK"
            item["execution_reason"] = str(exc)

        enriched.append(item)

    decision_rank = {
        "EXECUTE": 4,
        "REQUIRES_REVIEW": 3,
        "WATCH_ONLY": 2,
        "BLOCK": 1,
    }

    enriched.sort(
        key=lambda x: (
            decision_rank.get(x.get("execution_decision"), 0),
            x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0))),
        ) if isinstance(x, dict) else (0, 0),
        reverse=True,
    )

    return enriched


def _oracle047_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            if isinstance(_state.get("last_ranked"), list):
                _state["last_ranked"] = _oracle047_apply_execution_gatekeeper(_state["last_ranked"])

            ranked = _state.get("last_ranked") or []
            counts = {}
            for item in ranked:
                if isinstance(item, dict):
                    d = item.get("execution_decision", "UNKNOWN")
                    counts[d] = counts.get(d, 0) + 1

            _state["execution_gatekeeper_status"] = {
                "status": "ok" if oracle_execution_gatekeeper is not None else "missing",
                "decision_counts": counts,
                "top": ranked[:5],
            }
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["execution_gatekeeper_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle047_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle047_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle047_original_run_cycle(*args, **kwargs)
        _oracle047_enrich_state()
        return result


if "_oracle047_original_status" not in globals() and "status" in globals():
    _oracle047_original_status = status

    def status(*args, **kwargs):
        result = _oracle047_original_status(*args, **kwargs)
        _oracle047_enrich_state()

        if isinstance(result, dict):
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = _oracle047_apply_execution_gatekeeper(result["last_ranked"])

            if isinstance(result.get("pipeline_status"), dict):
                ps = result["pipeline_status"]
                if isinstance(ps.get("last_ranked"), list):
                    ps["last_ranked"] = _oracle047_apply_execution_gatekeeper(ps["last_ranked"])

            result["execution_gatekeeper_status"] = (
                globals().get("_state", {}).get("execution_gatekeeper_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )

        return result

# ============================================================
# END ORACLE-047
# ============================================================




# ============================================================
# ORACLE-048 Market Microstructure Integration
# ============================================================

try:
    from oracle_market_microstructure import oracle_market_microstructure
except Exception:
    oracle_market_microstructure = None


def _oracle048_apply_microstructure(ranked):
    if oracle_market_microstructure is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            micro = oracle_market_microstructure.analyze(item)
            item["microstructure"] = micro
            item["tradability"] = micro.get("tradability")
            item["microstructure_score"] = micro.get("microstructure_score")
            item["microstructure_risks"] = micro.get("risks", [])
            item["microstructure_blockers"] = micro.get("blockers", [])
            item["microstructure_card"] = micro.get("compact_card")
        except Exception as exc:
            item["microstructure"] = {
                "status": "error",
                "tradability": "UNTRADABLE",
                "reason": str(exc),
            }
            item["tradability"] = "UNTRADABLE"
            item["microstructure_score"] = 0

        enriched.append(item)

    tradability_rank = {
        "GOOD": 4,
        "CAUTION": 3,
        "POOR": 2,
        "UNTRADABLE": 1,
    }

    enriched.sort(
        key=lambda x: (
            tradability_rank.get(x.get("tradability"), 0),
            x.get("execution_decision") == "EXECUTE",
            x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0))),
        ) if isinstance(x, dict) else (0, False, 0),
        reverse=True,
    )

    return enriched


def _oracle048_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            if isinstance(_state.get("last_ranked"), list):
                _state["last_ranked"] = _oracle048_apply_microstructure(_state["last_ranked"])

            ranked = _state.get("last_ranked") or []
            counts = {}
            for item in ranked:
                if isinstance(item, dict):
                    t = item.get("tradability", "UNKNOWN")
                    counts[t] = counts.get(t, 0) + 1

            _state["microstructure_status"] = {
                "status": "ok" if oracle_market_microstructure is not None else "missing",
                "tradability_counts": counts,
                "top": ranked[:5],
            }
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["microstructure_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle048_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle048_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle048_original_run_cycle(*args, **kwargs)
        _oracle048_enrich_state()
        return result


if "_oracle048_original_status" not in globals() and "status" in globals():
    _oracle048_original_status = status

    def status(*args, **kwargs):
        result = _oracle048_original_status(*args, **kwargs)
        _oracle048_enrich_state()

        if isinstance(result, dict):
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = _oracle048_apply_microstructure(result["last_ranked"])

            if isinstance(result.get("pipeline_status"), dict):
                ps = result["pipeline_status"]
                if isinstance(ps.get("last_ranked"), list):
                    ps["last_ranked"] = _oracle048_apply_microstructure(ps["last_ranked"])

            result["microstructure_status"] = (
                globals().get("_state", {}).get("microstructure_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )

        return result

# ============================================================
# END ORACLE-048
# ============================================================




# ============================================================
# ORACLE-049 Live Order Book Intelligence Integration
# ============================================================

try:
    from oracle_order_book_intelligence import oracle_order_book_intelligence
except Exception:
    oracle_order_book_intelligence = None


def _oracle049_apply_order_book_intelligence(ranked):
    if oracle_order_book_intelligence is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            obi = oracle_order_book_intelligence.analyze(item)
            item["order_book_intelligence"] = obi
            item["order_book_rating"] = obi.get("order_book_rating")
            item["order_book_score"] = obi.get("score")
            item["tradable_edge"] = obi.get("metrics", {}).get("tradable_edge")
            item["execution_cost"] = obi.get("metrics", {}).get("execution_cost")
            item["fill_probability"] = obi.get("metrics", {}).get("fill_probability")
            item["best_execution_size"] = obi.get("metrics", {}).get("best_execution_size")
            item["order_book_card"] = obi.get("compact_card")
        except Exception as exc:
            item["order_book_intelligence"] = {
                "status": "error",
                "order_book_rating": "UNUSABLE",
                "reason": str(exc),
            }
            item["order_book_rating"] = "UNUSABLE"
            item["order_book_score"] = 0

        enriched.append(item)

    rating_rank = {
        "GOOD": 4,
        "FAIR": 3,
        "WEAK": 2,
        "UNUSABLE": 1,
    }

    enriched.sort(
        key=lambda x: (
            rating_rank.get(x.get("order_book_rating"), 0),
            x.get("tradable_edge", 0) or 0,
            x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0))),
        ) if isinstance(x, dict) else (0, 0, 0),
        reverse=True,
    )

    return enriched


def _oracle049_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            if isinstance(_state.get("last_ranked"), list):
                _state["last_ranked"] = _oracle049_apply_order_book_intelligence(_state["last_ranked"])

            ranked = _state.get("last_ranked") or []
            counts = {}
            for item in ranked:
                if isinstance(item, dict):
                    r = item.get("order_book_rating", "UNKNOWN")
                    counts[r] = counts.get(r, 0) + 1

            _state["order_book_intelligence_status"] = {
                "status": "ok" if oracle_order_book_intelligence is not None else "missing",
                "rating_counts": counts,
                "top": ranked[:5],
            }
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["order_book_intelligence_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle049_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle049_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle049_original_run_cycle(*args, **kwargs)
        _oracle049_enrich_state()
        return result


if "_oracle049_original_status" not in globals() and "status" in globals():
    _oracle049_original_status = status

    def status(*args, **kwargs):
        result = _oracle049_original_status(*args, **kwargs)
        _oracle049_enrich_state()

        if isinstance(result, dict):
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = _oracle049_apply_order_book_intelligence(result["last_ranked"])

            if isinstance(result.get("pipeline_status"), dict):
                ps = result["pipeline_status"]
                if isinstance(ps.get("last_ranked"), list):
                    ps["last_ranked"] = _oracle049_apply_order_book_intelligence(ps["last_ranked"])

            result["order_book_intelligence_status"] = (
                globals().get("_state", {}).get("order_book_intelligence_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )

        return result

# ============================================================
# END ORACLE-049
# ============================================================




# ============================================================
# ORACLE-050 Live Order Flow Integration
# ============================================================

try:
    from oracle_order_flow_engine import oracle_order_flow_engine
except Exception:
    oracle_order_flow_engine = None


def _oracle050_apply_order_flow(ranked):
    if oracle_order_flow_engine is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            flow = oracle_order_flow_engine.analyze(item)
            item["order_flow"] = flow
            item["flow_signal"] = flow.get("flow_signal")
            item["flow_score"] = flow.get("flow_score")
            item["flow_flags"] = flow.get("flags", [])
            item["order_flow_card"] = flow.get("compact_card")
        except Exception as exc:
            item["order_flow"] = {
                "status": "error",
                "flow_signal": "UNKNOWN",
                "reason": str(exc),
            }
            item["flow_signal"] = "UNKNOWN"
            item["flow_score"] = 0

        enriched.append(item)

    flow_rank = {
        "BULLISH_FLOW": 5,
        "IMPROVING_FLOW": 4,
        "NEUTRAL_FLOW": 3,
        "DETERIORATING_FLOW": 2,
        "AVOID_FLOW": 1,
        "NEW": 3,
        "UNKNOWN": 0,
    }

    enriched.sort(
        key=lambda x: (
            flow_rank.get(x.get("flow_signal"), 0),
            x.get("flow_score", 0) or 0,
            x.get("tradable_edge", 0) or 0,
            x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0))),
        ) if isinstance(x, dict) else (0, 0, 0, 0),
        reverse=True,
    )

    return enriched


def _oracle050_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            if isinstance(_state.get("last_ranked"), list):
                _state["last_ranked"] = _oracle050_apply_order_flow(_state["last_ranked"])

            ranked = _state.get("last_ranked") or []
            counts = {}
            for item in ranked:
                if isinstance(item, dict):
                    sig = item.get("flow_signal", "UNKNOWN")
                    counts[sig] = counts.get(sig, 0) + 1

            _state["order_flow_status"] = {
                "status": "ok" if oracle_order_flow_engine is not None else "missing",
                "flow_counts": counts,
                "top": ranked[:5],
            }
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["order_flow_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle050_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle050_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle050_original_run_cycle(*args, **kwargs)
        _oracle050_enrich_state()
        return result


if "_oracle050_original_status" not in globals() and "status" in globals():
    _oracle050_original_status = status

    def status(*args, **kwargs):
        result = _oracle050_original_status(*args, **kwargs)
        _oracle050_enrich_state()

        if isinstance(result, dict):
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = _oracle050_apply_order_flow(result["last_ranked"])

            if isinstance(result.get("pipeline_status"), dict):
                ps = result["pipeline_status"]
                if isinstance(ps.get("last_ranked"), list):
                    ps["last_ranked"] = _oracle050_apply_order_flow(ps["last_ranked"])

            result["order_flow_status"] = (
                globals().get("_state", {}).get("order_flow_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )

        return result

# ============================================================
# END ORACLE-050
# ============================================================




# ============================================================
# ORACLE-051 Live Opportunity Monitor Integration
# ============================================================

try:
    from oracle_live_opportunity_monitor import oracle_live_opportunity_monitor
except Exception:
    oracle_live_opportunity_monitor = None


def _oracle051_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            if isinstance(ranked, list) and oracle_live_opportunity_monitor is not None:
                monitor_status = oracle_live_opportunity_monitor.observe(ranked)
                _state["live_monitor_status"] = monitor_status
                _state["live_monitor_events"] = monitor_status.get("events", [])
            else:
                _state["live_monitor_status"] = {
                    "status": "missing" if oracle_live_opportunity_monitor is None else "no_ranked_data"
                }
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["live_monitor_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle051_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle051_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle051_original_run_cycle(*args, **kwargs)
        _oracle051_enrich_state()
        return result


if "_oracle051_original_status" not in globals() and "status" in globals():
    _oracle051_original_status = status

    def status(*args, **kwargs):
        result = _oracle051_original_status(*args, **kwargs)
        _oracle051_enrich_state()

        if isinstance(result, dict):
            result["live_monitor_status"] = (
                globals().get("_state", {}).get("live_monitor_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["live_monitor_events"] = (
                globals().get("_state", {}).get("live_monitor_events")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-051
# ============================================================




# ============================================================
# ORACLE-052 Opportunity Lifecycle Integration
# ============================================================

try:
    from oracle_opportunity_lifecycle import oracle_opportunity_lifecycle
except Exception:
    oracle_opportunity_lifecycle = None


def _oracle052_apply_lifecycle(ranked):
    if oracle_opportunity_lifecycle is None or not isinstance(ranked, list):
        return ranked, {"status": "missing"}

    result = oracle_opportunity_lifecycle.update(ranked)
    updated = result.get("top") if isinstance(result, dict) else None

    # update() mutates the original ranked item objects, so return ranked.
    return ranked, result


def _oracle052_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            if isinstance(ranked, list):
                enriched, status_obj = _oracle052_apply_lifecycle(ranked)

                lifecycle_rank = {
                    "EXECUTION_READY": 7,
                    "IMPROVING": 6,
                    "ACTIVE": 5,
                    "NEW": 4,
                    "DECAYING": 3,
                    "STALE": 2,
                    "BLOCKED": 1,
                }

                enriched.sort(
                    key=lambda x: (
                        lifecycle_rank.get(x.get("lifecycle_state"), 0),
                        x.get("lifecycle_score", 0) or 0,
                        x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0))),
                    ) if isinstance(x, dict) else (0, 0, 0),
                    reverse=True,
                )

                _state["last_ranked"] = enriched
                _state["lifecycle_status"] = status_obj
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["lifecycle_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle052_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle052_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle052_original_run_cycle(*args, **kwargs)
        _oracle052_enrich_state()
        return result


if "_oracle052_original_status" not in globals() and "status" in globals():
    _oracle052_original_status = status

    def status(*args, **kwargs):
        result = _oracle052_original_status(*args, **kwargs)
        _oracle052_enrich_state()

        if isinstance(result, dict):
            result["lifecycle_status"] = (
                globals().get("_state", {}).get("lifecycle_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-052
# ============================================================




# ============================================================
# ORACLE-053 Smart Alert Prioritizer Integration
# ============================================================

try:
    from oracle_smart_alert_prioritizer import oracle_smart_alert_prioritizer
except Exception:
    oracle_smart_alert_prioritizer = None


def _oracle053_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            if oracle_smart_alert_prioritizer is None:
                _state["smart_alert_status"] = {"status": "missing"}
                _state["smart_alerts"] = []
                return

            snapshot = dict(_state)
            result = oracle_smart_alert_prioritizer.prioritize(snapshot)
            _state["smart_alert_status"] = result
            _state["smart_alerts"] = result.get("top_alerts", [])
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["smart_alert_status"] = {
                "status": "error",
                "error": str(exc),
            }
            _state["smart_alerts"] = []


if "_oracle053_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle053_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle053_original_run_cycle(*args, **kwargs)
        _oracle053_enrich_state()
        return result


if "_oracle053_original_status" not in globals() and "status" in globals():
    _oracle053_original_status = status

    def status(*args, **kwargs):
        result = _oracle053_original_status(*args, **kwargs)
        _oracle053_enrich_state()

        if isinstance(result, dict):
            result["smart_alert_status"] = (
                globals().get("_state", {}).get("smart_alert_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["smart_alerts"] = (
                globals().get("_state", {}).get("smart_alerts")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-053
# ============================================================




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




# ============================================================
# ORACLE-055 Execution Queue Manager Integration
# ============================================================

try:
    from oracle_execution_queue_manager import oracle_execution_queue_manager
except Exception:
    oracle_execution_queue_manager = None


def _oracle055_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            smart_alerts = _state.get("smart_alerts", [])

            if oracle_execution_queue_manager is None:
                _state["execution_queue_status"] = {"status": "missing"}
                _state["execution_queue"] = []
                return

            if isinstance(ranked, list):
                result = oracle_execution_queue_manager.build_queue(ranked, smart_alerts)
                _state["execution_queue_status"] = result
                _state["execution_queue"] = result.get("queue", [])
            else:
                _state["execution_queue_status"] = {"status": "no_ranked_data"}
                _state["execution_queue"] = []
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["execution_queue_status"] = {
                "status": "error",
                "error": str(exc),
            }
            _state["execution_queue"] = []


if "_oracle055_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle055_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle055_original_run_cycle(*args, **kwargs)
        _oracle055_enrich_state()
        return result


if "_oracle055_original_status" not in globals() and "status" in globals():
    _oracle055_original_status = status

    def status(*args, **kwargs):
        result = _oracle055_original_status(*args, **kwargs)
        _oracle055_enrich_state()

        if isinstance(result, dict):
            result["execution_queue_status"] = (
                globals().get("_state", {}).get("execution_queue_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["execution_queue"] = (
                globals().get("_state", {}).get("execution_queue")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-055
# ============================================================




# ============================================================
# ORACLE-056 Live Price Discovery Integration
# ============================================================

try:
    from oracle_live_price_discovery import oracle_live_price_discovery
except Exception:
    oracle_live_price_discovery = None


def _oracle056_apply_price_discovery(ranked):
    if oracle_live_price_discovery is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            pd = oracle_live_price_discovery.analyze(item)
            item["price_discovery"] = pd
            item["price_quality"] = pd.get("quality")
            item["price_quality_score"] = pd.get("quality_score")
            item["price_metrics"] = pd.get("metrics", {})
            item["price_discovery_card"] = pd.get("compact_card")
        except Exception as exc:
            item["price_discovery"] = {
                "status": "error",
                "quality": "VERY_LOW",
                "reason": str(exc),
            }
            item["price_quality"] = "VERY_LOW"
            item["price_quality_score"] = 0

        enriched.append(item)

    quality_rank = {
        "HIGH": 4,
        "MEDIUM": 3,
        "LOW": 2,
        "VERY_LOW": 1,
    }

    enriched.sort(
        key=lambda x: (
            quality_rank.get(x.get("price_quality"), 0),
            x.get("price_quality_score", 0) or 0,
            x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0))),
        ) if isinstance(x, dict) else (0, 0, 0),
        reverse=True,
    )

    return enriched


def _oracle056_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            if isinstance(ranked, list):
                _state["last_ranked"] = _oracle056_apply_price_discovery(ranked)

                counts = {}
                for item in _state["last_ranked"]:
                    if isinstance(item, dict):
                        q = item.get("price_quality", "UNKNOWN")
                        counts[q] = counts.get(q, 0) + 1

                _state["price_discovery_status"] = {
                    "status": "ok" if oracle_live_price_discovery is not None else "missing",
                    "quality_counts": counts,
                    "top": _state["last_ranked"][:5],
                }
            else:
                _state["price_discovery_status"] = {"status": "no_ranked_data"}
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["price_discovery_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle056_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle056_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle056_original_run_cycle(*args, **kwargs)
        _oracle056_enrich_state()
        return result


if "_oracle056_original_status" not in globals() and "status" in globals():
    _oracle056_original_status = status

    def status(*args, **kwargs):
        result = _oracle056_original_status(*args, **kwargs)
        _oracle056_enrich_state()

        if isinstance(result, dict):
            result["price_discovery_status"] = (
                globals().get("_state", {}).get("price_discovery_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-056
# ============================================================




# ============================================================
# ORACLE-057 Market Regime Engine Integration
# ============================================================

try:
    from oracle_market_regime_engine import oracle_market_regime_engine
except Exception:
    oracle_market_regime_engine = None


def _oracle057_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")

            if oracle_market_regime_engine is None:
                _state["market_regime_status"] = {"status": "missing"}
                return

            result = oracle_market_regime_engine.analyze(ranked if isinstance(ranked, list) else [])
            _state["market_regime_status"] = result
            _state["market_regime"] = result.get("regime")
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["market_regime_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle057_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle057_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle057_original_run_cycle(*args, **kwargs)
        _oracle057_enrich_state()
        return result


if "_oracle057_original_status" not in globals() and "status" in globals():
    _oracle057_original_status = status

    def status(*args, **kwargs):
        result = _oracle057_original_status(*args, **kwargs)
        _oracle057_enrich_state()

        if isinstance(result, dict):
            result["market_regime_status"] = (
                globals().get("_state", {}).get("market_regime_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["market_regime"] = (
                globals().get("_state", {}).get("market_regime")
                if isinstance(globals().get("_state"), dict)
                else None
            )

        return result

# ============================================================
# END ORACLE-057
# ============================================================




# ============================================================
# ORACLE-058 Expected Value Engine Integration
# ============================================================

try:
    from oracle_expected_value_engine import oracle_expected_value_engine
except Exception:
    oracle_expected_value_engine = None


def _oracle058_apply_ev(ranked, market_regime=None):
    if oracle_expected_value_engine is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            ev = oracle_expected_value_engine.analyze(item, market_regime)
            item["expected_value"] = ev
            item["ev_decision"] = ev.get("ev_decision")
            item["ev_score"] = ev.get("ev_score")
            item["ev_metrics"] = ev.get("metrics", {})
            item["ev_card"] = ev.get("compact_card")
        except Exception as exc:
            item["expected_value"] = {
                "status": "error",
                "ev_decision": "NEGATIVE_EV",
                "reason": str(exc),
            }
            item["ev_decision"] = "NEGATIVE_EV"
            item["ev_score"] = 0

        enriched.append(item)

    ev_rank = {
        "POSITIVE_EV": 4,
        "WATCH_EV": 3,
        "WEAK_EV": 2,
        "NEGATIVE_EV": 1,
    }

    enriched.sort(
        key=lambda x: (
            ev_rank.get(x.get("ev_decision"), 0),
            x.get("ev_score", 0) or 0,
            x.get("queue_score", 0) or 0,
            x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0))),
        ) if isinstance(x, dict) else (0, 0, 0, 0),
        reverse=True,
    )

    return enriched


def _oracle058_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            regime = _state.get("market_regime")

            if isinstance(ranked, list):
                _state["last_ranked"] = _oracle058_apply_ev(ranked, regime)

                counts = {}
                for item in _state["last_ranked"]:
                    if isinstance(item, dict):
                        d = item.get("ev_decision", "UNKNOWN")
                        counts[d] = counts.get(d, 0) + 1

                _state["expected_value_status"] = {
                    "status": "ok" if oracle_expected_value_engine is not None else "missing",
                    "ev_counts": counts,
                    "top": _state["last_ranked"][:5],
                }
            else:
                _state["expected_value_status"] = {"status": "no_ranked_data"}
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["expected_value_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle058_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle058_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle058_original_run_cycle(*args, **kwargs)
        _oracle058_enrich_state()
        return result


if "_oracle058_original_status" not in globals() and "status" in globals():
    _oracle058_original_status = status

    def status(*args, **kwargs):
        result = _oracle058_original_status(*args, **kwargs)
        _oracle058_enrich_state()

        if isinstance(result, dict):
            result["expected_value_status"] = (
                globals().get("_state", {}).get("expected_value_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-058
# ============================================================




# ============================================================
# ORACLE-059 EV Ranked Opportunity Calibration
# ============================================================

def _oracle059_apply_ev_rank_calibration(ranked):
    if not isinstance(ranked, list):
        return ranked

    ev_rank = {
        "POSITIVE_EV": 4,
        "WATCH_EV": 3,
        "WEAK_EV": 2,
        "NEGATIVE_EV": 1,
    }

    for item in ranked:
        if not isinstance(item, dict):
            continue

        ev_decision = str(item.get("ev_decision") or "").upper()
        ev_score = float(item.get("ev_score") or 0)
        queue_decision = str(item.get("queue_decision") or "").upper()

        item["ev_queue_overlay"] = {
            "version": "ORACLE-059",
            "status": "applied",
            "ev_decision": ev_decision,
            "ev_score": ev_score,
            "queue_decision": queue_decision,
        }

        if ev_decision == "NEGATIVE_EV":
            item["oracle_final_action"] = "AVOID"
        elif ev_decision == "WEAK_EV":
            item["oracle_final_action"] = "WATCH_ONLY"
        elif ev_decision == "WATCH_EV":
            item["oracle_final_action"] = "REVIEW"
        elif ev_decision == "POSITIVE_EV":
            item["oracle_final_action"] = "PRIORITY_REVIEW"
        else:
            item["oracle_final_action"] = "UNKNOWN"

    ranked.sort(
        key=lambda x: (
            ev_rank.get(str(x.get("ev_decision") or "").upper(), 0),
            x.get("ev_score", 0) or 0,
            x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0))),
        ) if isinstance(x, dict) else (0, 0, 0),
        reverse=True,
    )

    return ranked


def _oracle059_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            if isinstance(ranked, list):
                _state["last_ranked"] = _oracle059_apply_ev_rank_calibration(ranked)

                counts = {}
                for item in _state["last_ranked"]:
                    if isinstance(item, dict):
                        action = item.get("oracle_final_action", "UNKNOWN")
                        counts[action] = counts.get(action, 0) + 1

                _state["ev_queue_overlay_status"] = {
                    "status": "ok",
                    "version": "ORACLE-059",
                    "final_action_counts": counts,
                    "top": _state["last_ranked"][:5],
                }
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["ev_queue_overlay_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle059_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle059_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle059_original_run_cycle(*args, **kwargs)
        _oracle059_enrich_state()
        return result


if "_oracle059_original_status" not in globals() and "status" in globals():
    _oracle059_original_status = status

    def status(*args, **kwargs):
        result = _oracle059_original_status(*args, **kwargs)
        _oracle059_enrich_state()

        if isinstance(result, dict):
            result["ev_queue_overlay_status"] = (
                globals().get("_state", {}).get("ev_queue_overlay_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-059
# ============================================================




# ============================================================
# ORACLE-060 Trade Readiness Report Integration
# ============================================================

try:
    from oracle_trade_readiness_report import oracle_trade_readiness_report
except Exception:
    oracle_trade_readiness_report = None


def _oracle060_apply_trade_readiness(ranked, market_regime=None):
    if oracle_trade_readiness_report is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            report = oracle_trade_readiness_report.build(item, market_regime)
            item["trade_readiness"] = report
            item["trade_readiness_verdict"] = report.get("verdict")
            item["trade_readiness_score"] = report.get("readiness_score")
            item["trade_readiness_card"] = report.get("compact_card")
        except Exception as exc:
            item["trade_readiness"] = {
                "status": "error",
                "verdict": "NOT_READY",
                "reason": str(exc),
            }
            item["trade_readiness_verdict"] = "NOT_READY"
            item["trade_readiness_score"] = 0

        enriched.append(item)

    rank = {
        "READY": 4,
        "REVIEW_READY": 3,
        "WATCH_ONLY": 2,
        "NOT_READY": 1,
    }

    enriched.sort(
        key=lambda x: (
            rank.get(x.get("trade_readiness_verdict"), 0),
            x.get("trade_readiness_score", 0) or 0,
            x.get("ev_score", 0) or 0,
        ) if isinstance(x, dict) else (0, 0, 0),
        reverse=True,
    )

    return enriched


def _oracle060_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            regime = _state.get("market_regime")

            if isinstance(ranked, list):
                _state["last_ranked"] = _oracle060_apply_trade_readiness(ranked, regime)

                counts = {}
                for item in _state["last_ranked"]:
                    if isinstance(item, dict):
                        v = item.get("trade_readiness_verdict", "UNKNOWN")
                        counts[v] = counts.get(v, 0) + 1

                _state["trade_readiness_status"] = {
                    "status": "ok" if oracle_trade_readiness_report is not None else "missing",
                    "verdict_counts": counts,
                    "top": _state["last_ranked"][:5],
                }
            else:
                _state["trade_readiness_status"] = {"status": "no_ranked_data"}
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["trade_readiness_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle060_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle060_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle060_original_run_cycle(*args, **kwargs)
        _oracle060_enrich_state()
        return result


if "_oracle060_original_status" not in globals() and "status" in globals():
    _oracle060_original_status = status

    def status(*args, **kwargs):
        result = _oracle060_original_status(*args, **kwargs)
        _oracle060_enrich_state()

        if isinstance(result, dict):
            result["trade_readiness_status"] = (
                globals().get("_state", {}).get("trade_readiness_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-060
# ============================================================




# ============================================================
# ORACLE-061 Final Decision Router Integration
# ============================================================

try:
    from oracle_final_decision_router import oracle_final_decision_router
except Exception:
    oracle_final_decision_router = None


def _oracle061_apply_final_decision(ranked, market_regime=None):
    if oracle_final_decision_router is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            fd = oracle_final_decision_router.route(item, market_regime)
            item["final_decision"] = fd
            item["oracle_final_action"] = fd.get("final_action")
            item["oracle_final_score"] = fd.get("final_score")
            item["oracle_final_card"] = fd.get("compact_card")
        except Exception as exc:
            item["final_decision"] = {
                "status": "error",
                "final_action": "NO_TRADE",
                "reason": str(exc),
            }
            item["oracle_final_action"] = "NO_TRADE"
            item["oracle_final_score"] = 0

        enriched.append(item)

    rank = {
        "READY_FOR_EXECUTION": 4,
        "HUMAN_REVIEW": 3,
        "WATCH": 2,
        "NO_TRADE": 1,
    }

    enriched.sort(
        key=lambda x: (
            rank.get(x.get("oracle_final_action"), 0),
            x.get("oracle_final_score", 0) or 0,
            x.get("trade_readiness_score", 0) or 0,
            x.get("ev_score", 0) or 0,
        ) if isinstance(x, dict) else (0, 0, 0, 0),
        reverse=True,
    )

    return enriched


def _oracle061_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            regime = _state.get("market_regime")

            if isinstance(ranked, list):
                _state["last_ranked"] = _oracle061_apply_final_decision(ranked, regime)

                counts = {}
                for item in _state["last_ranked"]:
                    if isinstance(item, dict):
                        a = item.get("oracle_final_action", "UNKNOWN")
                        counts[a] = counts.get(a, 0) + 1

                _state["final_decision_status"] = {
                    "status": "ok" if oracle_final_decision_router is not None else "missing",
                    "action_counts": counts,
                    "top": _state["last_ranked"][:5],
                }
            else:
                _state["final_decision_status"] = {"status": "no_ranked_data"}
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["final_decision_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle061_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle061_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle061_original_run_cycle(*args, **kwargs)
        _oracle061_enrich_state()
        return result


if "_oracle061_original_status" not in globals() and "status" in globals():
    _oracle061_original_status = status

    def status(*args, **kwargs):
        result = _oracle061_original_status(*args, **kwargs)
        _oracle061_enrich_state()

        if isinstance(result, dict):
            result["final_decision_status"] = (
                globals().get("_state", {}).get("final_decision_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-061
# ============================================================




# ============================================================
# ORACLE-063 Final Alert Formatter Integration
# ============================================================

try:
    from oracle_final_alert_formatter import oracle_final_alert_formatter
except Exception:
    oracle_final_alert_formatter = None


def _oracle063_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")

            if oracle_final_alert_formatter is None:
                _state["final_alert_status"] = {"status": "missing"}
                _state["final_alerts"] = []
                return

            result = oracle_final_alert_formatter.format_many(ranked if isinstance(ranked, list) else [], limit=10)
            _state["final_alert_status"] = result
            _state["final_alerts"] = result.get("alerts", [])
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["final_alert_status"] = {"status": "error", "error": str(exc)}
            _state["final_alerts"] = []


if "_oracle063_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle063_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle063_original_run_cycle(*args, **kwargs)
        _oracle063_enrich_state()
        return result


if "_oracle063_original_status" not in globals() and "status" in globals():
    _oracle063_original_status = status

    def status(*args, **kwargs):
        result = _oracle063_original_status(*args, **kwargs)
        _oracle063_enrich_state()

        if isinstance(result, dict):
            result["final_alert_status"] = (
                globals().get("_state", {}).get("final_alert_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["final_alerts"] = (
                globals().get("_state", {}).get("final_alerts")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-063
# ============================================================




# ============================================================
# ORACLE-064 Alert Outbox Manager Integration
# ============================================================

try:
    from oracle_alert_outbox_manager import oracle_alert_outbox_manager
except Exception:
    oracle_alert_outbox_manager = None


def _oracle064_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            alerts = _state.get("final_alerts", [])

            if oracle_alert_outbox_manager is None:
                _state["alert_outbox_status"] = {"status": "missing"}
                _state["alert_outbox"] = []
                return

            result = oracle_alert_outbox_manager.stage_alerts(alerts if isinstance(alerts, list) else [])
            _state["alert_outbox_status"] = result
            _state["alert_outbox"] = result.get("outbox", [])
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["alert_outbox_status"] = {"status": "error", "error": str(exc)}
            _state["alert_outbox"] = []


if "_oracle064_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle064_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle064_original_run_cycle(*args, **kwargs)
        _oracle064_enrich_state()
        return result


if "_oracle064_original_status" not in globals() and "status" in globals():
    _oracle064_original_status = status

    def status(*args, **kwargs):
        result = _oracle064_original_status(*args, **kwargs)
        _oracle064_enrich_state()

        if isinstance(result, dict):
            result["alert_outbox_status"] = (
                globals().get("_state", {}).get("alert_outbox_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["alert_outbox"] = (
                globals().get("_state", {}).get("alert_outbox")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-064
# ============================================================




# ============================================================
# ORACLE-065 Alert Delivery Bridge Integration
# ============================================================

try:
    from oracle_alert_delivery_bridge import oracle_alert_delivery_bridge
except Exception:
    oracle_alert_delivery_bridge = None


def _oracle065_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            outbox = _state.get("alert_outbox", [])

            if oracle_alert_delivery_bridge is None:
                _state["alert_delivery_status"] = {"status": "missing"}
                _state["alert_delivery_payloads"] = []
                return

            result = oracle_alert_delivery_bridge.prepare(outbox if isinstance(outbox, list) else [])
            _state["alert_delivery_status"] = result
            _state["alert_delivery_payloads"] = result.get("payloads", [])
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["alert_delivery_status"] = {"status": "error", "error": str(exc)}
            _state["alert_delivery_payloads"] = []


if "_oracle065_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle065_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle065_original_run_cycle(*args, **kwargs)
        _oracle065_enrich_state()
        return result


if "_oracle065_original_status" not in globals() and "status" in globals():
    _oracle065_original_status = status

    def status(*args, **kwargs):
        result = _oracle065_original_status(*args, **kwargs)
        _oracle065_enrich_state()

        if isinstance(result, dict):
            result["alert_delivery_status"] = (
                globals().get("_state", {}).get("alert_delivery_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["alert_delivery_payloads"] = (
                globals().get("_state", {}).get("alert_delivery_payloads")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-065
# ============================================================




# ============================================================
# ORACLE-066 Live Trade Tracker Integration
# ============================================================

try:
    from oracle_live_trade_tracker import oracle_live_trade_tracker
except Exception:
    oracle_live_trade_tracker = None


def _oracle066_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked", [])

            if oracle_live_trade_tracker is None:
                _state["live_trade_tracker_status"] = {"status": "missing"}
                _state["live_trades"] = []
                return

            result = oracle_live_trade_tracker.track(ranked if isinstance(ranked, list) else [])
            _state["live_trade_tracker_status"] = result
            _state["live_trades"] = result.get("open_trades", [])
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["live_trade_tracker_status"] = {"status": "error", "error": str(exc)}
            _state["live_trades"] = []


if "_oracle066_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle066_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle066_original_run_cycle(*args, **kwargs)
        _oracle066_enrich_state()
        return result


if "_oracle066_original_status" not in globals() and "status" in globals():
    _oracle066_original_status = status

    def status(*args, **kwargs):
        result = _oracle066_original_status(*args, **kwargs)
        _oracle066_enrich_state()

        if isinstance(result, dict):
            result["live_trade_tracker_status"] = (
                globals().get("_state", {}).get("live_trade_tracker_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["live_trades"] = (
                globals().get("_state", {}).get("live_trades")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-066
# ============================================================




# ============================================================
# ORACLE-067 Outcome Scoring Engine Integration
# ============================================================

try:
    from oracle_outcome_scoring_engine import oracle_outcome_scoring_engine
except Exception:
    oracle_outcome_scoring_engine = None


def _oracle067_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            trades = _state.get("live_trades", [])

            if oracle_outcome_scoring_engine is None:
                _state["outcome_scoring_status"] = {"status": "missing"}
                _state["outcome_scores"] = []
                return

            result = oracle_outcome_scoring_engine.score_trades(trades if isinstance(trades, list) else [])
            _state["outcome_scoring_status"] = result
            _state["outcome_scores"] = result.get("scored_trades", [])
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["outcome_scoring_status"] = {"status": "error", "error": str(exc)}
            _state["outcome_scores"] = []


if "_oracle067_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle067_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle067_original_run_cycle(*args, **kwargs)
        _oracle067_enrich_state()
        return result


if "_oracle067_original_status" not in globals() and "status" in globals():
    _oracle067_original_status = status

    def status(*args, **kwargs):
        result = _oracle067_original_status(*args, **kwargs)
        _oracle067_enrich_state()

        if isinstance(result, dict):
            result["outcome_scoring_status"] = (
                globals().get("_state", {}).get("outcome_scoring_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["outcome_scores"] = (
                globals().get("_state", {}).get("outcome_scores")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-067
# ============================================================




# ============================================================
# ORACLE-068 Signal Learning Memory Integration
# ============================================================

try:
    from oracle_signal_learning_memory import oracle_signal_learning_memory
except Exception:
    oracle_signal_learning_memory = None


def _oracle068_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked", [])
            outcomes = _state.get("outcome_scores", [])

            if oracle_signal_learning_memory is None:
                _state["signal_learning_status"] = {"status": "missing"}
                return

            result = oracle_signal_learning_memory.learn(
                ranked if isinstance(ranked, list) else [],
                outcomes if isinstance(outcomes, list) else [],
            )
            _state["signal_learning_status"] = result
            _state["signal_learning_top_patterns"] = result.get("top_patterns", [])
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["signal_learning_status"] = {"status": "error", "error": str(exc)}
            _state["signal_learning_top_patterns"] = []


if "_oracle068_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle068_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle068_original_run_cycle(*args, **kwargs)
        _oracle068_enrich_state()
        return result


if "_oracle068_original_status" not in globals() and "status" in globals():
    _oracle068_original_status = status

    def status(*args, **kwargs):
        result = _oracle068_original_status(*args, **kwargs)
        _oracle068_enrich_state()

        if isinstance(result, dict):
            result["signal_learning_status"] = (
                globals().get("_state", {}).get("signal_learning_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["signal_learning_top_patterns"] = (
                globals().get("_state", {}).get("signal_learning_top_patterns")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-068
# ============================================================




# ============================================================
# ORACLE-069 Learning Score Adapter Integration
# ============================================================

try:
    from oracle_learning_score_adapter import oracle_learning_score_adapter
except Exception:
    oracle_learning_score_adapter = None


def _oracle069_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked", [])
            patterns = _state.get("signal_learning_top_patterns", [])

            if oracle_learning_score_adapter is None:
                _state["learning_adapter_status"] = {"status": "missing"}
                return

            result = oracle_learning_score_adapter.apply(
                ranked if isinstance(ranked, list) else [],
                patterns if isinstance(patterns, list) else [],
            )
            _state["learning_adapter_status"] = result
            _state["last_ranked"] = result.get("ranked", ranked)
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["learning_adapter_status"] = {"status": "error", "error": str(exc)}


if "_oracle069_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle069_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle069_original_run_cycle(*args, **kwargs)
        _oracle069_enrich_state()
        return result


if "_oracle069_original_status" not in globals() and "status" in globals():
    _oracle069_original_status = status

    def status(*args, **kwargs):
        result = _oracle069_original_status(*args, **kwargs)
        _oracle069_enrich_state()

        if isinstance(result, dict):
            result["learning_adapter_status"] = (
                globals().get("_state", {}).get("learning_adapter_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-069
# ============================================================




# ============================================================
# ORACLE-070 Learning-Aware Final Action Integration
# ============================================================

def _oracle070_apply_learning_final_overlay(ranked):
    if not isinstance(ranked, list):
        return ranked

    action_rank = {
        "READY_FOR_EXECUTION": 4,
        "HUMAN_REVIEW": 3,
        "WATCH": 2,
        "NO_TRADE": 1,
    }

    for item in ranked:
        if not isinstance(item, dict):
            continue

        learning = item.get("learning_adapter") if isinstance(item.get("learning_adapter"), dict) else {}
        final = item.get("final_decision") if isinstance(item.get("final_decision"), dict) else {}

        item["learning_final_overlay"] = {
            "version": "ORACLE-070",
            "status": "applied",
            "learning_confidence": learning.get("learning_confidence"),
            "learning_boost": learning.get("learning_boost"),
            "learning_penalty": learning.get("learning_penalty"),
            "adjusted_score": learning.get("adjusted_score"),
            "final_action": item.get("oracle_final_action"),
        }

        # If final router already ran before learning adapter in the patch chain,
        # apply conservative post-processing here too.
        conf = str(learning.get("learning_confidence") or "NONE").upper()
        boost = float(learning.get("learning_boost") or 0)
        penalty = float(learning.get("learning_penalty") or 0)
        adjusted = float(learning.get("adjusted_score") or item.get("oracle_final_score") or 0)
        action = str(item.get("oracle_final_action") or "NO_TRADE").upper()

        if conf in ("HIGH", "MEDIUM"):
            if penalty >= 8 and action in ("READY_FOR_EXECUTION", "HUMAN_REVIEW"):
                action = "HUMAN_REVIEW" if action == "READY_FOR_EXECUTION" else "WATCH"
            elif boost >= 8 and action == "WATCH" and adjusted >= 65:
                action = "HUMAN_REVIEW"

        item["oracle_final_action"] = action
        item["oracle_final_score"] = round(adjusted, 2)

    ranked.sort(
        key=lambda x: (
            action_rank.get(str(x.get("oracle_final_action") or "").upper(), 0),
            x.get("oracle_final_score", 0) or 0,
            x.get("learning_adjusted_score", 0) or 0,
        ) if isinstance(x, dict) else (0, 0, 0),
        reverse=True,
    )

    return ranked


def _oracle070_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            if isinstance(ranked, list):
                _state["last_ranked"] = _oracle070_apply_learning_final_overlay(ranked)

                counts = {}
                for item in _state["last_ranked"]:
                    if isinstance(item, dict):
                        a = item.get("oracle_final_action", "UNKNOWN")
                        counts[a] = counts.get(a, 0) + 1

                _state["learning_final_router_status"] = {
                    "version": "ORACLE-070",
                    "status": "ok",
                    "action_counts": counts,
                    "top": _state["last_ranked"][:5],
                }
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["learning_final_router_status"] = {
                "version": "ORACLE-070",
                "status": "error",
                "error": str(exc),
            }


if "_oracle070_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle070_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle070_original_run_cycle(*args, **kwargs)
        _oracle070_enrich_state()
        return result


if "_oracle070_original_status" not in globals() and "status" in globals():
    _oracle070_original_status = status

    def status(*args, **kwargs):
        result = _oracle070_original_status(*args, **kwargs)
        _oracle070_enrich_state()

        if isinstance(result, dict):
            result["learning_final_router_status"] = (
                globals().get("_state", {}).get("learning_final_router_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-070
# ============================================================




# ============================================================
# ORACLE-077 Data Quality Upgrade Planner Integration
# ============================================================

try:
    from oracle_data_quality_planner import oracle_data_quality_planner
except Exception:
    oracle_data_quality_planner = None


def _oracle077_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked", [])
            regime = _state.get("market_regime")

            if oracle_data_quality_planner is None:
                _state["data_quality_planner_status"] = {"status": "missing"}
                return

            result = oracle_data_quality_planner.analyze(
                ranked if isinstance(ranked, list) else [],
                regime,
            )
            _state["data_quality_planner_status"] = result
            _state["data_quality_recommendations"] = result.get("recommendations", [])
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["data_quality_planner_status"] = {"status": "error", "error": str(exc)}
            _state["data_quality_recommendations"] = []


if "_oracle077_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle077_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle077_original_run_cycle(*args, **kwargs)
        _oracle077_enrich_state()
        return result


if "_oracle077_original_status" not in globals() and "status" in globals():
    _oracle077_original_status = status

    def status(*args, **kwargs):
        result = _oracle077_original_status(*args, **kwargs)
        _oracle077_enrich_state()

        if isinstance(result, dict):
            result["data_quality_planner_status"] = (
                globals().get("_state", {}).get("data_quality_planner_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["data_quality_recommendations"] = (
                globals().get("_state", {}).get("data_quality_recommendations")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-077
# ============================================================


if __name__ == "__main__":
    import json
    print(json.dumps(diagnostics(), indent=2))
    print()
    print(format_status())
