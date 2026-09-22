from __future__ import annotations

import dataclasses
import importlib
import inspect
import json
import re
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import (
    build_existing_canonical_router,
)

READ_ONLY = True
EXECUTION_AUTHORITY = False
PROBABILITY_ENABLED = False

CANONICAL_SPORTS = (
    "baseball",
    "basketball",
    "football",
    "hockey",
    "soccer",
    "tennis",
    "golf",
    "combat",
    "esports",
)

SPORT_PATTERNS = {
    "baseball": (
        r"\bmlb\b", r"\bbaseball\b", r"\binnings?\b", r"\bpitcher\b",
        r"\bhome runs?\b", r"\brbis?\b", r"\bstrikeouts?\b",
        r"\byankees\b", r"\bdodgers\b", r"\bred sox\b", r"\bcubs\b",
    ),
    "hockey": (
        r"\bnhl\b", r"\bhockey\b", r"\bpuck\b", r"\bpower play\b",
        r"\bshots on goal\b", r"\bstanley cup\b",
    ),
    "basketball": (
        r"\bnba\b", r"\bwnba\b", r"\bbasketball\b", r"\brebounds?\b",
        r"\bassists?\b", r"\bthree[- ]pointers?\b",
    ),
    "football": (
        r"\bnfl\b", r"\bamerican football\b", r"\btouchdowns?\b",
        r"\bpassing yards?\b", r"\brushing yards?\b", r"\breceptions?\b",
        r"\bsuper bowl\b",
    ),
    "soccer": (
        r"\bsoccer\b", r"\bpremier league\b", r"\bchampions league\b",
        r"\bla liga\b", r"\bserie a\b", r"\bbundesliga\b", r"\bligue 1\b",
        r"\bmls\b", r"\buefa\b", r"\bfifa\b", r"\bfc\b",
    ),
    "tennis": (
        r"\batp\b", r"\bwta\b", r"\btennis\b", r"\bwimbledon\b",
        r"\bus open\b", r"\baustralian open\b", r"\bfrench open\b",
    ),
    "combat": (
        r"\bufc\b", r"\bmma\b", r"\bboxing\b", r"\bknockout\b",
        r"\bsubmission\b", r"\bko/tko\b",
    ),
    "golf": (
        r"\bpga\b", r"\blpga\b", r"\bgolf\b", r"\bmasters\b",
    ),
    "esports": (
        r"\besports?\b", r"\bleague of legends\b", r"\bvalorant\b",
        r"\bdota\b", r"\bcounter[- ]strike\b", r"\bcs2\b",
    ),
}

def _safe_value(value: Any, depth: int = 0) -> Any:
    if depth > 7:
        return "<max-depth>"
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if dataclasses.is_dataclass(value):
        return {f.name: _safe_value(getattr(value, f.name), depth + 1)
                for f in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(k): _safe_value(v, depth + 1)
                for k, v in list(value.items())[:400]}
    if isinstance(value, (list, tuple, set)):
        return [_safe_value(v, depth + 1) for v in list(value)[:400]]
    if hasattr(value, "__dict__"):
        return {k: _safe_value(v, depth + 1)
                for k, v in vars(value).items()
                if not k.startswith("__")}
    return str(value)

def _walk(value: Any, prefix: str = ""):
    if isinstance(value, dict):
        for k, v in value.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            yield p, v
            yield from _walk(v, p)
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            p = f"{prefix}[{i}]"
            yield p, v
            yield from _walk(v, p)

def _first_text(obj: Any, names: Iterable[str]) -> str | None:
    names = tuple(n.lower() for n in names)
    norm = _safe_value(obj)
    for path, value in _walk(norm):
        tail = path.rsplit(".", 1)[-1].lower()
        tail = re.sub(r"\[\d+\]$", "", tail)
        if tail in names and isinstance(value, str) and value.strip():
            return value.strip()
    return None

def _all_text(obj: Any) -> str:
    norm = _safe_value(obj)
    vals = []
    for _, value in _walk(norm):
        if isinstance(value, str) and value.strip():
            vals.append(value.strip())
    return " | ".join(vals)

def _import_first(candidates):
    errors = []
    for module_name, symbol in candidates:
        try:
            mod = importlib.import_module(module_name)
            value = getattr(mod, symbol, None)
            if value is not None:
                return value, f"{module_name}.{symbol}"
        except Exception as exc:
            errors.append(f"{module_name}: {type(exc).__name__}: {exc}")
    raise RuntimeError("No supported repository-native symbol found: " + " ; ".join(errors))

def _load_current_market_cohort():
    fetch, fetch_path = _import_first((
        ("qseries_v2.oracle_adapters.independent.oad_082_single_immutable_live_market_cohort_snapshot",
         "fetch_single_immutable_live_market_cohort_snapshot"),
        ("qseries_v2.oracle_adapters.independent.oad_082_single_immutable_live_market_cohort_snapshot",
         "build_single_immutable_live_market_cohort_snapshot"),
        ("qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index",
         "fetch_current_open_kalshi_market_index"),
    ))

    sig = inspect.signature(fetch)
    kwargs = {}
    if "root" in sig.parameters:
        kwargs["root"] = Path.cwd()
    if "limit" in sig.parameters:
        kwargs["limit"] = 1000
    if "timeout_seconds" in sig.parameters:
        kwargs["timeout_seconds"] = 30

    result = fetch(**kwargs)
    if isinstance(result, tuple) and len(result) == 2 and not isinstance(result[0], str):
        primary = result[0]
    else:
        primary = result

    markets = None
    snapshot_id = None

    if isinstance(primary, dict):
        for key in ("markets", "market_index", "records", "items"):
            if isinstance(primary.get(key), (list, tuple)):
                markets = tuple(primary[key])
                break
        snapshot_id = primary.get("snapshot_id") or primary.get("cohort_id")
    elif isinstance(primary, (list, tuple)):
        markets = tuple(primary)
    else:
        for key in ("markets", "market_index", "records", "items"):
            value = getattr(primary, key, None)
            if isinstance(value, (list, tuple)):
                markets = tuple(value)
                break
        snapshot_id = getattr(primary, "snapshot_id", None) or getattr(primary, "cohort_id", None)

    if markets is None:
        raise RuntimeError(f"Unable to extract markets from current cohort result type {type(primary)}")

    return markets, snapshot_id, fetch_path

def _extract_market_fields(market: Any):
    ticker = _first_text(market, ("ticker", "market_ticker", "source_market_id", "symbol"))
    title = _first_text(market, ("title", "market_title", "question", "subtitle"))
    event_ticker = _first_text(market, ("event_ticker", "eventticker"))
    series_ticker = _first_text(market, ("series_ticker", "seriesticker"))
    return {
        "ticker": ticker,
        "title": title,
        "event_ticker": event_ticker,
        "series_ticker": series_ticker,
        "raw": _safe_value(market),
    }

def _classify_current_market_with_repo(market: Any):
    candidates = (
        ("qseries_v2.oracle_adapters.independent.oad_106_universal_identity_classification_physical_gate",
         "classify_market"),
        ("qseries_v2.oracle_adapters.independent.oad_106_universal_identity_classification_physical_gate",
         "classify_market_identity"),
        ("qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation",
         "classify_market"),
        ("qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation",
         "resolve_semantic_identity"),
    )
    for module_name, symbol in candidates:
        try:
            mod = importlib.import_module(module_name)
            func = getattr(mod, symbol, None)
            if not callable(func):
                continue
            sig = inspect.signature(func)
            try:
                if len(sig.parameters) == 1:
                    result = func(market)
                elif "market" in sig.parameters:
                    result = func(market=market)
                else:
                    continue
            except Exception:
                continue
            text = _all_text(result).lower()
            return result, f"{module_name}.{symbol}", text
        except Exception:
            continue
    return None, None, ""

def _looks_sports_unknown(market: Any):
    # First prefer current repo classification if an exact callable is exported.
    result, path, text = _classify_current_market_with_repo(market)
    if path:
        sports = ("sports" in text)
        unknown = ("unknown" in text or "unresolved" in text or "none" in text)
        return sports and unknown, path, _safe_value(result)

    # Structural fallback uses current production market identity only to isolate candidates;
    # it never writes or changes production classification.
    f = _extract_market_fields(market)
    identity = " | ".join(x for x in (
        f["ticker"], f["title"], f["event_ticker"], f["series_ticker"]
    ) if x).lower()

    sports_signal = bool(re.search(
        r"\b(nhl|mlb|nba|wnba|nfl|ufc|mma|atp|wta|soccer|tennis|baseball|basketball|football|hockey|golf|esports|match|game|player|team)\b",
        identity,
        re.I,
    ))
    return sports_signal, "STRUCTURAL_FALLBACK_AUDIT_ONLY", f

def _router_backend(root: Path):
    router = build_existing_canonical_router(root)
    backend = getattr(router, "_persistence_backend", None)
    if backend is None:
        raise RuntimeError("canonical PostgreSQL backend unavailable")
    if not callable(getattr(backend, "_connect", None)):
        raise RuntimeError("backend._connect() unavailable")
    return router, backend

def _read_market_snapshot_observations(backend, tickers):
    tickers = tuple(sorted({t for t in tickers if t}))
    if not tickers:
        return []

    conn = backend._connect()
    try:
        with conn.cursor() as cur:
            cur.execute("BEGIN READ ONLY")

            # Inspect only the canonical observation table schema, then use exact bounded SQL.
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='oracle_canonical_observations'
                ORDER BY ordinal_position
            """)
            columns = [r[0] for r in cur.fetchall()]

            # We already know the production table stores observations and source IDs.
            # Discover the actual serialized observation column instead of guessing.
            preferred = [
                c for c in columns
                if c.lower() in (
                    "observation_json", "canonical_observation", "observation",
                    "payload_json", "record_json", "observation_payload"
                )
            ]

            if preferred:
                value_col = preferred[0]
                # Direct bounded JSON/text identity recovery if serialized observation column exists.
                cur.execute(
                    f"""
                    SELECT {value_col}
                    FROM public.oracle_canonical_observations
                    WHERE CAST({value_col} AS text) LIKE '%%market_snapshot%%'
                      AND EXISTS (
                          SELECT 1
                          FROM unnest(%s::text[]) AS wanted(t)
                          WHERE CAST({value_col} AS text) LIKE '%%' || wanted.t || '%%'
                      )
                    LIMIT %s
                    """,
                    (list(tickers), max(5000, len(tickers) * 8)),
                )
                rows = cur.fetchall()
                conn.rollback()
                return [r[0] for r in rows]

            # If the canonical table does not expose serialized observation directly,
            # join the exact current ticker set through the learning index and fetch only
            # corresponding canonical observation IDs. This is still bounded to the exact cohort.
            cur.execute(
                """
                SELECT DISTINCT i.ticker, i.observation_id
                FROM public.oracle_production_learning_evidence_index i
                WHERE i.ticker = ANY(%s::text[])
                ORDER BY i.ticker, i.observation_id
                """,
                (list(tickers),),
            )
            pairs = cur.fetchall()
        conn.rollback()
        return [("PAIR", str(t), str(o)) for t, o in pairs]
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass

def _request_class(backend):
    for module_name in (
        backend.__class__.__module__,
        "qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract",
        "qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_backend",
    ):
        try:
            mod = importlib.import_module(module_name)
        except Exception:
            continue
        cls = getattr(mod, "CanonicalPersistenceQueryRequest", None)
        if cls is not None:
            return cls
    raise RuntimeError("CanonicalPersistenceQueryRequest unavailable")

def _request_for_observation_id(request_cls, backend, observation_id):
    method = getattr(request_cls, "by_observation_id", None)
    if not callable(method):
        raise RuntimeError("by_observation_id unavailable")
    return method(
        query_id="oad-exact-sports-unknown-" + uuid.uuid4().hex,
        backend_id=str(getattr(backend, "backend_id")),
        observation_id=str(observation_id),
        requested_at=datetime.now(timezone.utc),
        query_metadata={"audit": "exact_sports_unknown_identity_recovery", "read_only": True},
    )

def _decode_observation(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value

def _extract_snapshot_identity(observation: Any):
    norm = _safe_value(_decode_observation(observation))
    observation_type = _first_text(norm, ("observation_type",))
    market_title = None
    source_market_id = None
    event_ticker = None
    source_symbol = None

    # Canonical payload is an immutable list-of-pairs. Decode it explicitly.
    payload = norm.get("payload") if isinstance(norm, dict) else None
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, list) and len(item) == 2:
                key, value = item
                if key == "market_title" and isinstance(value, str):
                    market_title = value
                elif key == "source_market_id" and isinstance(value, str):
                    source_market_id = value
                elif key == "event_ticker" and isinstance(value, str):
                    event_ticker = value
                elif key == "source_symbol" and isinstance(value, str):
                    source_symbol = value

    return {
        "observation_type": observation_type,
        "market_title": market_title,
        "source_market_id": source_market_id,
        "event_ticker": event_ticker,
        "source_symbol": source_symbol,
        "canonical_observation": norm,
    }

def _resolve_family(identity_text: str):
    hits = []
    for family, patterns in SPORT_PATTERNS.items():
        matched = [p for p in patterns if re.search(p, identity_text, re.I)]
        if matched:
            hits.append((family, len(matched), matched))
    hits.sort(key=lambda x: (-x[1], x[0]))

    if not hits:
        return "UNKNOWN", "NO_DEFENSIBLE_FAMILY_SIGNAL", []
    if len(hits) > 1 and hits[0][1] == hits[1][1]:
        top = hits[0][1]
        tied = [x[0] for x in hits if x[1] == top]
        return "UNKNOWN", "CONFLICTING_FAMILY_SIGNALS", tied
    return hits[0][0], "MARKET_IDENTITY_SIGNAL", hits[0][2]

def run_exact_sports_unknown_cohort_postgresql_identity_recovery_audit(root=None):
    root = Path(root or Path.cwd()).resolve()

    markets, snapshot_id, cohort_source = _load_current_market_cohort()
    market_rows = [_extract_market_fields(m) for m in markets]

    unknown_candidates = []
    classifier_paths = Counter()
    for market, fields in zip(markets, market_rows):
        is_unknown, path, detail = _looks_sports_unknown(market)
        classifier_paths[path] += 1
        if is_unknown and fields["ticker"]:
            unknown_candidates.append({
                **fields,
                "isolation_path": path,
                "classification_detail": detail,
            })

    # Deduplicate by actual market ticker before touching PostgreSQL.
    dedup = {}
    for row in unknown_candidates:
        dedup.setdefault(row["ticker"], row)
    unknown_candidates = list(dedup.values())
    tickers = [r["ticker"] for r in unknown_candidates]

    _, backend = _router_backend(root)
    raw = _read_market_snapshot_observations(backend, tickers)

    restored = []
    request_cls = _request_class(backend)

    if raw and isinstance(raw[0], tuple) and raw[0] and raw[0][0] == "PAIR":
        # Exact cohort only. Restore at most one useful market_snapshot per ticker.
        by_ticker = defaultdict(list)
        for _, ticker, obs_id in raw:
            by_ticker[ticker].append(obs_id)

        for ticker in tickers:
            chosen = None
            # Cap exact queries per market to avoid the prior 10k serialized-query mistake.
            for obs_id in by_ticker.get(ticker, [])[:8]:
                req = _request_for_observation_id(request_cls, backend, obs_id)
                observations = backend.query(request=req)
                for obs in observations:
                    ident = _extract_snapshot_identity(obs)
                    if ident["observation_type"] == "market_snapshot":
                        chosen = ident
                        chosen["ticker"] = ticker
                        chosen["observation_id"] = obs_id
                        break
                if chosen is not None:
                    break
            if chosen is not None:
                restored.append(chosen)
    else:
        for value in raw:
            ident = _extract_snapshot_identity(value)
            if ident["observation_type"] == "market_snapshot":
                restored.append(ident)

    # One snapshot per ticker.
    snapshots = {}
    for rec in restored:
        ticker = rec.get("source_market_id") or rec.get("source_symbol") or rec.get("ticker")
        if ticker and ticker in dedup and ticker not in snapshots:
            snapshots[ticker] = rec

    assignments = []
    family_counts = Counter()
    reason_counts = Counter()

    for ticker, candidate in sorted(dedup.items()):
        snap = snapshots.get(ticker)
        title = (snap or {}).get("market_title") or candidate.get("title")
        event_ticker = (snap or {}).get("event_ticker") or candidate.get("event_ticker")
        identity_text = " | ".join(x for x in (
            ticker, title, event_ticker, candidate.get("series_ticker")
        ) if x)

        family, reason, evidence = _resolve_family(identity_text)
        family_counts[family] += 1
        reason_counts[reason] += 1

        assignments.append({
            "ticker": ticker,
            "market_title": title,
            "event_ticker": event_ticker,
            "series_ticker": candidate.get("series_ticker"),
            "current_family": "sports:UNKNOWN",
            "recommended_family": family,
            "reason": reason,
            "evidence": evidence,
            "postgres_market_snapshot_found": snap is not None,
            "isolation_path": candidate["isolation_path"],
        })

    report = {
        "read_only": True,
        "execution_authority": False,
        "probability_enabled": False,
        "postgres_transaction": "BEGIN READ ONLY",
        "current_market_cohort_source": cohort_source,
        "snapshot_id": snapshot_id,
        "current_market_count": len(markets),
        "sports_unknown_candidate_count": len(unknown_candidates),
        "unique_sports_unknown_tickers": len(tickers),
        "postgres_market_snapshots_recovered": len(snapshots),
        "classifier_isolation_paths": dict(classifier_paths),
        "family_counts": dict(family_counts.most_common()),
        "reason_counts": dict(reason_counts.most_common()),
        "assignments": assignments,
    }

    report_path = root / "OAD_EXACT_SPORTS_UNKNOWN_COHORT_POSTGRESQL_IDENTITY_RECOVERY_AUDIT.json"
    unknown_path = root / "OAD_EXACT_SPORTS_UNKNOWN_COHORT_STILL_UNKNOWN.json"

    report_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    still_unknown = [r for r in assignments if r["recommended_family"] == "UNKNOWN"]
    unknown_path.write_text(json.dumps(still_unknown, indent=2, sort_keys=True, default=str), encoding="utf-8")

    return report, report_path, unknown_path
