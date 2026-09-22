from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json

from .oad_279_gmgn_solana_token_intelligence_adapter import (
    acquire_current_gmgn_solana_token_intelligence,
)
from .oad_261_universal_expansion_source_single_writer_postgresql_persistence import (
    PRODUCER,
    PRIORITY,
    canonicalize_expansion_observation,
)
from .oad_068_exact_postgresql_independent_readback import (
    _backend,
    _query_one,
    exact_postgresql_readback,
)
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import (
    submit_observation_batch,
    await_request,
)

READ_ONLY = True
PROBABILITY_ENABLED = False
DIRECTION_ENABLED = False
PUBLICATION_ALLOWED = False
EXECUTION_AUTHORITY = False

BATCH_ID = "oad281.gmgn-solana-token-intelligence"


@dataclass(frozen=True, slots=True)
class GMGNExpansionObservation:
    source_id: str
    provenance_hash: str
    observed_at: object
    observation_type: str
    source_class: str
    provider: str
    subject: str
    payload: dict
    execution_authority: bool = False


@dataclass(frozen=True, slots=True)
class GMGNPersistenceResult:
    token_address: str
    raw_observations: int
    canonical_observations: int
    already_present: int
    committed_new: int
    exact_readback: int
    providers: tuple
    source_ids: tuple
    observation_ids: tuple
    rows: tuple
    execution_authority: bool = False


def _stable_hash(value):
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _build_section_observation(gmgn, section):
    token = str(gmgn.token_address).strip()
    payload = gmgn.payload.get(section)
    if not isinstance(payload, dict):
        raise RuntimeError(
            "GMGN " + section + " payload must be a dictionary"
        )

    source_id = "source.gmgn.solana.token." + token + "." + section
    provenance_hash = _stable_hash(
        {
            "source_id": source_id,
            "provider": "gmgn",
            "source_class": "token_intelligence",
            "subject": token,
            "observation_type": "gmgn_solana_token_" + section,
            "observed_at": gmgn.observed_at,
            "payload": payload,
        }
    )

    return GMGNExpansionObservation(
        source_id=source_id,
        provenance_hash=provenance_hash,
        observed_at=gmgn.observed_at,
        observation_type="gmgn_solana_token_" + section,
        source_class="token_intelligence",
        provider="gmgn",
        subject=token,
        payload=dict(payload),
        execution_authority=False,
    )


def build_gmgn_expansion_observations(gmgn):
    return tuple(
        _build_section_observation(gmgn, section)
        for section in ("info", "security", "pool")
    )


def persist_gmgn_solana_token_intelligence(
    root=None,
    timeout_seconds=120.0,
    acquisition_timeout_seconds=30.0,
):
    root = Path(root or Path.cwd()).resolve()

    gmgn = acquire_current_gmgn_solana_token_intelligence(
        timeout_seconds=acquisition_timeout_seconds,
        candidate_limit=5,
    )
    raw = build_gmgn_expansion_observations(gmgn)

    canonical = tuple(
        canonicalize_expansion_observation(x, BATCH_ID)
        for x in raw
    )

    backend = _backend(root)
    existing = 0
    missing = []

    for index, observation in enumerate(canonical):
        if _query_one(backend, observation.observation_id, index) is None:
            missing.append(observation)
        else:
            existing += 1

    committed = 0
    if missing:
        submission = submit_observation_batch(
            PRODUCER,
            PRIORITY,
            tuple(missing),
            root,
        )
        events = tuple(
            await_request(
                str(submission.request_id),
                root,
                float(timeout_seconds),
            )
        )
        accepted = tuple(
            event
            for event in events
            if getattr(event, "accepted", False) is True
        )
        if len(accepted) != len(missing):
            raise RuntimeError(
                "GMGN universal single-writer commit mismatch"
            )
        committed = len(accepted)

    ids = tuple(x.observation_id for x in canonical)
    rows = (
        tuple(exact_postgresql_readback(ids, root))
        if ids
        else ()
    )

    if len(rows) != len(ids):
        raise RuntimeError(
            "GMGN exact PostgreSQL readback mismatch"
        )

    return GMGNPersistenceResult(
        token_address=gmgn.token_address,
        raw_observations=len(raw),
        canonical_observations=len(canonical),
        already_present=existing,
        committed_new=committed,
        exact_readback=len(rows),
        providers=tuple(x.provider for x in raw),
        source_ids=tuple(x.source_id for x in raw),
        observation_ids=ids,
        rows=rows,
        execution_authority=False,
    )


# Preserve the old public entry point while moving it onto the corrected
# token-intelligence persistence boundary.
def persist_gmgn_solana_trending(
    root=None,
    timeout_seconds=120.0,
    acquisition_timeout_seconds=30.0,
):
    return persist_gmgn_solana_token_intelligence(
        root=root,
        timeout_seconds=timeout_seconds,
        acquisition_timeout_seconds=acquisition_timeout_seconds,
    )
