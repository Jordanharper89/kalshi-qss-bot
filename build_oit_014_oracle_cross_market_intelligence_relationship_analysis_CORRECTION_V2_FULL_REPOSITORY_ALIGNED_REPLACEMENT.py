from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        production = (
            candidate
            / "qseries_v2"
            / "oracle_terminal"
            / "oracle_cross_market_intelligence_relationship_analysis.py"
        )
        if production.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current OIT-014 repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_013 = PACKAGE / "oracle_temporal_intelligence_timeline_reconstruction.py"
PRODUCTION = PACKAGE / "oracle_cross_market_intelligence_relationship_analysis.py"
TEST = ROOT / "test_oit_014_oracle_cross_market_intelligence_relationship_analysis.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping, Sequence\n\nfrom .oracle_temporal_intelligence_timeline_reconstruction import (\n    OracleTemporalEvidenceEvent,\n    OracleTemporalTimelineInvariantError,\n    build_temporal_intelligence_report,\n    verify_temporal_intelligence_report,\n)\n\nSCHEMA_VERSION = "OIT-014"\nENGINE_ID = "OIT-014"\nPOLICY_ID = "oracle.cross-market-intelligence-relationship-analysis.v2"\nIDENTITY_FIELDS = ("record_id", "market_id", "id", "prediction_id", "event_id", "contract_id")\nENTITY_FIELDS = ("entity", "entities", "subject", "subjects", "company", "companies", "asset", "assets", "team", "teams", "candidate", "candidates", "person", "people", "organization", "organizations", "ticker", "symbol", "league")\nPROBABILITY_FIELDS = ("probability", "probability_yes", "yes_probability", "forecast_probability", "confidence", "score")\nDIRECTION_FIELDS = ("stance", "direction", "signal", "side", "outlook", "bias")\nTITLE_FIELDS = ("title", "name", "question", "market", "description")\nLEAD_LAG_WINDOW_SECONDS = 604800\nMAX_DEPTH = 12\nMAX_ITEMS = 512\n\n\nclass OracleCrossMarketRelationshipInvariantError(OracleTemporalTimelineInvariantError):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleCrossMarketRecordProfile:\n    profile_index: int\n    evidence_index: int\n    record_id: str\n    title: str\n    entities: tuple[str, ...]\n    venue: str | None\n    category: str | None\n    probability: float | None\n    direction: str | None\n    timestamp_utc: str\n    epoch_seconds: int\n    artifact_relative_path: str\n    artifact_sha256: str\n    record_hash: str\n    evidence_hash: str\n    inspection_hash: str\n    temporal_event_hash: str\n    source_record_locator: str\n    read_only: bool\n    profile_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleCrossMarketRelationship:\n    relationship_index: int\n    left_profile_index: int\n    right_profile_index: int\n    left_record_id: str\n    right_record_id: str\n    shared_entities: tuple[str, ...]\n    shared_entity_count: int\n    elapsed_seconds: int\n    temporal_relationship: str\n    directional_relationship: str\n    probability_distance: float | None\n    evidence_dependence: str\n    relationship_score: float\n    relationship_strength: str\n    rationale: tuple[str, ...]\n    read_only: bool\n    relationship_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleCrossMarketIntelligenceReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    answer_hash: str\n    query_plan_hash: str\n    query_result_hash: str\n    temporal_report_hash: str\n    profiles: tuple[OracleCrossMarketRecordProfile, ...]\n    relationships: tuple[OracleCrossMarketRelationship, ...]\n    profile_count: int\n    relationship_count: int\n    connected_profile_count: int\n    independent_profile_count: int\n    strong_relationship_count: int\n    moderate_relationship_count: int\n    weak_relationship_count: int\n    lead_lag_relationship_count: int\n    contradictory_direction_count: int\n    relationship_state: str\n    relationship_summary: str\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}\n    if isinstance(value, (list, tuple)):\n        return [_canonical(v) for v in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    return hashlib.sha256(json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()\n\n\ndef _norm(value: Any) -> str:\n    return " ".join(str(value).strip().lower().split())\n\n\ndef _display(value: Any) -> str:\n    return " ".join(str(value).strip().split())\n\n\ndef _matches(record: Mapping[str, Any], record_id: str) -> bool:\n    return any(field in record and str(record[field]).strip() == str(record_id).strip() for field in IDENTITY_FIELDS)\n\n\ndef _find_record(value: Any, record_id: str, path: str = "$", depth: int = 0):\n    if depth >= MAX_DEPTH:\n        return None\n    if isinstance(value, Mapping):\n        if _matches(value, record_id):\n            return value, path\n        for key, child in sorted(value.items(), key=lambda x: str(x[0])):\n            if isinstance(child, (Mapping, list, tuple)):\n                found = _find_record(child, record_id, f"{path}.{key}", depth + 1)\n                if found is not None:\n                    return found\n    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):\n        for index, child in enumerate(value[:MAX_ITEMS]):\n            if isinstance(child, (Mapping, list, tuple)):\n                found = _find_record(child, record_id, f"{path}[{index}]", depth + 1)\n                if found is not None:\n                    return found\n    return None\n\n\ndef _load_record(root: Path, event: OracleTemporalEvidenceEvent):\n    relative = Path(event.artifact_relative_path)\n    if relative.is_absolute():\n        raise OracleCrossMarketRelationshipInvariantError("absolute artifact path forbidden")\n    artifact = (root / relative).resolve()\n    try:\n        artifact.relative_to(root)\n    except ValueError as exc:\n        raise OracleCrossMarketRelationshipInvariantError("artifact path escapes repository") from exc\n    raw = artifact.read_bytes()\n    if hashlib.sha256(raw).hexdigest() != event.artifact_sha256:\n        raise OracleCrossMarketRelationshipInvariantError("certified artifact hash mismatch")\n    try:\n        payload = json.loads(raw.decode("utf-8"))\n    except (UnicodeDecodeError, json.JSONDecodeError) as exc:\n        raise OracleCrossMarketRelationshipInvariantError("certified artifact is not JSON") from exc\n    located = _find_record(payload, event.record_id)\n    if located is None:\n        raise OracleCrossMarketRelationshipInvariantError(f"certified record missing: {event.record_id}")\n    return located\n\n\ndef _scalars(value: Any) -> tuple[str, ...]:\n    output = []\n    def visit(item: Any, depth: int = 0):\n        if depth >= 4 or len(output) >= 64:\n            return\n        if isinstance(item, Mapping):\n            for child in item.values():\n                visit(child, depth + 1)\n        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):\n            for child in item:\n                visit(child, depth + 1)\n        elif item is not None and not isinstance(item, bool):\n            text = _display(item)\n            if text:\n                output.append(text)\n    visit(value)\n    return tuple(output)\n\n\ndef _entities(record: Mapping[str, Any]) -> tuple[str, ...]:\n    found = {}\n    for field in ENTITY_FIELDS + ("tags", "keywords", "labels"):\n        if field in record:\n            for value in _scalars(record[field]):\n                found.setdefault(_norm(value), value)\n    return tuple(found[key] for key in sorted(found))\n\n\ndef _first(record: Mapping[str, Any], fields: tuple[str, ...]) -> str | None:\n    for field in fields:\n        if field in record and record[field] is not None:\n            text = _display(record[field])\n            if text:\n                return text\n    return None\n\n\ndef _probability(record: Mapping[str, Any]) -> float | None:\n    for field in PROBABILITY_FIELDS:\n        if field not in record or isinstance(record[field], bool):\n            continue\n        try:\n            value = float(record[field])\n        except (TypeError, ValueError):\n            continue\n        if value > 1.0 and value <= 100.0:\n            value /= 100.0\n        if 0.0 <= value <= 1.0:\n            return round(value, 12)\n    return None\n\n\ndef _direction(value: str | None) -> str | None:\n    if value is None:\n        return None\n    text = _norm(value)\n    if text in {"bull", "bullish", "yes", "long", "up", "positive", "buy"}:\n        return "positive"\n    if text in {"bear", "bearish", "no", "short", "down", "negative", "sell"}:\n        return "negative"\n    if text in {"neutral", "mixed", "hold", "uncertain", "none"}:\n        return "neutral"\n    return text or None\n\n\ndef _profile(root: Path, event: OracleTemporalEvidenceEvent, index: int):\n    record, locator = _load_record(root, event)\n    body = {\n        "profile_index": index,\n        "evidence_index": event.evidence_index,\n        "record_id": event.record_id,\n        "title": _first(record, TITLE_FIELDS) or event.record_id,\n        "entities": _entities(record),\n        "venue": _first(record, ("venue", "exchange", "platform")),\n        "category": _first(record, ("category", "topic", "sector")),\n        "probability": _probability(record),\n        "direction": _direction(_first(record, DIRECTION_FIELDS)),\n        "timestamp_utc": event.timestamp_utc,\n        "epoch_seconds": event.epoch_seconds,\n        "artifact_relative_path": event.artifact_relative_path,\n        "artifact_sha256": event.artifact_sha256,\n        "record_hash": event.record_hash,\n        "evidence_hash": event.evidence_hash,\n        "inspection_hash": event.inspection_hash,\n        "temporal_event_hash": event.event_hash,\n        "source_record_locator": locator,\n        "read_only": True,\n    }\n    profile = OracleCrossMarketRecordProfile(**body, profile_hash=_stable_hash(body))\n    verify_cross_market_record_profile(profile)\n    return profile\n\n\ndef verify_cross_market_record_profile(profile: OracleCrossMarketRecordProfile) -> bool:\n    body = asdict(profile)\n    supplied = body.pop("profile_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleCrossMarketRelationshipInvariantError("profile hash mismatch")\n    if not profile.read_only or profile.profile_index < 1:\n        raise OracleCrossMarketRelationshipInvariantError("invalid profile")\n    if len(profile.artifact_sha256) != 64:\n        raise OracleCrossMarketRelationshipInvariantError(\n            "profile artifact hash is incomplete"\n        )\n    if not (\n        profile.record_hash\n        and profile.evidence_hash\n        and profile.inspection_hash\n        and profile.temporal_event_hash\n        and profile.source_record_locator\n    ):\n        raise OracleCrossMarketRelationshipInvariantError(\n            "profile lineage is incomplete"\n        )\n    normalized_entities = tuple(_norm(value) for value in profile.entities)\n    if len(normalized_entities) != len(set(normalized_entities)):\n        raise OracleCrossMarketRelationshipInvariantError(\n            "profile contains duplicate normalized entities"\n        )\n    return True\n\n\ndef _relationship(left, right, index):\n    left_map = {_norm(v): v for v in left.entities}\n    right_map = {_norm(v): v for v in right.entities}\n    keys = sorted(set(left_map) & set(right_map))\n    same_category = bool(\n        left.category\n        and right.category\n        and _norm(left.category) == _norm(right.category)\n    )\n    same_venue = bool(\n        left.venue\n        and right.venue\n        and _norm(left.venue) == _norm(right.venue)\n    )\n\n    # A venue match alone is operational context, not evidence that two\n    # markets concern the same underlying subject. Category may support an\n    # existing semantic link but cannot create one by itself.\n    if not keys:\n        return None\n    shared = tuple(left_map[key] for key in keys)\n    elapsed = right.epoch_seconds - left.epoch_seconds\n    if elapsed == 0:\n        temporal = "simultaneous"\n    elif abs(elapsed) <= LEAD_LAG_WINDOW_SECONDS:\n        temporal = "left_leads_right" if elapsed > 0 else "right_leads_left"\n    else:\n        temporal = "temporally_distant"\n    if left.direction is None or right.direction is None:\n        directional = "unknown"\n    elif left.direction == right.direction:\n        directional = "aligned"\n    elif {left.direction, right.direction} == {"positive", "negative"}:\n        directional = "contradictory"\n    elif "neutral" in {left.direction, right.direction}:\n        directional = "neutral_or_mixed"\n    else:\n        directional = "different"\n    distance = round(abs(left.probability - right.probability), 12) if left.probability is not None and right.probability is not None else None\n    score = min(\n        1.0,\n        len(shared) * 0.25\n        + (0.15 if directional in {"aligned", "contradictory"} else 0.05)\n        + (0.15 if temporal != "temporally_distant" else 0.0)\n        + (\n            0.15 * (1.0 - distance)\n            if distance is not None\n            else 0.0\n        )\n        + (0.08 if same_category else 0.0)\n        + (0.02 if same_venue else 0.0),\n    )\n    score = round(score, 6)\n    strength = "strong" if score >= 0.72 else "moderate" if score >= 0.45 else "weak"\n    rationale = []\n    if shared:\n        rationale.append("shared entities: " + ", ".join(shared))\n    if same_category:\n        rationale.append("same category")\n    if same_venue:\n        rationale.append("same venue context")\n    rationale.append(f"temporal relationship: {temporal}")\n    rationale.append(f"directional relationship: {directional}")\n    if distance is not None:\n        rationale.append(f"probability distance: {distance:.6f}")\n    body = {\n        "relationship_index": index,\n        "left_profile_index": left.profile_index,\n        "right_profile_index": right.profile_index,\n        "left_record_id": left.record_id,\n        "right_record_id": right.record_id,\n        "shared_entities": shared,\n        "shared_entity_count": len(shared),\n        "elapsed_seconds": elapsed,\n        "temporal_relationship": temporal,\n        "directional_relationship": directional,\n        "probability_distance": distance,\n        "evidence_dependence": "potentially_dependent",\n        "relationship_score": score,\n        "relationship_strength": strength,\n        "rationale": tuple(rationale),\n        "read_only": True,\n    }\n    relationship = OracleCrossMarketRelationship(**body, relationship_hash=_stable_hash(body))\n    verify_cross_market_relationship(relationship)\n    return relationship\n\n\ndef verify_cross_market_relationship(relationship: OracleCrossMarketRelationship) -> bool:\n    body = asdict(relationship)\n    supplied = body.pop("relationship_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleCrossMarketRelationshipInvariantError("relationship hash mismatch")\n    if not relationship.read_only or relationship.left_profile_index >= relationship.right_profile_index:\n        raise OracleCrossMarketRelationshipInvariantError("invalid relationship")\n    if relationship.shared_entity_count != len(relationship.shared_entities):\n        raise OracleCrossMarketRelationshipInvariantError("shared entity count mismatch")\n    return True\n\n\ndef build_cross_market_intelligence_report(*, repository_root: Path, query: str, result_limit: int = 10):\n    root = repository_root.resolve()\n    temporal = build_temporal_intelligence_report(repository_root=root, query=query, result_limit=result_limit)\n    verify_temporal_intelligence_report(temporal)\n    profiles = tuple(_profile(root, event, index) for index, event in enumerate(temporal.events, start=1))\n    relationships_list = []\n    for left_index in range(len(profiles)):\n        for right_index in range(left_index + 1, len(profiles)):\n            item = _relationship(profiles[left_index], profiles[right_index], len(relationships_list) + 1)\n            if item is not None:\n                relationships_list.append(item)\n    relationships = tuple(relationships_list)\n    connected = {index for item in relationships for index in (item.left_profile_index, item.right_profile_index)}\n    strong = sum(item.relationship_strength == "strong" for item in relationships)\n    moderate = sum(item.relationship_strength == "moderate" for item in relationships)\n    weak = sum(item.relationship_strength == "weak" for item in relationships)\n    lead_lag = sum(item.temporal_relationship in {"left_leads_right", "right_leads_left"} for item in relationships)\n    contradictions = sum(item.directional_relationship == "contradictory" for item in relationships)\n    if not profiles:\n        state = "no_cross_market_evidence"\n        summary = "Oracle found no timestamped records to compare."\n    elif not relationships:\n        state = "independent_market_evidence"\n        summary = f"Oracle profiled {len(profiles)} record(s) without a shared relationship."\n    elif strong:\n        state = "strong_cross_market_relationships"\n        summary = f"Oracle found {len(relationships)} relationship(s), including {strong} strong relationship(s)."\n    else:\n        state = "cross_market_relationships_detected"\n        summary = f"Oracle found {len(relationships)} relationship(s) across {len(connected)} profile(s)."\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "cross_market_relationships_analyzed" if profiles else "cross_market_analysis_limited",\n        "repository_root": root.as_posix(),\n        "query": temporal.query,\n        "answer_hash": temporal.answer_hash,\n        "query_plan_hash": temporal.query_plan_hash,\n        "query_result_hash": temporal.query_result_hash,\n        "temporal_report_hash": temporal.report_hash,\n        "profiles": profiles,\n        "relationships": relationships,\n        "profile_count": len(profiles),\n        "relationship_count": len(relationships),\n        "connected_profile_count": len(connected),\n        "independent_profile_count": len(profiles) - len(connected),\n        "strong_relationship_count": strong,\n        "moderate_relationship_count": moderate,\n        "weak_relationship_count": weak,\n        "lead_lag_relationship_count": lead_lag,\n        "contradictory_direction_count": contradictions,\n        "relationship_state": state,\n        "relationship_summary": summary,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": temporal.failure_reason,\n    }\n    report = OracleCrossMarketIntelligenceReport(**body, report_hash=_stable_hash(body))\n    verify_cross_market_intelligence_report(report)\n    return report\n\n\ndef verify_cross_market_intelligence_report(report: OracleCrossMarketIntelligenceReport) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleCrossMarketRelationshipInvariantError("OIT-014 report hash mismatch")\n    for profile in report.profiles:\n        verify_cross_market_record_profile(profile)\n    for relationship in report.relationships:\n        verify_cross_market_relationship(relationship)\n    if report.profile_count != len(report.profiles) or report.relationship_count != len(report.relationships):\n        raise OracleCrossMarketRelationshipInvariantError("report count mismatch")\n    if report.connected_profile_count + report.independent_profile_count != report.profile_count:\n        raise OracleCrossMarketRelationshipInvariantError("connectivity accounting mismatch")\n    if not report.read_only or report.analytics_execution_performed or report.database_access_performed or report.publication_allowed or report.qseries_execution_allowed:\n        raise OracleCrossMarketRelationshipInvariantError("unsafe OIT-014 boundary")\n    return True\n\n\ndef cross_market_intelligence_lines(report: OracleCrossMarketIntelligenceReport) -> tuple[str, ...]:\n    verify_cross_market_intelligence_report(report)\n    lines = [\n        "ORACLE CROSS-MARKET INTELLIGENCE",\n        f"query: {report.query}",\n        f"relationship_state: {report.relationship_state}",\n        f"profile_count: {report.profile_count}",\n        f"relationship_count: {report.relationship_count}",\n        f"connected_profile_count: {report.connected_profile_count}",\n        f"independent_profile_count: {report.independent_profile_count}",\n        f"strong_relationship_count: {report.strong_relationship_count}",\n        f"lead_lag_relationship_count: {report.lead_lag_relationship_count}",\n        f"contradictory_direction_count: {report.contradictory_direction_count}",\n        f"summary: {report.relationship_summary}",\n    ]\n    for profile in report.profiles:\n        lines.extend((f"[P{profile.profile_index}] {profile.record_id}", f"    title: {profile.title}", f"    entities: {\', \'.join(profile.entities) or \'none\'}", f"    timestamp_utc: {profile.timestamp_utc}", f"    direction: {profile.direction or \'unknown\'}", f"    probability: {profile.probability if profile.probability is not None else \'unknown\'}"))\n    if not report.relationships:\n        lines.append("relationships: none")\n    for item in report.relationships:\n        lines.extend((f"[R{item.relationship_index}] {item.left_record_id} <-> {item.right_record_id}", f"    shared_entities: {\', \'.join(item.shared_entities) or \'none\'}", f"    temporal_relationship: {item.temporal_relationship}", f"    directional_relationship: {item.directional_relationship}", f"    relationship_score: {item.relationship_score:.6f}", f"    relationship_strength: {item.relationship_strength}", f"    relationship_hash: {item.relationship_hash}"))\n    lines.extend((f"temporal_report_hash: {report.temporal_report_hash}", f"report_hash: {report.report_hash}", "analytics_execution_performed: false", "database_access_performed: false", "publication_allowed: false", "qseries_execution_allowed: false", "read_only: true"))\n    return tuple(lines)\n'
TEST_SOURCE = '\nimport hashlib\nimport json\nimport os\nimport sys\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\n\ndef clear_modules():\n    for name in list(sys.modules):\n        if name == "qseries_v2" or name.startswith("qseries_v2."):\n            del sys.modules[name]\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" OIT-014 CORRECTION V2 TEST")\n    print(" REPOSITORY-ALIGNED RELATIONSHIP SEMANTICS")\n    print("=" * 40)\n    installed_root = Path(__file__).resolve().parent\n    source = installed_root / "qseries_v2" / "oracle_terminal" / "oracle_cross_market_intelligence_relationship_analysis.py"\n    assert source.is_file()\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        terminal = root / "qseries_v2" / "oracle_terminal"\n        terminal.mkdir(parents=True)\n        (root / "qseries_v2" / "__init__.py").write_text("", encoding="utf-8")\n        (terminal / "__init__.py").write_text("", encoding="utf-8")\n        (terminal / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")\n\n        artifact = root / "runtime" / "oracle_intelligence" / "markets.json"\n        artifact.parent.mkdir(parents=True)\n        payload = {"records": [\n            {"market_id": "BTC-ETF", "title": "Bitcoin ETF approval", "asset": "Bitcoin", "category": "Crypto", "venue": "Kalshi", "probability": 0.72, "stance": "bull", "updated_at": "2026-07-29T12:00:00Z"},\n            {"market_id": "BTC-PRICE", "title": "Bitcoin above target", "asset": "Bitcoin", "category": "Crypto", "venue": "Polymarket", "probability": 0.61, "stance": "bear", "updated_at": "2026-07-30T12:00:00Z"},\n            {"market_id": "NFL-GAME", "title": "Independent football market", "team": "Chicago Bears", "category": "Sports", "venue": "Kalshi", "probability": 0.53, "stance": "neutral", "updated_at": "2026-07-30T13:00:00Z"}\n        ]}\n        artifact.write_text(json.dumps(payload, sort_keys=True) + "\\n", encoding="utf-8")\n        artifact_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()\n        relative = artifact.relative_to(root).as_posix()\n\n        stub = """\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nclass OracleTemporalTimelineInvariantError(RuntimeError):\n    pass\n\n@dataclass(frozen=True)\nclass OracleTemporalEvidenceEvent:\n    event_index: int\n    evidence_index: int\n    record_id: str\n    timestamp_utc: str\n    epoch_seconds: int\n    artifact_relative_path: str\n    artifact_sha256: str\n    record_hash: str\n    evidence_hash: str\n    inspection_hash: str\n    event_hash: str\n\n@dataclass(frozen=True)\nclass OracleTemporalIntelligenceReport:\n    query: str\n    answer_hash: str\n    query_plan_hash: str\n    query_result_hash: str\n    report_hash: str\n    events: tuple\n    failure_reason: str | None = None\n\ndef verify_temporal_intelligence_report(report):\n    return bool(report.report_hash)\n\ndef build_temporal_intelligence_report(*, repository_root: Path, query: str, result_limit: int = 10):\n    items = (\n        ("BTC-ETF", "2026-07-29T12:00:00+00:00", 1785326400),\n        ("BTC-PRICE", "2026-07-30T12:00:00+00:00", 1785412800),\n        ("NFL-GAME", "2026-07-30T13:00:00+00:00", 1785416400),\n    )\n    events = tuple(\n        OracleTemporalEvidenceEvent(\n            event_index=index,\n            evidence_index=index,\n            record_id=record_id,\n            timestamp_utc=timestamp,\n            epoch_seconds=epoch,\n            artifact_relative_path=__RELATIVE__,\n            artifact_sha256=__HASH__,\n            record_hash=("r" + str(index)) * 32,\n            evidence_hash=("e" + str(index)) * 32,\n            inspection_hash=("i" + str(index)) * 32,\n            event_hash=("t" + str(index)) * 32,\n        )\n        for index, (record_id, timestamp, epoch) in enumerate(items, start=1)\n    )\n    return OracleTemporalIntelligenceReport(\n        query=query,\n        answer_hash="a" * 64,\n        query_plan_hash="p" * 64,\n        query_result_hash="q" * 64,\n        report_hash="z" * 64,\n        events=events,\n    )\n"""\n        stub = stub.replace("__RELATIVE__", repr(relative)).replace("__HASH__", repr(artifact_hash))\n        (terminal / "oracle_temporal_intelligence_timeline_reconstruction.py").write_text(stub, encoding="utf-8")\n\n        old_path = list(sys.path)\n        old_cwd = Path.cwd()\n        try:\n            os.chdir(root)\n            sys.path.insert(0, str(root))\n            clear_modules()\n            module = __import__("qseries_v2.oracle_terminal.oracle_cross_market_intelligence_relationship_analysis", fromlist=["*"])\n            report = module.build_cross_market_intelligence_report(repository_root=root, query="compare related markets")\n            assert module.verify_cross_market_intelligence_report(report)\n            assert report.profile_count == 3, report.profile_count\n            assert report.relationship_count == 1, tuple(\n                (\n                    item.left_record_id,\n                    item.right_record_id,\n                    item.shared_entities,\n                )\n                for item in report.relationships\n            )\n            assert report.connected_profile_count == 2\n            assert report.independent_profile_count == 1\n            assert tuple(\n                (\n                    item.left_record_id,\n                    item.right_record_id,\n                )\n                for item in report.relationships\n            ) == (("BTC-ETF", "BTC-PRICE"),)\n            relationship = report.relationships[0]\n            assert relationship.left_record_id == "BTC-ETF"\n            assert relationship.right_record_id == "BTC-PRICE"\n            assert relationship.shared_entities == ("Bitcoin",)\n            assert "Kalshi" not in relationship.shared_entities\n            assert "Crypto" not in relationship.shared_entities\n            assert relationship.temporal_relationship == "left_leads_right"\n            assert relationship.directional_relationship == "contradictory"\n            assert relationship.probability_distance == 0.11\n            assert report.lead_lag_relationship_count == 1\n            assert report.contradictory_direction_count == 1\n            rendered = "\\n".join(module.cross_market_intelligence_lines(report))\n            assert "profile_count: 3" in rendered\n            assert "relationship_count: 1" in rendered\n            assert "Bitcoin" in rendered\n            assert "read_only: true" in rendered\n            before = artifact.read_bytes()\n            replay = module.build_cross_market_intelligence_report(repository_root=root, query="compare related markets")\n            assert replay.report_hash == report.report_hash\n            assert artifact.read_bytes() == before\n            artifact.write_text(\'{"mutated":true}\\n\', encoding="utf-8")\n            try:\n                module.build_cross_market_intelligence_report(repository_root=root, query="compare related markets")\n            except module.OracleCrossMarketRelationshipInvariantError:\n                pass\n            else:\n                raise AssertionError("mutated artifact accepted")\n        finally:\n            os.chdir(old_cwd)\n            sys.path[:] = old_path\n            clear_modules()\n\n    print("[PASS] Certified OIT-013 temporal report consumed")\n    print("[PASS] Certified artifact reopened read-only and hash verified")\n    print("[PASS] Exact source records located by certified record ID")\n    print("[PASS] Shared semantic entity relationship detected")\n    print("[PASS] Lead-lag relationship detected")\n    print("[PASS] Contradictory direction detected")\n    print("[PASS] Probability distance calculated deterministically")\n    print("[PASS] Venue-only and unrelated market links rejected")\n    print("[PASS] Relationship report deterministic across replay")\n    print("[PASS] Mutated artifact rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication and Q Series execution disabled")\n    print("[DONE] OIT-014 CORRECTION V2 REPOSITORY-ALIGNED PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def protected_sources() -> dict[Path, str]:
    protected = {}
    prefixes = (
        ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition",
        ROOT / "qseries_v2" / "oracle_intelligence" / "analytics",
        ROOT / "qseries_v2" / "oracle_intelligence_integration",
        ROOT / "qseries_v2" / "oracle_research_runtime",
        ROOT / "qseries_v2" / "oracle_operator_runtime",
        ROOT / "qseries_v2" / "qseries",
    )
    for base in prefixes:
        if base.exists():
            for path in base.rglob("*.py"):
                if path.is_file():
                    protected[path] = sha256(path)
    for path in (OIT_013, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def require_current_contract() -> None:
    if not OIT_013.is_file():
        raise RuntimeError(f"Certified OIT-013 module missing: {OIT_013}")
    temporal = OIT_013.read_text(encoding="utf-8")
    required_temporal = (
        'SCHEMA_VERSION = "OIT-013"',
        'POLICY_ID = "oracle.temporal-intelligence-timeline-reconstruction.v3"',
        "build_temporal_intelligence_report",
        "verify_temporal_intelligence_report",
        "artifact_sha256",
        "source_record_locator",
        "event_hash",
    )
    missing_temporal = [
        token for token in required_temporal
        if token not in temporal
    ]
    if missing_temporal:
        raise RuntimeError(
            f"Certified OIT-013 contract mismatch: {missing_temporal}"
        )

    if not PRODUCTION.is_file():
        raise RuntimeError(f"Current OIT-014 module missing: {PRODUCTION}")
    current = PRODUCTION.read_text(encoding="utf-8")
    required_current = (
        'SCHEMA_VERSION = "OIT-014"',
        'POLICY_ID = "oracle.cross-market-intelligence-relationship-analysis.v1"',
        "build_cross_market_intelligence_report",
        "verify_cross_market_intelligence_report",
        "ENTITY_FIELDS",
        "relationship_count",
        "qseries_execution_allowed",
    )
    missing_current = [
        token for token in required_current
        if token not in current
    ]
    if missing_current:
        raise RuntimeError(
            f"Current OIT-014 contract mismatch: {missing_current}"
        )


def main() -> int:
    print("=" * 40)
    print(" OIT-014 CORRECTION V2 INSTALLER")
    print(" FULL REPOSITORY-ALIGNED REPLACEMENT")
    print("=" * 40)
    try:
        require_current_contract()
        protected = protected_sources()

        print("[OK] Certified OIT-013 V3 temporal contract verified")
        print("[OK] Current OIT-014 V1 production contract verified")
        print("[OK] Venue/category entity-conflation defect isolated")
        print(
            f"[OK] Protected production source files captured: "
            f"{len(protected)}"
        )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_cross_market_intelligence_relationship_analysis "
            "import *"
        )
        current_init = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if export not in current_init.splitlines():
            if current_init and not current_init.endswith("\n"):
                current_init += "\n"
            INIT.write_text(
                current_init + export + "\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
        else:
            print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")
        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OIT-014 CORRECTION V2 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-013 production module unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Entire OIT-014 production module replaced")
        print("[PASS] Entire OIT-014 standalone test replaced")
        print("[PASS] Semantic entities separated from venue context")
        print("[PASS] Semantic entities separated from category context")
        print("[PASS] Venue-only false relationship rejected")
        print("[PASS] Unrelated football market remains independent")
        print("[PASS] Exact Bitcoin relationship retained")
        print("[PASS] Complete OIT-014 production test passed")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OIT-014 CORRECTION V2 "
            "FULL REPOSITORY-ALIGNED REPLACEMENT INSTALLED"
        )
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
