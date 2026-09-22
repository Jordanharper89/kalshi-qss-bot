from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence

ENGINE_ID = "OII-003"
SCHEMA_VERSION = "OII-003.v1"
ALGORITHM_VERSION = "source-provenance-graph.v1"

ALLOWED_RELATIONSHIPS = (
    "derived_from", "quotes", "summarizes", "confirms", "contradicts",
    "duplicates", "depends_on", "causally_related_to",
    "historically_analogous_to", "same_primary_origin",
)
DEPENDENCY_RELATIONSHIPS = frozenset({
    "derived_from", "quotes", "summarizes", "duplicates",
    "depends_on", "same_primary_origin",
})
ORIGIN_RELATIONSHIPS = frozenset({
    "derived_from", "quotes", "summarizes", "duplicates",
    "same_primary_origin",
})


class OracleSourceProvenanceInvariantError(ValueError):
    pass


def _stable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _stable(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}
    if is_dataclass(value):
        return _stable(asdict(value))
    if isinstance(value, (tuple, list)):
        return [_stable(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_stable(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(value, datetime):
        return _timestamp(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "__dict__"):
        return _stable(vars(value))
    return str(value)


def canonical_json(value: Any) -> str:
    return json.dumps(_stable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def stable_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OracleSourceProvenanceInvariantError(f"{name} must be a non-empty string")
    return value.strip()


def _timestamp(value: Any) -> str:
    if isinstance(value, str):
        candidate = value.strip()
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        try:
            value = datetime.fromisoformat(candidate)
        except ValueError as exc:
            raise OracleSourceProvenanceInvariantError("invalid ISO-8601 timestamp") from exc
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise OracleSourceProvenanceInvariantError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _metadata(value: Any) -> tuple[tuple[str, Any], ...]:
    if value is None:
        return ()
    items = value.items() if isinstance(value, Mapping) else value
    result = []
    seen = set()
    for key, item in items:
        key = _text(key, "metadata key")
        if key in seen:
            raise OracleSourceProvenanceInvariantError("duplicate metadata key")
        seen.add(key)
        result.append((key, _stable(item)))
    return tuple(sorted(result))


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if is_dataclass(value):
        return {field.name: getattr(value, field.name) for field in fields(value)}
    if hasattr(value, "__dict__"):
        return vars(value)
    raise OracleSourceProvenanceInvariantError("OII-002 evidence must be record-like")


def _first(payload: Mapping[str, Any], names: Sequence[str], required: bool = True) -> Any:
    for name in names:
        if name in payload:
            return payload[name]
    if required:
        raise OracleSourceProvenanceInvariantError(f"missing required field; expected one of {tuple(names)}")
    return None


@dataclass(frozen=True)
class SourceIdentityNode:
    node_id: str
    source_id: str
    source_class: str
    source_locator: str
    source_identity_hash: str
    primary_origin_hint: str
    observed_at: str
    metadata: tuple[tuple[str, Any], ...]
    node_hash: str


@dataclass(frozen=True)
class EvidenceIdentityNode:
    node_id: str
    evidence_id: str
    source_id: str
    observation_id: str
    content_hash: str
    replay_hash: str
    chain_hash: str
    observed_at: str
    valid_from: str
    valid_until: str
    claim_ids: tuple[str, ...]
    metadata: tuple[tuple[str, Any], ...]
    node_hash: str


@dataclass(frozen=True)
class ProvenanceEdge:
    edge_id: str
    from_node_id: str
    to_node_id: str
    relationship: str
    asserted_by_evidence_id: str
    observed_at: str
    confidence_basis: str
    metadata: tuple[tuple[str, Any], ...]
    edge_hash: str


@dataclass(frozen=True)
class SourceOriginResolution:
    node_id: str
    primary_origin_node_ids: tuple[str, ...]
    dependency_chain_node_ids: tuple[str, ...]
    shared_origin_group_ids: tuple[str, ...]
    circular_dependency_detected: bool
    resolution_hash: str


@dataclass(frozen=True)
class SourceProvenanceGraph:
    graph_id: str
    source_nodes: tuple[SourceIdentityNode, ...]
    evidence_nodes: tuple[EvidenceIdentityNode, ...]
    edges: tuple[ProvenanceEdge, ...]
    origin_resolutions: tuple[SourceOriginResolution, ...]
    circular_paths: tuple[tuple[str, ...], ...]
    deterministic_traversal: tuple[str, ...]
    graph_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    created_at: str
    read_only: bool
    publication_allowed: bool
    alerting_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool


def build_source_node(*, source_id: str, source_class: str, source_locator: str,
                      source_identity_hash: str, observed_at: Any,
                      primary_origin_hint: str = "", metadata: Any = ()) -> SourceIdentityNode:
    source_id = _text(source_id, "source_id")
    source_class = _text(source_class, "source_class")
    source_locator = _text(source_locator, "source_locator")
    if not _sha(source_identity_hash):
        raise OracleSourceProvenanceInvariantError("source_identity_hash must be lowercase SHA-256")
    body = {
        "node_id": "source:" + stable_hash((source_id, source_class, source_locator, source_identity_hash)),
        "source_id": source_id,
        "source_class": source_class,
        "source_locator": source_locator,
        "source_identity_hash": source_identity_hash,
        "primary_origin_hint": str(primary_origin_hint).strip(),
        "observed_at": _timestamp(observed_at),
        "metadata": _metadata(metadata),
    }
    return SourceIdentityNode(**body, node_hash=stable_hash(body))


def build_evidence_node(*, evidence_id: str, source_id: str, observation_id: str,
                        content_hash: str, replay_hash: str, chain_hash: str,
                        observed_at: Any, valid_from: Any, valid_until: Any,
                        claim_ids: Sequence[str] = (), metadata: Any = ()) -> EvidenceIdentityNode:
    evidence_id = _text(evidence_id, "evidence_id")
    source_id = _text(source_id, "source_id")
    observation_id = _text(observation_id, "observation_id")
    for name, value in (("content_hash", content_hash), ("replay_hash", replay_hash), ("chain_hash", chain_hash)):
        if not _sha(value):
            raise OracleSourceProvenanceInvariantError(f"{name} must be lowercase SHA-256")
    valid_from = _timestamp(valid_from)
    valid_until = _timestamp(valid_until)
    if valid_until < valid_from:
        raise OracleSourceProvenanceInvariantError("valid_until precedes valid_from")
    claims = tuple(sorted({_text(v, "claim_id") for v in claim_ids}))
    body = {
        "node_id": "evidence:" + stable_hash((evidence_id, source_id, observation_id, content_hash, replay_hash, chain_hash)),
        "evidence_id": evidence_id,
        "source_id": source_id,
        "observation_id": observation_id,
        "content_hash": content_hash,
        "replay_hash": replay_hash,
        "chain_hash": chain_hash,
        "observed_at": _timestamp(observed_at),
        "valid_from": valid_from,
        "valid_until": valid_until,
        "claim_ids": claims,
        "metadata": _metadata(metadata),
    }
    return EvidenceIdentityNode(**body, node_hash=stable_hash(body))


def build_evidence_node_from_oii002(value: Any) -> EvidenceIdentityNode:
    payload = _mapping(value)
    if _first(payload, ("read_only", "is_read_only")) is not True:
        raise OracleSourceProvenanceInvariantError("OII-002 evidence must be read-only")
    forbidden = (
        "publication_allowed", "publishing_allowed", "alerting_allowed", "alerts_allowed",
        "qseries_handoff_allowed", "qseries_execution_allowed", "execution_allowed",
        "order_creation_allowed", "order_placement_allowed", "funds_movement_allowed",
        "funds_moved", "portfolio_mutation_allowed", "portfolio_mutated",
    )
    for field in forbidden:
        if field in payload and payload[field] is not False:
            raise OracleSourceProvenanceInvariantError(f"forbidden OII-002 authority: {field}")

    claims = _first(payload, ("claims", "canonical_claims", "claim_ids"), False) or ()
    claim_ids = []
    for claim in claims:
        if isinstance(claim, str):
            claim_ids.append(claim)
        else:
            item = _mapping(claim)
            claim_ids.append(str(_first(item, ("claim_id", "id", "claim_hash"))))

    return build_evidence_node(
        evidence_id=str(_first(payload, ("evidence_id", "canonical_evidence_id", "record_id"))),
        source_id=str(_first(payload, ("source_id",))),
        observation_id=str(_first(payload, ("observation_id", "source_observation_id"))),
        content_hash=str(_first(payload, ("content_hash", "evidence_content_hash"))),
        replay_hash=str(_first(payload, ("replay_hash",))),
        chain_hash=str(_first(payload, ("chain_hash", "lineage_hash"))),
        observed_at=_first(payload, ("observed_at", "observation_timestamp")),
        valid_from=_first(payload, ("valid_from", "validity_started_at", "observed_at")),
        valid_until=_first(payload, ("valid_until", "expires_at", "validity_ended_at")),
        claim_ids=claim_ids,
        metadata={"source_contract": "OII-002"},
    )


def build_provenance_edge(*, from_node_id: str, to_node_id: str, relationship: str,
                          asserted_by_evidence_id: str, observed_at: Any,
                          confidence_basis: str, metadata: Any = ()) -> ProvenanceEdge:
    from_node_id = _text(from_node_id, "from_node_id")
    to_node_id = _text(to_node_id, "to_node_id")
    if from_node_id == to_node_id:
        raise OracleSourceProvenanceInvariantError("self edge rejected")
    if relationship not in ALLOWED_RELATIONSHIPS:
        raise OracleSourceProvenanceInvariantError("unsupported relationship")
    body = {
        "edge_id": "edge:" + stable_hash((from_node_id, to_node_id, relationship, asserted_by_evidence_id)),
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
        "relationship": relationship,
        "asserted_by_evidence_id": _text(asserted_by_evidence_id, "asserted_by_evidence_id"),
        "observed_at": _timestamp(observed_at),
        "confidence_basis": _text(confidence_basis, "confidence_basis"),
        "metadata": _metadata(metadata),
    }
    return ProvenanceEdge(**body, edge_hash=stable_hash(body))


def _verify(record: Any, hash_field: str) -> None:
    body = asdict(record)
    supplied = body.pop(hash_field)
    if stable_hash(body) != supplied:
        raise OracleSourceProvenanceInvariantError(f"{hash_field} verification failed")


def _reachable(start: str, adjacency: Mapping[str, tuple[str, ...]]) -> tuple[str, ...]:
    seen, pending = set(), list(adjacency.get(start, ()))
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        pending.extend(adjacency.get(current, ()))
    seen.discard(start)
    return tuple(sorted(seen))


def _cycles(node_ids: Sequence[str], adjacency: Mapping[str, tuple[str, ...]]) -> tuple[tuple[str, ...], ...]:
    state = {node: 0 for node in node_ids}
    stack, positions, found = [], {}, set()

    def canonical(path: tuple[str, ...]) -> tuple[str, ...]:
        base = path[:-1]
        rotations = [base[i:] + base[:i] for i in range(len(base))]
        chosen = min(rotations)
        return chosen + (chosen[0],)

    def visit(node: str) -> None:
        state[node] = 1
        positions[node] = len(stack)
        stack.append(node)
        for target in adjacency.get(node, ()):
            if state[target] == 0:
                visit(target)
            elif state[target] == 1:
                found.add(canonical(tuple(stack[positions[target]:]) + (target,)))
        stack.pop()
        positions.pop(node, None)
        state[node] = 2

    for node in sorted(node_ids):
        if state[node] == 0:
            visit(node)
    return tuple(sorted(found))


def build_source_provenance_graph(*, source_nodes: Iterable[SourceIdentityNode],
                                  evidence_nodes: Iterable[EvidenceIdentityNode],
                                  edges: Iterable[ProvenanceEdge],
                                  created_at: Any) -> SourceProvenanceGraph:
    sources = tuple(sorted(source_nodes, key=lambda x: x.node_id))
    evidence = tuple(sorted(evidence_nodes, key=lambda x: x.node_id))
    edge_items = tuple(sorted(edges, key=lambda x: x.edge_id))
    nodes = sources + evidence
    if not nodes:
        raise OracleSourceProvenanceInvariantError("empty graph rejected")

    by_id = {}
    evidence_ids = set()
    source_ids = set()
    for node in nodes:
        _verify(node, "node_hash")
        if node.node_id in by_id:
            raise OracleSourceProvenanceInvariantError("duplicate node")
        by_id[node.node_id] = node
        if isinstance(node, SourceIdentityNode):
            if node.source_id in source_ids:
                raise OracleSourceProvenanceInvariantError("duplicate source identity")
            source_ids.add(node.source_id)
        else:
            if node.evidence_id in evidence_ids:
                raise OracleSourceProvenanceInvariantError("duplicate evidence identity")
            evidence_ids.add(node.evidence_id)

    seen_edges = set()
    dependency = {node: [] for node in by_id}
    origin = {node: [] for node in by_id}
    undirected = {node: set() for node in by_id}
    for edge in edge_items:
        _verify(edge, "edge_hash")
        if edge.from_node_id not in by_id or edge.to_node_id not in by_id:
            raise OracleSourceProvenanceInvariantError("edge references unknown node")
        if edge.asserted_by_evidence_id not in evidence_ids:
            raise OracleSourceProvenanceInvariantError("edge assertion lacks evidence")
        identity = (edge.from_node_id, edge.to_node_id, edge.relationship)
        if identity in seen_edges:
            raise OracleSourceProvenanceInvariantError("duplicate edge")
        seen_edges.add(identity)
        if edge.relationship in DEPENDENCY_RELATIONSHIPS:
            dependency[edge.from_node_id].append(edge.to_node_id)
        if edge.relationship in ORIGIN_RELATIONSHIPS:
            origin[edge.from_node_id].append(edge.to_node_id)
            undirected[edge.from_node_id].add(edge.to_node_id)
            undirected[edge.to_node_id].add(edge.from_node_id)

    dependency = {k: tuple(sorted(v)) for k, v in dependency.items()}
    origin = {k: tuple(sorted(v)) for k, v in origin.items()}
    circular_paths = _cycles(tuple(by_id), dependency)
    circular_nodes = {node for path in circular_paths for node in path}

    group_for = {}
    unseen = set(by_id)
    while unseen:
        seed = min(unseen)
        component, pending = set(), [seed]
        while pending:
            node = pending.pop()
            if node in component:
                continue
            component.add(node)
            pending.extend(undirected[node])
        unseen -= component
        group = "origin-group:" + stable_hash(tuple(sorted(component)))
        for node in component:
            group_for[node] = group

    resolutions = []
    for node in sorted(by_id):
        chain = _reachable(node, dependency)
        reachable_origins = set(_reachable(node, origin))
        candidates = reachable_origins or {node}
        primary = tuple(sorted(x for x in candidates if not any(y in candidates for y in origin.get(x, ()))))
        if not primary:
            primary = tuple(sorted(candidates))
        groups = tuple(sorted({group_for[x] for x in (node,) + chain}))
        body = {
            "node_id": node,
            "primary_origin_node_ids": primary,
            "dependency_chain_node_ids": chain,
            "shared_origin_group_ids": groups,
            "circular_dependency_detected": node in circular_nodes,
        }
        resolutions.append(SourceOriginResolution(**body, resolution_hash=stable_hash(body)))

    created = _timestamp(created_at)
    identity = {
        "source_nodes": sources, "evidence_nodes": evidence, "edges": edge_items,
        "origin_resolutions": tuple(resolutions), "circular_paths": circular_paths,
        "deterministic_traversal": tuple(sorted(by_id)), "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION, "algorithm_version": ALGORITHM_VERSION,
    }
    graph_hash = stable_hash(identity)
    return SourceProvenanceGraph(
        graph_id="provenance-graph:" + graph_hash,
        source_nodes=sources,
        evidence_nodes=evidence,
        edges=edge_items,
        origin_resolutions=tuple(resolutions),
        circular_paths=circular_paths,
        deterministic_traversal=tuple(sorted(by_id)),
        graph_hash=graph_hash,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        created_at=created,
        read_only=True,
        publication_allowed=False,
        alerting_allowed=False,
        qseries_handoff_allowed=False,
        qseries_execution_allowed=False,
        order_creation_allowed=False,
        funds_movement_allowed=False,
        portfolio_mutation_allowed=False,
    )


def serialize_graph(graph: SourceProvenanceGraph) -> str:
    return canonical_json(graph)


def verify_graph(graph: SourceProvenanceGraph) -> bool:
    rebuilt = build_source_provenance_graph(
        source_nodes=graph.source_nodes,
        evidence_nodes=graph.evidence_nodes,
        edges=graph.edges,
        created_at=graph.created_at,
    )
    if rebuilt.graph_hash != graph.graph_hash or rebuilt.graph_id != graph.graph_id:
        raise OracleSourceProvenanceInvariantError("graph verification failed")
    forbidden = (
        graph.publication_allowed, graph.alerting_allowed, graph.qseries_handoff_allowed,
        graph.qseries_execution_allowed, graph.order_creation_allowed,
        graph.funds_movement_allowed, graph.portfolio_mutation_allowed,
    )
    if graph.read_only is not True or any(forbidden):
        raise OracleSourceProvenanceInvariantError("Oracle safety boundary violated")
    return True
