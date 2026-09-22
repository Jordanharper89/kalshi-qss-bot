"""
OLA-012
Oracle PostgreSQL Canonical Observation Persistence Backend

PostgreSQL implementation of the OLA-011 canonical persistence backend
contract.

Architecture:

CANONICAL OBSERVATION
    |
OLA-008 CANONICAL LEDGER SEMANTICS
    |
OLA-011 BACKEND CONTRACT
    |
OLA-012 POSTGRESQL BACKEND
    |
POSTGRESQL
    |
IMMUTABLE SNAPSHOT CHECKPOINTS

Permanent rules:

- PostgreSQL implements Oracle's canonical contract.
- PostgreSQL does not redefine canonical identity.
- Canonical observations are append-only.
- Duplicate observation identity is rejected.
- Duplicate content identity is rejected.
- Atomic batches commit all or none.
- Expected terminal chain identity must match.
- Sequence ordering is explicit.
- Chain continuity is explicit.
- Canonical observation JSON is preserved.
- Restored observations are contract-verified.
- Snapshot checkpoints are immutable.
- Caller supplies contract timestamps.
- Canonical stable hashing is used.
- repr() is never used.
- Oracle remains read-only intelligence.
- No execution adapter is resolved.
- No execution adapter is invoked.
- No trade authorization exists.
- No orders are placed.
- No funds are moved.
- No portfolio is mutated.

Driver note:

The backend accepts a connection_factory. Production may supply psycopg.connect
or another PostgreSQL DB-API-compatible connection factory.

The module intentionally does not silently install or select a database driver.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Callable, Mapping


from .oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    RawSourceObservation,
)

from .oracle_canonical_persistence_backend_contract import (
    CanonicalPersistenceAppendRequest,
    CanonicalPersistenceAppendResult,
    CanonicalPersistenceQueryRequest,
    CanonicalPersistenceSnapshotCheckpoint,
    PersistenceBackendCapabilityRecord,
    PersistenceBackendContractError,
    PersistenceBackendHealthRecord,
    REQUIRED_BACKEND_CAPABILITIES,
)


SCHEMA_VERSION = "OLA-012"
ENGINE_ID = "OLA-012"

BACKEND_ID = "backend.oracle.postgresql.canonical"
BACKEND_TYPE = "postgresql"

POSTGRESQL_CHAIN_GENESIS_TEXT = (
    "oracle.postgresql.canonical.persistence.genesis.v1"
)


class PostgreSQLPersistenceBackendError(RuntimeError):
    """Raised when the PostgreSQL backend fails."""


class PostgreSQLPersistenceSchemaError(
    PostgreSQLPersistenceBackendError
):
    """Raised when PostgreSQL schema initialization fails."""


class PostgreSQLPersistenceIntegrityError(
    PostgreSQLPersistenceBackendError
):
    """Raised when stored canonical evidence fails validation."""


def canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(
    value: Any,
) -> str:
    return sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


GENESIS_CHAIN_HASH = stable_hash(
    {
        "schema_version": SCHEMA_VERSION,
        "record_type": "postgresql_persistence_chain_genesis",
        "genesis_text": POSTGRESQL_CHAIN_GENESIS_TEXT,
    }
)


CREATE_OBSERVATIONS_SQL = """
/* ola012:create_observations */
CREATE TABLE IF NOT EXISTS oracle_canonical_observations (
    sequence_number BIGINT PRIMARY KEY,
    observation_id TEXT NOT NULL UNIQUE,
    content_hash TEXT NOT NULL UNIQUE,
    source_id TEXT NOT NULL,
    source_observation_id TEXT NOT NULL,
    observation_type TEXT NOT NULL,
    acquisition_batch_id TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    acquired_at TIMESTAMPTZ NOT NULL,
    persisted_at TIMESTAMPTZ NOT NULL,
    observation_replay_hash TEXT NOT NULL,
    canonical_observation_json JSONB NOT NULL,
    previous_chain_hash TEXT NOT NULL,
    chain_hash TEXT NOT NULL UNIQUE
)
"""

CREATE_SOURCE_INDEX_SQL = """
/* ola012:create_source_index */
CREATE INDEX IF NOT EXISTS idx_oracle_canonical_observations_source
ON oracle_canonical_observations (
    source_id,
    sequence_number
)
"""

CREATE_OBSERVED_INDEX_SQL = """
/* ola012:create_observed_index */
CREATE INDEX IF NOT EXISTS idx_oracle_canonical_observations_observed
ON oracle_canonical_observations (
    observed_at,
    sequence_number
)
"""

CREATE_STATE_SQL = """
/* ola012:create_state */
CREATE TABLE IF NOT EXISTS oracle_canonical_persistence_state (
    state_id SMALLINT PRIMARY KEY,
    terminal_sequence_number BIGINT NOT NULL,
    terminal_chain_hash TEXT NOT NULL
)
"""

CREATE_CHECKPOINTS_SQL = """
/* ola012:create_checkpoints */
CREATE TABLE IF NOT EXISTS oracle_persistence_snapshot_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    backend_id TEXT NOT NULL,
    snapshot_schema_version TEXT NOT NULL,
    snapshot_engine_id TEXT NOT NULL,
    snapshot_hash TEXT NOT NULL,
    entry_count BIGINT NOT NULL,
    terminal_chain_hash TEXT NOT NULL,
    checkpointed_at TIMESTAMPTZ NOT NULL,
    checkpoint_json JSONB NOT NULL,
    checkpoint_hash TEXT NOT NULL UNIQUE
)
"""

INSERT_GENESIS_STATE_SQL = """
/* ola012:insert_genesis_state */
INSERT INTO oracle_canonical_persistence_state (
    state_id,
    terminal_sequence_number,
    terminal_chain_hash
)
VALUES (
    1,
    0,
    %s
)
ON CONFLICT (state_id) DO NOTHING
"""

SELECT_STATE_FOR_UPDATE_SQL = """
/* ola012:select_state_for_update */
SELECT
    terminal_sequence_number,
    terminal_chain_hash
FROM oracle_canonical_persistence_state
WHERE state_id = 1
FOR UPDATE
"""

SELECT_STATE_SQL = """
/* ola012:select_state */
SELECT
    terminal_sequence_number,
    terminal_chain_hash
FROM oracle_canonical_persistence_state
WHERE state_id = 1
"""

SELECT_DUPLICATE_SQL = """
/* ola012:select_duplicate */
SELECT
    observation_id,
    content_hash
FROM oracle_canonical_observations
WHERE observation_id = %s
   OR content_hash = %s
LIMIT 1
"""

INSERT_OBSERVATION_SQL = """
/* ola012:insert_observation */
INSERT INTO oracle_canonical_observations (
    sequence_number,
    observation_id,
    content_hash,
    source_id,
    source_observation_id,
    observation_type,
    acquisition_batch_id,
    observed_at,
    acquired_at,
    persisted_at,
    observation_replay_hash,
    canonical_observation_json,
    previous_chain_hash,
    chain_hash
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s
)
"""

UPDATE_STATE_SQL = """
/* ola012:update_state */
UPDATE oracle_canonical_persistence_state
SET
    terminal_sequence_number = %s,
    terminal_chain_hash = %s
WHERE state_id = 1
"""

SELECT_BY_OBSERVATION_ID_SQL = """
/* ola012:query_by_observation_id */
SELECT canonical_observation_json
FROM oracle_canonical_observations
WHERE observation_id = %s
ORDER BY sequence_number
LIMIT 1
"""

SELECT_BY_SOURCE_ID_SQL = """
/* ola012:query_by_source_id */
SELECT canonical_observation_json
FROM oracle_canonical_observations
WHERE source_id = %s
ORDER BY sequence_number
LIMIT %s
"""

SELECT_BY_TIME_RANGE_SQL = """
/* ola012:query_by_time_range */
SELECT canonical_observation_json
FROM oracle_canonical_observations
WHERE observed_at >= %s
  AND observed_at <= %s
ORDER BY observed_at, sequence_number
LIMIT %s
"""

INSERT_CHECKPOINT_SQL = """
/* ola012:insert_checkpoint */
INSERT INTO oracle_persistence_snapshot_checkpoints (
    checkpoint_id,
    backend_id,
    snapshot_schema_version,
    snapshot_engine_id,
    snapshot_hash,
    entry_count,
    terminal_chain_hash,
    checkpointed_at,
    checkpoint_json,
    checkpoint_hash
)
VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s
)
"""

SELECT_CHECKPOINT_SQL = """
/* ola012:select_checkpoint */
SELECT checkpoint_json
FROM oracle_persistence_snapshot_checkpoints
WHERE checkpoint_id = %s
LIMIT 1
"""

HEALTH_SQL = """
/* ola012:health */
SELECT 1
"""


class OraclePostgreSQLCanonicalObservationPersistenceBackend:
    """
    PostgreSQL implementation of OLA-011.

    connection_factory must return a DB-API-style PostgreSQL connection.

    Expected connection behavior:
    - cursor()
    - commit()
    - rollback()
    - close()

    Expected cursor behavior:
    - execute(sql, params)
    - fetchone()
    - fetchall()
    - close()
    """

    backend_id = BACKEND_ID
    backend_type = BACKEND_TYPE

    read_only = True
    execution_allowed = False

    execution_adapter_resolved = False
    execution_adapter_invoked = False
    trade_authorization_allowed = False
    order_placement_allowed = False
    funds_moved = False
    portfolio_mutated = False

    def __init__(
        self,
        *,
        connection_factory: Callable[[], Any],
        auto_initialize_schema: bool = True,
    ) -> None:
        if not callable(connection_factory):
            raise PersistenceBackendContractError(
                "connection_factory must be callable"
            )

        self._connection_factory = connection_factory

        if auto_initialize_schema:
            self.initialize_schema()

        self._assert_invariants()

    def _assert_invariants(self) -> None:
        actual = {
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_adapter_resolved": (
                self.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                self.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

        expected = {
            "read_only": True,
            "execution_allowed": False,
            "execution_adapter_resolved": False,
            "execution_adapter_invoked": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        if actual != expected:
            raise PostgreSQLPersistenceIntegrityError(
                "PostgreSQL backend no-execution invariants violated"
            )

    def _connect(self):
        connection = self._connection_factory()

        if connection is None:
            raise PostgreSQLPersistenceBackendError(
                "connection_factory returned None"
            )

        return connection

    def initialize_schema(self) -> None:
        connection = self._connect()
        cursor = None

        try:
            cursor = connection.cursor()

            cursor.execute(
                CREATE_OBSERVATIONS_SQL
            )

            cursor.execute(
                CREATE_SOURCE_INDEX_SQL
            )

            cursor.execute(
                CREATE_OBSERVED_INDEX_SQL
            )

            cursor.execute(
                CREATE_STATE_SQL
            )

            cursor.execute(
                CREATE_CHECKPOINTS_SQL
            )

            cursor.execute(
                INSERT_GENESIS_STATE_SQL,
                (
                    GENESIS_CHAIN_HASH,
                ),
            )

            connection.commit()

        except Exception as exc:
            try:
                connection.rollback()
            except Exception:
                pass

            raise PostgreSQLPersistenceSchemaError(
                "PostgreSQL canonical persistence schema "
                "initialization failed"
            ) from exc

        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

            try:
                connection.close()
            except Exception:
                pass

    def capability_record(
        self,
        *,
        checked_at: datetime,
    ) -> PersistenceBackendCapabilityRecord:
        return PersistenceBackendCapabilityRecord.create(
            backend_id=self.backend_id,
            backend_type=self.backend_type,
            contract_version="OLA-011",
            supported_capabilities=(
                REQUIRED_BACKEND_CAPABILITIES
            ),
            checked_at=checked_at,
            backend_metadata={
                "implementation_engine_id": ENGINE_ID,
                "storage_engine": "PostgreSQL",
                "canonical_contract": "OLA-011",
                "schema_managed_by": ENGINE_ID,
            },
        )

    def health_record(
        self,
        *,
        checked_at: datetime,
    ) -> PersistenceBackendHealthRecord:
        connection = None
        cursor = None

        reachable = False
        writable = False
        readable = False
        transactional = False

        error_type = None

        try:
            connection = self._connect()

            reachable = True

            cursor = connection.cursor()

            cursor.execute(
                HEALTH_SQL
            )

            row = cursor.fetchone()

            readable = (
                row is not None
                and int(row[0]) == 1
            )

            connection.rollback()

            transactional = True

            cursor.close()
            cursor = connection.cursor()

            cursor.execute(
                SELECT_STATE_SQL
            )

            state = cursor.fetchone()

            writable = state is not None

            connection.rollback()

        except Exception as exc:
            error_type = type(exc).__name__

            if connection is not None:
                try:
                    connection.rollback()
                except Exception:
                    transactional = False

        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

        return PersistenceBackendHealthRecord.create(
            backend_id=self.backend_id,
            checked_at=checked_at,
            reachable=reachable,
            writable=writable,
            readable=readable,
            transactional=transactional,
            health_metadata={
                "implementation_engine_id": ENGINE_ID,
                "error_type": error_type,
            },
        )

    def append(
        self,
        *,
        request: CanonicalPersistenceAppendRequest,
        completed_at: datetime,
    ) -> CanonicalPersistenceAppendResult:
        self._assert_invariants()

        if not isinstance(
            request,
            CanonicalPersistenceAppendRequest,
        ):
            raise PersistenceBackendContractError(
                "request must be CanonicalPersistenceAppendRequest"
            )

        if request.backend_id != self.backend_id:
            raise PersistenceBackendContractError(
                "append request backend_id mismatch"
            )

        connection = self._connect()
        cursor = None

        prior_terminal_chain_hash = None

        try:
            cursor = connection.cursor()

            cursor.execute(
                SELECT_STATE_FOR_UPDATE_SQL
            )

            state = cursor.fetchone()

            if state is None:
                raise PostgreSQLPersistenceIntegrityError(
                    "canonical persistence state row is missing"
                )

            prior_sequence_number = int(
                state[0]
            )

            prior_terminal_chain_hash = str(
                state[1]
            )

            if (
                request.expected_terminal_chain_hash
                != prior_terminal_chain_hash
            ):
                connection.rollback()

                return CanonicalPersistenceAppendResult.create(
                    request=request,
                    append_status="rejected",
                    appended_count=0,
                    first_sequence_number=None,
                    last_sequence_number=None,
                    prior_terminal_chain_hash=(
                        prior_terminal_chain_hash
                    ),
                    terminal_chain_hash=(
                        prior_terminal_chain_hash
                    ),
                    persisted_observation_ids=(),
                    completed_at=completed_at,
                    atomic=True,
                    committed=False,
                    reason_codes=(
                        "expected_terminal_chain_hash_mismatch",
                        "append_rejected",
                    ),
                    backend_receipt_metadata={
                        "implementation_engine_id": ENGINE_ID,
                    },
                )

            for observation in request.observations:
                cursor.execute(
                    SELECT_DUPLICATE_SQL,
                    (
                        observation.observation_id,
                        observation.content_hash,
                    ),
                )

                duplicate = cursor.fetchone()

                if duplicate is not None:
                    connection.rollback()

                    duplicate_observation_id = str(
                        duplicate[0]
                    )

                    duplicate_content_hash = str(
                        duplicate[1]
                    )

                    if (
                        duplicate_observation_id
                        == observation.observation_id
                    ):
                        reason = (
                            "duplicate_observation_identity"
                        )
                    elif (
                        duplicate_content_hash
                        == observation.content_hash
                    ):
                        reason = (
                            "duplicate_content_identity"
                        )
                    else:
                        reason = (
                            "canonical_identity_conflict"
                        )

                    return (
                        CanonicalPersistenceAppendResult.create(
                            request=request,
                            append_status="rejected",
                            appended_count=0,
                            first_sequence_number=None,
                            last_sequence_number=None,
                            prior_terminal_chain_hash=(
                                prior_terminal_chain_hash
                            ),
                            terminal_chain_hash=(
                                prior_terminal_chain_hash
                            ),
                            persisted_observation_ids=(),
                            completed_at=completed_at,
                            atomic=True,
                            committed=False,
                            reason_codes=(
                                reason,
                                "append_rejected",
                            ),
                            backend_receipt_metadata={
                                "implementation_engine_id": (
                                    ENGINE_ID
                                ),
                            },
                        )
                    )

            sequence_number = prior_sequence_number

            previous_chain_hash = (
                prior_terminal_chain_hash
            )

            persisted_observation_ids = []

            first_sequence_number = (
                prior_sequence_number + 1
            )

            for observation in request.observations:
                sequence_number += 1

                observation_json = (
                    observation.to_canonical_dict()
                )

                chain_hash = stable_hash(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "record_type": (
                            "postgresql_canonical_chain_link"
                        ),
                        "sequence_number": sequence_number,
                        "previous_chain_hash": (
                            previous_chain_hash
                        ),
                        "observation_id": (
                            observation.observation_id
                        ),
                        "content_hash": (
                            observation.content_hash
                        ),
                        "observation_replay_hash": (
                            observation.replay_hash
                        ),
                        "canonical_observation": (
                            observation_json
                        ),
                        "persisted_at": completed_at.isoformat(),
                    }
                )

                cursor.execute(
                    INSERT_OBSERVATION_SQL,
                    (
                        sequence_number,
                        observation.observation_id,
                        observation.content_hash,
                        observation.source_id,
                        observation.source_observation_id,
                        observation.observation_type,
                        observation.acquisition_batch_id,
                        observation.observed_at,
                        observation.acquired_at,
                        completed_at,
                        observation.replay_hash,
                        json.dumps(
                            observation_json,
                            sort_keys=True,
                            separators=(",", ":"),
                            ensure_ascii=False,
                            allow_nan=False,
                        ),
                        previous_chain_hash,
                        chain_hash,
                    ),
                )

                persisted_observation_ids.append(
                    observation.observation_id
                )

                previous_chain_hash = chain_hash

            cursor.execute(
                UPDATE_STATE_SQL,
                (
                    sequence_number,
                    previous_chain_hash,
                ),
            )

            connection.commit()

            return CanonicalPersistenceAppendResult.create(
                request=request,
                append_status="committed",
                appended_count=len(
                    request.observations
                ),
                first_sequence_number=(
                    first_sequence_number
                ),
                last_sequence_number=sequence_number,
                prior_terminal_chain_hash=(
                    prior_terminal_chain_hash
                ),
                terminal_chain_hash=(
                    previous_chain_hash
                ),
                persisted_observation_ids=tuple(
                    persisted_observation_ids
                ),
                completed_at=completed_at,
                atomic=True,
                committed=True,
                reason_codes=(
                    "expected_terminal_chain_hash_verified",
                    "canonical_identity_checked",
                    "atomic_append_committed",
                    "chain_state_committed",
                ),
                backend_receipt_metadata={
                    "implementation_engine_id": ENGINE_ID,
                    "storage_engine": "PostgreSQL",
                    "transaction_committed": True,
                },
            )

        except Exception as exc:
            try:
                connection.rollback()
            except Exception:
                pass

            raise PostgreSQLPersistenceBackendError(
                "PostgreSQL canonical append failed closed"
            ) from exc

        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

            try:
                connection.close()
            except Exception:
                pass

    def query(
        self,
        *,
        request: CanonicalPersistenceQueryRequest,
    ) -> tuple[CanonicalObservation, ...]:
        self._assert_invariants()

        if not isinstance(
            request,
            CanonicalPersistenceQueryRequest,
        ):
            raise PersistenceBackendContractError(
                "request must be CanonicalPersistenceQueryRequest"
            )

        if request.backend_id != self.backend_id:
            raise PersistenceBackendContractError(
                "query request backend_id mismatch"
            )

        connection = self._connect()
        cursor = None

        try:
            cursor = connection.cursor()

            if request.query_type == "by_observation_id":
                cursor.execute(
                    SELECT_BY_OBSERVATION_ID_SQL,
                    (
                        request.observation_id,
                    ),
                )

            elif request.query_type == "by_source_id":
                cursor.execute(
                    SELECT_BY_SOURCE_ID_SQL,
                    (
                        request.source_id,
                        request.limit,
                    ),
                )

            elif (
                request.query_type
                == "by_observed_time_range"
            ):
                cursor.execute(
                    SELECT_BY_TIME_RANGE_SQL,
                    (
                        request.observed_from,
                        request.observed_to,
                        request.limit,
                    ),
                )

            else:
                raise PersistenceBackendContractError(
                    "unsupported canonical query type"
                )

            rows = cursor.fetchall()

            observations = tuple(
                self._restore_observation(
                    row[0]
                )
                for row in rows
            )

            connection.rollback()

            return observations

        except PersistenceBackendContractError:
            try:
                connection.rollback()
            except Exception:
                pass

            raise

        except Exception as exc:
            try:
                connection.rollback()
            except Exception:
                pass

            raise PostgreSQLPersistenceBackendError(
                "PostgreSQL canonical query failed closed"
            ) from exc

        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

            try:
                connection.close()
            except Exception:
                pass

    def terminal_chain_hash(self) -> str:
        self._assert_invariants()

        connection = self._connect()
        cursor = None

        try:
            cursor = connection.cursor()

            cursor.execute(
                SELECT_STATE_SQL
            )

            state = cursor.fetchone()

            if state is None:
                raise PostgreSQLPersistenceIntegrityError(
                    "canonical persistence state row is missing"
                )

            connection.rollback()

            return str(
                state[1]
            )

        except PostgreSQLPersistenceIntegrityError:
            try:
                connection.rollback()
            except Exception:
                pass

            raise

        except Exception as exc:
            try:
                connection.rollback()
            except Exception:
                pass

            raise PostgreSQLPersistenceBackendError(
                "PostgreSQL terminal chain inspection failed"
            ) from exc

        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

            try:
                connection.close()
            except Exception:
                pass

    def write_snapshot_checkpoint(
        self,
        *,
        checkpoint: CanonicalPersistenceSnapshotCheckpoint,
    ) -> CanonicalPersistenceSnapshotCheckpoint:
        self._assert_invariants()

        if not isinstance(
            checkpoint,
            CanonicalPersistenceSnapshotCheckpoint,
        ):
            raise PersistenceBackendContractError(
                "checkpoint must be "
                "CanonicalPersistenceSnapshotCheckpoint"
            )

        if checkpoint.backend_id != self.backend_id:
            raise PersistenceBackendContractError(
                "checkpoint backend_id mismatch"
            )

        current_terminal_hash = (
            self.terminal_chain_hash()
        )

        if (
            checkpoint.terminal_chain_hash
            != current_terminal_hash
        ):
            raise PostgreSQLPersistenceIntegrityError(
                "checkpoint terminal chain hash does not match "
                "backend state"
            )

        connection = self._connect()
        cursor = None

        try:
            cursor = connection.cursor()

            checkpoint_json = {
                "schema_version": checkpoint.schema_version,
                "engine_id": checkpoint.engine_id,
                "checkpoint_id": checkpoint.checkpoint_id,
                "backend_id": checkpoint.backend_id,
                "snapshot_schema_version": (
                    checkpoint.snapshot_schema_version
                ),
                "snapshot_engine_id": (
                    checkpoint.snapshot_engine_id
                ),
                "snapshot_hash": checkpoint.snapshot_hash,
                "entry_count": checkpoint.entry_count,
                "terminal_chain_hash": (
                    checkpoint.terminal_chain_hash
                ),
                "checkpointed_at": (
                    checkpoint.checkpointed_at.isoformat()
                ),
                "checkpoint_metadata": dict(
                    checkpoint.checkpoint_metadata
                ),
                "checkpoint_hash": checkpoint.checkpoint_hash,
                "immutable": checkpoint.immutable,
                "read_only": checkpoint.read_only,
                "execution_allowed": (
                    checkpoint.execution_allowed
                ),
            }

            cursor.execute(
                INSERT_CHECKPOINT_SQL,
                (
                    checkpoint.checkpoint_id,
                    checkpoint.backend_id,
                    checkpoint.snapshot_schema_version,
                    checkpoint.snapshot_engine_id,
                    checkpoint.snapshot_hash,
                    checkpoint.entry_count,
                    checkpoint.terminal_chain_hash,
                    checkpoint.checkpointed_at,
                    json.dumps(
                        checkpoint_json,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                        allow_nan=False,
                    ),
                    checkpoint.checkpoint_hash,
                ),
            )

            connection.commit()

            return checkpoint

        except Exception as exc:
            try:
                connection.rollback()
            except Exception:
                pass

            raise PostgreSQLPersistenceBackendError(
                "PostgreSQL snapshot checkpoint write failed closed"
            ) from exc

        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

            try:
                connection.close()
            except Exception:
                pass

    def read_snapshot_checkpoint(
        self,
        *,
        checkpoint_id: str,
    ) -> CanonicalPersistenceSnapshotCheckpoint | None:
        if not isinstance(checkpoint_id, str):
            raise PersistenceBackendContractError(
                "checkpoint_id must be a string"
            )

        normalized_checkpoint_id = (
            checkpoint_id.strip()
        )

        if not normalized_checkpoint_id:
            raise PersistenceBackendContractError(
                "checkpoint_id must not be empty"
            )

        connection = self._connect()
        cursor = None

        try:
            cursor = connection.cursor()

            cursor.execute(
                SELECT_CHECKPOINT_SQL,
                (
                    normalized_checkpoint_id,
                ),
            )

            row = cursor.fetchone()

            connection.rollback()

            if row is None:
                return None

            data = self._load_json_value(
                row[0]
            )

            checkpoint = (
                CanonicalPersistenceSnapshotCheckpoint.create(
                    checkpoint_id=data["checkpoint_id"],
                    backend_id=data["backend_id"],
                    snapshot_schema_version=(
                        data["snapshot_schema_version"]
                    ),
                    snapshot_engine_id=(
                        data["snapshot_engine_id"]
                    ),
                    snapshot_hash=data["snapshot_hash"],
                    entry_count=int(
                        data["entry_count"]
                    ),
                    terminal_chain_hash=(
                        data["terminal_chain_hash"]
                    ),
                    checkpointed_at=(
                        datetime.fromisoformat(
                            data["checkpointed_at"]
                        )
                    ),
                    checkpoint_metadata=(
                        data["checkpoint_metadata"]
                    ),
                )
            )

            if (
                checkpoint.checkpoint_hash
                != data["checkpoint_hash"]
            ):
                raise PostgreSQLPersistenceIntegrityError(
                    "stored checkpoint hash validation failed"
                )

            return checkpoint

        except PostgreSQLPersistenceIntegrityError:
            try:
                connection.rollback()
            except Exception:
                pass

            raise

        except Exception as exc:
            try:
                connection.rollback()
            except Exception:
                pass

            raise PostgreSQLPersistenceBackendError(
                "PostgreSQL snapshot checkpoint read failed closed"
            ) from exc

        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

            try:
                connection.close()
            except Exception:
                pass

    @classmethod
    def _restore_observation(
        cls,
        value: Any,
    ) -> CanonicalObservation:
        data = cls._load_json_value(
            value
        )

        required_fields = {
            "schema_version",
            "source_id",
            "source_observation_id",
            "observation_id",
            "observed_at",
            "acquired_at",
            "observation_type",
            "payload",
            "provenance",
            "acquisition_batch_id",
            "content_hash",
            "replay_hash",
            "read_only",
            "execution_allowed",
        }

        if set(data.keys()) != required_fields:
            raise PostgreSQLPersistenceIntegrityError(
                "stored canonical observation fields are incompatible"
            )

        if data["read_only"] is not True:
            raise PostgreSQLPersistenceIntegrityError(
                "stored observation lost read_only invariant"
            )

        if data["execution_allowed"] is not False:
            raise PostgreSQLPersistenceIntegrityError(
                "stored observation gained execution capability"
            )

        raw = RawSourceObservation.create(
            source_observation_id=(
                data["source_observation_id"]
            ),
            observed_at=datetime.fromisoformat(
                data["observed_at"]
            ),
            observation_type=data["observation_type"],
            payload=data["payload"],
            provenance=data["provenance"],
        )

        observation = CanonicalObservation.create(
            source_id=data["source_id"],
            raw_observation=raw,
            acquired_at=datetime.fromisoformat(
                data["acquired_at"]
            ),
            acquisition_batch_id=(
                data["acquisition_batch_id"]
            ),
        )

        if (
            observation.observation_id
            != data["observation_id"]
        ):
            raise PostgreSQLPersistenceIntegrityError(
                "stored observation_id validation failed"
            )

        if observation.content_hash != data["content_hash"]:
            raise PostgreSQLPersistenceIntegrityError(
                "stored content_hash validation failed"
            )

        if observation.replay_hash != data["replay_hash"]:
            raise PostgreSQLPersistenceIntegrityError(
                "stored replay_hash validation failed"
            )

        return observation

    @staticmethod
    def _load_json_value(
        value: Any,
    ) -> dict[str, Any]:
        if isinstance(value, str):
            loaded = json.loads(
                value
            )

        elif isinstance(value, Mapping):
            loaded = dict(value)

        else:
            raise PostgreSQLPersistenceIntegrityError(
                "stored JSON value has incompatible type"
            )

        if not isinstance(loaded, dict):
            raise PostgreSQLPersistenceIntegrityError(
                "stored JSON value must decode to mapping"
            )

        return loaded


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "BACKEND_ID",
    "BACKEND_TYPE",
    "GENESIS_CHAIN_HASH",
    "PostgreSQLPersistenceBackendError",
    "PostgreSQLPersistenceSchemaError",
    "PostgreSQLPersistenceIntegrityError",
    "OraclePostgreSQLCanonicalObservationPersistenceBackend",
    "canonical_json",
    "stable_hash",
]
