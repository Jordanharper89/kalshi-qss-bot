from __future__ import annotations

import dataclasses
import importlib
import inspect
import json
import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import (
    build_existing_canonical_router,
)

READ_ONLY = True
EXECUTION_AUTHORITY = False
PROBABILITY_ENABLED = False

SPORT_PATTERNS = {
    "baseball": (
        r"\bmlb\b", r"\bbaseball\b", r"\binnings?\b", r"\bhome runs?\b",
        r"\brbis?\b", r"\bpitcher\b", r"\bstrikeouts?\b",
    ),
    "hockey": (
        r"\bnhl\b", r"\bhockey\b", r"\bpuck\b", r"\bpower play\b",
        r"\bshots on goal\b",
    ),
    "basketball": (
        r"\bnba\b", r"\bwnba\b", r"\bbasketball\b", r"\brebounds?\b",
        r"\bassists?\b", r"\bthree[- ]pointers?\b",
    ),
    "football": (
        r"\bnfl\b", r"\bamerican football\b", r"\btouchdowns?\b",
        r"\bpassing yards?\b", r"\brushing yards?\b", r"\breceptions?\b",
    ),
    "soccer": (
        r"\bsoccer\b", r"\bpremier league\b", r"\bchampions league\b",
        r"\bla liga\b", r"\bserie a\b", r"\bbundesliga\b", r"\bligue 1\b",
        r"\bmls\b", r"\buefa\b", r"\bfifa\b",
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
        r"\besports?\b", r"\bleague of legends\b",
        r"\bcounter[- ]strike\b", r"\bvalorant\b", r"\bdota\b",
    ),
}

def _router_backend(root: Path):
    router = build_existing_canonical_router(root)
    backend = getattr(router, "_persistence_backend", None)
    if backend is None:
        raise RuntimeError("existing canonical PostgreSQL backend unavailable")
    if not callable(getattr(backend, "_connect", None)):
        raise RuntimeError("audited backend._connect() unavailable")
    if not callable(getattr(backend, "query", None)):
        raise RuntimeError("certified backend.query() unavailable")
    return router, backend

def _safe_value(value: Any, depth: int = 0) -> Any:
    if depth > 6:
        return "<max-depth>"
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if dataclasses.is_dataclass(value):
        return {
            f.name: _safe_value(getattr(value, f.name), depth + 1)
            for f in dataclasses.fields(value)
        }
    if isinstance(value, dict):
        return {
            str(k): _safe_value(v, depth + 1)
            for k, v in list(value.items())[:300]
        }
    if isinstance(value, (list, tuple, set)):
        return [_safe_value(v, depth + 1) for v in list(value)[:300]]
    if hasattr(value, "__dict__"):
        return {
            k: _safe_value(v, depth + 1)
            for k, v in vars(value).items()
            if not k.startswith("__")
        }
    return str(value)

def _flatten_strings(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    out = []
    if value is None:
        return out
    if isinstance(value, str):
        if value.strip():
            out.append((prefix, value))
        return out
    if isinstance(value, (int, float, bool)):
        out.append((prefix, str(value)))
        return out
    if isinstance(value, dict):
        for k, v in value.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            out.extend(_flatten_strings(v, p))
        return out
    if isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            out.extend(_flatten_strings(v, f"{prefix}[{i}]"))
        return out
    return _flatten_strings(_safe_value(value), prefix)

def _request_class(backend):
    for module_name in (
        backend.__class__.__module__,
        "qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_backend",
        "qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router",
    ):
        try:
            mod = importlib.import_module(module_name)
        except Exception:
            continue
        cls = getattr(mod, "CanonicalPersistenceQueryRequest", None)
        if cls is not None:
            return cls
    raise RuntimeError("CanonicalPersistenceQueryRequest class not found")

def _query_metadata_value(parameter):
    annotation = parameter.annotation
    text = str(annotation)
    # Prefer immutable empty tuple for tuple-style metadata contracts.
    if "tuple" in text.lower():
        return ()
    # Mapping/dict contracts accept empty mapping.
    if "mapping" in text.lower() or "dict" in text.lower():
        return {}
    # Default repository convention in persistence requests is metadata mapping.
    return {}

def _request_for_observation_id(request_cls, backend, observation_id: str):
    method = getattr(request_cls, "by_observation_id", None)
    if not callable(method):
        raise RuntimeError("CanonicalPersistenceQueryRequest.by_observation_id unavailable")

    sig = inspect.signature(method)
    params = sig.parameters

    required = ("query_id", "backend_id", "requested_at", "query_metadata", "observation_id")
    missing = [name for name in required if name not in params]
    if missing:
        raise RuntimeError(
            "Unexpected by_observation_id contract; missing parameters: "
            + ", ".join(missing)
        )

    kwargs = {
        "query_id": "oad-postgresql-identity-recovery-" + uuid.uuid4().hex,
        "backend_id": str(getattr(backend, "backend_id")),
        "requested_at": datetime.now(timezone.utc),
        "query_metadata": _query_metadata_value(params["query_metadata"]),
        "observation_id": observation_id,
    }

    return method(**kwargs), kwargs, str(sig)

def _read_linkage_rows(backend, limit: int):
    conn = backend._connect()
    if conn is None:
        raise RuntimeError("backend._connect() returned None")
    try:
        with conn.cursor() as cur:
            cur.execute("BEGIN READ ONLY")
            cur.execute(
                """
                SELECT ticker, observation_id
                FROM public.oracle_production_learning_evidence_index
                WHERE ticker IS NOT NULL
                  AND observation_id IS NOT NULL
                ORDER BY ticker, observation_id
                LIMIT %s
                """,
                (int(limit),),
            )
            rows = cur.fetchall()
        conn.rollback()
        return tuple((str(t), str(o)) for t, o in rows)
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass

def _classify_family(text: str):
    hits = []
    for family, patterns in SPORT_PATTERNS.items():
        matched = [p for p in patterns if re.search(p, text, re.I)]
        if matched:
            hits.append((family, len(matched), matched))
    hits.sort(key=lambda x: (-x[1], x[0]))
    if not hits:
        return "UNKNOWN", "NO_EXPLICIT_FAMILY_SIGNAL", []
    if len(hits) > 1 and hits[0][1] == hits[1][1]:
        n = hits[0][1]
        tied = [x[0] for x in hits if x[1] == n]
        return "UNKNOWN", "CONFLICTING_FAMILY_SIGNAL:" + ",".join(tied), tied
    return hits[0][0], "CANONICAL_OBSERVATION_SIGNAL", hits[0][2]

def run_canonical_observation_identity_recovery_audit(
    root=None,
    linkage_limit: int = 25000,
    max_unique_observations: int = 10000,
):
    root = Path(root or Path.cwd()).resolve()
    _, backend = _router_backend(root)
    request_cls = _request_class(backend)

    by_id = getattr(request_cls, "by_observation_id")
    constructor_signature = str(inspect.signature(by_id))

    linkage = _read_linkage_rows(backend, linkage_limit)

    unique = []
    seen = set()
    for ticker, observation_id in linkage:
        if observation_id in seen:
            continue
        seen.add(observation_id)
        unique.append((ticker, observation_id))
        if len(unique) >= int(max_unique_observations):
            break

    family_counts = Counter()
    reason_counts = Counter()
    field_paths = Counter()
    restored = []
    unresolved = []
    missing = []
    first_request_contract = None

    for ticker, observation_id in unique:
        request, request_kwargs, request_signature = _request_for_observation_id(
            request_cls, backend, observation_id
        )
        if first_request_contract is None:
            first_request_contract = {
                "signature": request_signature,
                "query_id": request_kwargs["query_id"],
                "backend_id": request_kwargs["backend_id"],
                "requested_at": request_kwargs["requested_at"].isoformat(),
                "query_metadata_type": type(request_kwargs["query_metadata"]).__name__,
                "observation_id": request_kwargs["observation_id"],
            }

        observations = backend.query(request=request)

        if not observations:
            missing.append({
                "ticker": ticker,
                "observation_id": observation_id,
            })
            continue

        for obs in observations:
            normalized = _safe_value(obs)
            strings = _flatten_strings(normalized)
            for path, _ in strings:
                field_paths[path] += 1

            identity_text = " | ".join(
                [ticker, observation_id] + [text for _, text in strings]
            )
            family, reason, signals = _classify_family(identity_text)
            family_counts[family] += 1
            reason_counts[reason] += 1

            rec = {
                "ticker": ticker,
                "observation_id": observation_id,
                "family": family,
                "reason": reason,
                "signals": signals,
                "canonical_observation_type": (
                    f"{type(obs).__module__}.{type(obs).__name__}"
                ),
                "canonical_observation": normalized,
            }
            restored.append(rec)
            if family == "UNKNOWN":
                unresolved.append(rec)

    report = {
        "read_only": True,
        "execution_authority": False,
        "probability_enabled": False,
        "postgres_transaction": "BEGIN READ ONLY",
        "canonical_query_surface": "backend.query(request=CanonicalPersistenceQueryRequest)",
        "request_class": f"{request_cls.__module__}.{request_cls.__name__}",
        "by_observation_id_signature": constructor_signature,
        "first_request_contract": first_request_contract,
        "linkage_rows_read": len(linkage),
        "unique_observations_attempted": len(unique),
        "restored_observation_count": len(restored),
        "missing_observation_count": len(missing),
        "family_counts": dict(family_counts.most_common()),
        "reason_counts": dict(reason_counts.most_common()),
        "observed_field_paths": dict(field_paths.most_common(250)),
        "restored": restored,
        "unresolved": unresolved,
        "missing": missing,
    }

    report_path = root / "OAD_POSTGRESQL_CANONICAL_OBSERVATION_IDENTITY_RECOVERY_AUDIT.json"
    unknown_path = root / "OAD_POSTGRESQL_CANONICAL_OBSERVATION_STILL_UNKNOWN.json"

    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    unknown_path.write_text(
        json.dumps(unresolved, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )

    return report, report_path, unknown_path
