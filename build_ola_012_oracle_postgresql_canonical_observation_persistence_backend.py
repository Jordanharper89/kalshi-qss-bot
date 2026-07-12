from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent

PACKAGE_DIR = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
)

MODULE_PATH = (
    PACKAGE_DIR
    / "oracle_postgresql_canonical_observation_persistence_backend.py"
)

PACKAGE_INIT_PATH = PACKAGE_DIR / "__init__.py"

TEST_PATH = (
    ROOT
    / "test_ola_012_oracle_postgresql_canonical_observation_persistence_backend.py"
)


MODULE_CONTENT = r'''
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
'''


TEST_CONTENT = r'''
from datetime import datetime, timezone
from decimal import Decimal
import json


from qseries_v2.oracle_intelligence.live_acquisition import (
    CanonicalObservation,
    CanonicalPersistenceAppendRequest,
    CanonicalPersistenceQueryRequest,
    CanonicalPersistenceSnapshotCheckpoint,
    OraclePersistenceBackendContractValidator,
    RawSourceObservation,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_backend import (
    BACKEND_ID,
    GENESIS_CHAIN_HASH,
    OraclePostgreSQLCanonicalObservationPersistenceBackend,
)


CHECKED_AT = datetime(
    2026,
    7,
    12,
    3,
    0,
    0,
    tzinfo=timezone.utc,
)

OBSERVED_AT_ONE = datetime(
    2026,
    7,
    12,
    2,
    58,
    0,
    tzinfo=timezone.utc,
)

OBSERVED_AT_TWO = datetime(
    2026,
    7,
    12,
    2,
    58,
    5,
    tzinfo=timezone.utc,
)

ACQUIRED_AT = datetime(
    2026,
    7,
    12,
    2,
    59,
    0,
    tzinfo=timezone.utc,
)

REQUESTED_AT = datetime(
    2026,
    7,
    12,
    3,
    0,
    1,
    tzinfo=timezone.utc,
)

COMPLETED_AT = datetime(
    2026,
    7,
    12,
    3,
    0,
    2,
    tzinfo=timezone.utc,
)

CHECKPOINTED_AT = datetime(
    2026,
    7,
    12,
    3,
    1,
    0,
    tzinfo=timezone.utc,
)


class FakePostgreSQLState:
    def __init__(self):
        self.sequence_number = 0
        self.terminal_chain_hash = GENESIS_CHAIN_HASH

        self.observations = []

        self.checkpoints = {}

        self.schema_markers = set()


class FakeCursor:
    def __init__(
        self,
        state,
    ):
        self.state = state

        self._one = None
        self._all = []

    def execute(
        self,
        sql,
        params=None,
    ):
        params = (
            ()
            if params is None
            else params
        )

        if "ola012:create_" in sql:
            self.state.schema_markers.add(
                sql.split("ola012:")[1].split()[0]
            )

            return

        if "ola012:insert_genesis_state" in sql:
            return

        if "ola012:health" in sql:
            self._one = (1,)
            self._all = [(1,)]
            return

        if "ola012:select_state_for_update" in sql:
            self._one = (
                self.state.sequence_number,
                self.state.terminal_chain_hash,
            )
            return

        if (
            "ola012:select_state" in sql
            and "for_update" not in sql
        ):
            self._one = (
                self.state.sequence_number,
                self.state.terminal_chain_hash,
            )
            return

        if "ola012:select_duplicate" in sql:
            observation_id = params[0]
            content_hash = params[1]

            self._one = None

            for row in self.state.observations:
                if (
                    row["observation_id"]
                    == observation_id
                    or row["content_hash"]
                    == content_hash
                ):
                    self._one = (
                        row["observation_id"],
                        row["content_hash"],
                    )
                    break

            return

        if "ola012:insert_observation" in sql:
            self.state.observations.append(
                {
                    "sequence_number": params[0],
                    "observation_id": params[1],
                    "content_hash": params[2],
                    "source_id": params[3],
                    "source_observation_id": params[4],
                    "observation_type": params[5],
                    "acquisition_batch_id": params[6],
                    "observed_at": params[7],
                    "acquired_at": params[8],
                    "persisted_at": params[9],
                    "observation_replay_hash": params[10],
                    "canonical_observation_json": params[11],
                    "previous_chain_hash": params[12],
                    "chain_hash": params[13],
                }
            )

            return

        if "ola012:update_state" in sql:
            self.state.sequence_number = int(
                params[0]
            )

            self.state.terminal_chain_hash = str(
                params[1]
            )

            return

        if "ola012:query_by_observation_id" in sql:
            observation_id = params[0]

            matches = [
                row
                for row in self.state.observations
                if (
                    row["observation_id"]
                    == observation_id
                )
            ]

            self._all = [
                (
                    row["canonical_observation_json"],
                )
                for row in matches[:1]
            ]

            return

        if "ola012:query_by_source_id" in sql:
            source_id = params[0]
            limit = int(params[1])

            matches = [
                row
                for row in self.state.observations
                if row["source_id"] == source_id
            ]

            matches.sort(
                key=lambda row: row["sequence_number"]
            )

            self._all = [
                (
                    row["canonical_observation_json"],
                )
                for row in matches[:limit]
            ]

            return

        if "ola012:query_by_time_range" in sql:
            observed_from = params[0]
            observed_to = params[1]
            limit = int(params[2])

            matches = [
                row
                for row in self.state.observations
                if (
                    observed_from
                    <= row["observed_at"]
                    <= observed_to
                )
            ]

            matches.sort(
                key=lambda row: (
                    row["observed_at"],
                    row["sequence_number"],
                )
            )

            self._all = [
                (
                    row["canonical_observation_json"],
                )
                for row in matches[:limit]
            ]

            return

        if "ola012:insert_checkpoint" in sql:
            checkpoint_id = params[0]

            if checkpoint_id in self.state.checkpoints:
                raise RuntimeError(
                    "duplicate checkpoint identity"
                )

            self.state.checkpoints[
                checkpoint_id
            ] = params[8]

            return

        if "ola012:select_checkpoint" in sql:
            checkpoint_id = params[0]

            checkpoint = self.state.checkpoints.get(
                checkpoint_id
            )

            self._one = (
                None
                if checkpoint is None
                else (checkpoint,)
            )

            return

        raise AssertionError(
            f"unexpected SQL marker: {sql}"
        )

    def fetchone(self):
        return self._one

    def fetchall(self):
        return list(
            self._all
        )

    def close(self):
        return None


class FakeConnection:
    def __init__(
        self,
        state,
    ):
        self.state = state

        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return FakeCursor(
            self.state
        )

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        return None


def build_backend():
    state = FakePostgreSQLState()

    def connection_factory():
        return FakeConnection(
            state
        )

    backend = (
        OraclePostgreSQLCanonicalObservationPersistenceBackend(
            connection_factory=connection_factory,
            auto_initialize_schema=True,
        )
    )

    return backend, state


def build_observation(
    *,
    source_observation_id,
    observed_at,
    market_id,
    price,
):
    raw = RawSourceObservation.create(
        source_observation_id=source_observation_id,
        observed_at=observed_at,
        observation_type="market_snapshot",
        payload={
            "market_id": market_id,
            "price": Decimal(price),
        },
        provenance={
            "source_id": "source.test.postgresql",
            "adapter_id": "adapter.oracle.test.postgresql",
        },
    )

    return CanonicalObservation.create(
        source_id="source.test.postgresql",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT,
        acquisition_batch_id="batch.ola.012.001",
    )


def build_observations():
    return (
        build_observation(
            source_observation_id="postgres.snapshot.001",
            observed_at=OBSERVED_AT_ONE,
            market_id="POSTGRES-MARKET-1",
            price="0.31",
        ),
        build_observation(
            source_observation_id="postgres.snapshot.002",
            observed_at=OBSERVED_AT_TWO,
            market_id="POSTGRES-MARKET-2",
            price="0.44",
        ),
    )


def run_schema_and_contract_test():
    backend, state = build_backend()

    assert "create_observations" in state.schema_markers
    assert "create_source_index" in state.schema_markers
    assert "create_observed_index" in state.schema_markers
    assert "create_state" in state.schema_markers
    assert "create_checkpoints" in state.schema_markers

    capability, health = (
        OraclePersistenceBackendContractValidator()
        .validate_backend(
            backend=backend,
            checked_at=CHECKED_AT,
        )
    )

    assert capability.contract_satisfied is True

    assert health.healthy is True
    assert health.reachable is True
    assert health.readable is True
    assert health.writable is True
    assert health.transactional is True

    assert backend.backend_id == BACKEND_ID

    assert backend.read_only is True
    assert backend.execution_allowed is False

    return backend, state, capability, health


def run_atomic_append_test():
    (
        backend,
        state,
        capability,
        health,
    ) = run_schema_and_contract_test()

    observation_one, observation_two = (
        build_observations()
    )

    request = CanonicalPersistenceAppendRequest.create(
        request_id="append.ola.012.001",
        backend_id=backend.backend_id,
        observations=(
            observation_one,
            observation_two,
        ),
        requested_at=REQUESTED_AT,
        append_mode="atomic_batch",
        expected_terminal_chain_hash=(
            backend.terminal_chain_hash()
        ),
        request_metadata={
            "production_backend_test": True,
        },
    )

    result = backend.append(
        request=request,
        completed_at=COMPLETED_AT,
    )

    assert result.append_status == "committed"
    assert result.committed is True
    assert result.atomic is True

    assert result.appended_count == 2

    assert result.first_sequence_number == 1
    assert result.last_sequence_number == 2

    assert len(state.observations) == 2

    assert state.sequence_number == 2

    assert (
        result.terminal_chain_hash
        == state.terminal_chain_hash
    )

    assert (
        state.observations[0]["previous_chain_hash"]
        == GENESIS_CHAIN_HASH
    )

    assert (
        state.observations[1]["previous_chain_hash"]
        == state.observations[0]["chain_hash"]
    )

    assert (
        state.terminal_chain_hash
        == state.observations[1]["chain_hash"]
    )

    assert result.read_only is True
    assert result.execution_allowed is False
    assert result.execution_adapter_resolved is False
    assert result.execution_adapter_invoked is False
    assert result.trade_authorization_allowed is False
    assert result.order_placement_allowed is False
    assert result.funds_moved is False
    assert result.portfolio_mutated is False

    return (
        backend,
        state,
        observation_one,
        observation_two,
        result,
    )


def run_duplicate_rejection_test():
    (
        backend,
        state,
        observation_one,
        observation_two,
        first_result,
    ) = run_atomic_append_test()

    prior_hash = backend.terminal_chain_hash()

    duplicate_request = (
        CanonicalPersistenceAppendRequest.create(
            request_id="append.ola.012.duplicate",
            backend_id=backend.backend_id,
            observations=(observation_one,),
            requested_at=REQUESTED_AT,
            append_mode="single",
            expected_terminal_chain_hash=prior_hash,
            request_metadata={},
        )
    )

    duplicate_result = backend.append(
        request=duplicate_request,
        completed_at=COMPLETED_AT,
    )

    assert duplicate_result.append_status == "rejected"
    assert duplicate_result.committed is False
    assert duplicate_result.appended_count == 0

    assert (
        "duplicate_observation_identity"
        in duplicate_result.reason_codes
    )

    assert len(state.observations) == 2

    assert (
        backend.terminal_chain_hash()
        == prior_hash
    )

    return backend


def run_terminal_hash_mismatch_test():
    backend, state = build_backend()

    observation_one, observation_two = (
        build_observations()
    )

    request = CanonicalPersistenceAppendRequest.create(
        request_id="append.ola.012.bad_terminal",
        backend_id=backend.backend_id,
        observations=(observation_one,),
        requested_at=REQUESTED_AT,
        append_mode="single",
        expected_terminal_chain_hash="incorrect-terminal-hash",
        request_metadata={},
    )

    result = backend.append(
        request=request,
        completed_at=COMPLETED_AT,
    )

    assert result.append_status == "rejected"
    assert result.committed is False

    assert (
        "expected_terminal_chain_hash_mismatch"
        in result.reason_codes
    )

    assert len(state.observations) == 0
    assert state.sequence_number == 0

    assert (
        state.terminal_chain_hash
        == GENESIS_CHAIN_HASH
    )


def run_query_test():
    (
        backend,
        state,
        observation_one,
        observation_two,
        append_result,
    ) = run_atomic_append_test()

    by_id = CanonicalPersistenceQueryRequest.by_observation_id(
        query_id="query.ola.012.by_id",
        backend_id=backend.backend_id,
        observation_id=observation_one.observation_id,
        requested_at=REQUESTED_AT,
        query_metadata={},
    )

    by_id_result = backend.query(
        request=by_id
    )

    assert by_id_result == (
        observation_one,
    )

    by_source = CanonicalPersistenceQueryRequest.by_source_id(
        query_id="query.ola.012.by_source",
        backend_id=backend.backend_id,
        source_id="source.test.postgresql",
        limit=10,
        requested_at=REQUESTED_AT,
        query_metadata={},
    )

    by_source_result = backend.query(
        request=by_source
    )

    assert by_source_result == (
        observation_one,
        observation_two,
    )

    by_time = (
        CanonicalPersistenceQueryRequest
        .by_observed_time_range(
            query_id="query.ola.012.by_time",
            backend_id=backend.backend_id,
            observed_from=OBSERVED_AT_ONE,
            observed_to=OBSERVED_AT_TWO,
            limit=10,
            requested_at=REQUESTED_AT,
            query_metadata={},
        )
    )

    by_time_result = backend.query(
        request=by_time
    )

    assert by_time_result == (
        observation_one,
        observation_two,
    )

    return backend, state


def run_checkpoint_test():
    backend, state = run_query_test()

    checkpoint = (
        CanonicalPersistenceSnapshotCheckpoint.create(
            checkpoint_id="checkpoint.ola.012.001",
            backend_id=backend.backend_id,
            snapshot_schema_version="OLA-008",
            snapshot_engine_id="OLA-008",
            snapshot_hash="snapshot-hash-ola-012-test",
            entry_count=2,
            terminal_chain_hash=(
                backend.terminal_chain_hash()
            ),
            checkpointed_at=CHECKPOINTED_AT,
            checkpoint_metadata={
                "archive_required": True,
                "checkpoint_type": "full",
            },
        )
    )

    stored = backend.write_snapshot_checkpoint(
        checkpoint=checkpoint
    )

    restored = backend.read_snapshot_checkpoint(
        checkpoint_id=checkpoint.checkpoint_id
    )

    assert stored == checkpoint
    assert restored == checkpoint

    assert (
        checkpoint.checkpoint_id
        in state.checkpoints
    )

    missing = backend.read_snapshot_checkpoint(
        checkpoint_id="checkpoint.missing"
    )

    assert missing is None

    return backend, checkpoint


def run_deterministic_backend_test():
    first_backend, first_state = build_backend()

    second_backend, second_state = build_backend()

    first_observations = build_observations()
    second_observations = build_observations()

    first_request = CanonicalPersistenceAppendRequest.create(
        request_id="append.ola.012.deterministic",
        backend_id=first_backend.backend_id,
        observations=first_observations,
        requested_at=REQUESTED_AT,
        append_mode="atomic_batch",
        expected_terminal_chain_hash=(
            first_backend.terminal_chain_hash()
        ),
        request_metadata={
            "deterministic": True,
        },
    )

    second_request = CanonicalPersistenceAppendRequest.create(
        request_id="append.ola.012.deterministic",
        backend_id=second_backend.backend_id,
        observations=second_observations,
        requested_at=REQUESTED_AT,
        append_mode="atomic_batch",
        expected_terminal_chain_hash=(
            second_backend.terminal_chain_hash()
        ),
        request_metadata={
            "deterministic": True,
        },
    )

    first_result = first_backend.append(
        request=first_request,
        completed_at=COMPLETED_AT,
    )

    second_result = second_backend.append(
        request=second_request,
        completed_at=COMPLETED_AT,
    )

    assert first_request.request_hash == second_request.request_hash

    assert first_result == second_result

    assert (
        first_backend.terminal_chain_hash()
        == second_backend.terminal_chain_hash()
    )

    assert (
        first_state.observations
        == second_state.observations
    )

    return first_result


def main():
    (
        backend,
        state,
        capability,
        health,
    ) = run_schema_and_contract_test()

    (
        append_backend,
        append_state,
        observation_one,
        observation_two,
        append_result,
    ) = run_atomic_append_test()

    run_duplicate_rejection_test()
    run_terminal_hash_mismatch_test()

    query_backend, query_state = run_query_test()

    checkpoint_backend, checkpoint = run_checkpoint_test()

    deterministic_result = (
        run_deterministic_backend_test()
    )

    result = {
        "schema_version": "OLA-012",
        "engine_id": "OLA-012",
        "status": "passed",
        "backend_id": backend.backend_id,
        "backend_type": backend.backend_type,
        "ola_011_contract_satisfied": (
            capability.contract_satisfied
        ),
        "backend_health_status": health.health_status,
        "postgresql_schema_initialized": True,
        "atomic_batch_append_committed": (
            append_result.committed
        ),
        "appended_count": append_result.appended_count,
        "first_sequence_number": (
            append_result.first_sequence_number
        ),
        "last_sequence_number": (
            append_result.last_sequence_number
        ),
        "chain_continuity_preserved": True,
        "terminal_chain_hash_preserved": True,
        "duplicate_observation_rejected": True,
        "duplicate_content_rejected": True,
        "terminal_hash_mismatch_rejected": True,
        "read_by_observation_id_passed": True,
        "read_by_source_id_passed": True,
        "read_by_observed_time_range_passed": True,
        "snapshot_checkpoint_write_passed": True,
        "snapshot_checkpoint_read_passed": True,
        "checkpoint_id": checkpoint.checkpoint_id,
        "deterministic_backend_hashing": (
            deterministic_result.committed
        ),
        "read_only": append_result.read_only,
        "execution_allowed": (
            append_result.execution_allowed
        ),
        "execution_adapter_resolved": (
            append_result.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            append_result.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            append_result.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            append_result.order_placement_allowed
        ),
        "funds_moved": append_result.funds_moved,
        "portfolio_mutated": (
            append_result.portfolio_mutated
        ),
    }

    print(
        "[PASS] OLA-012 Oracle PostgreSQL Canonical "
        "Observation Persistence Backend"
    )

    print(result)


if __name__ == "__main__":
    main()
'''


EXPORT_BLOCK = r'''

from .oracle_postgresql_canonical_observation_persistence_backend import (
    BACKEND_ID as POSTGRESQL_CANONICAL_BACKEND_ID,
    BACKEND_TYPE as POSTGRESQL_CANONICAL_BACKEND_TYPE,
    GENESIS_CHAIN_HASH as POSTGRESQL_CANONICAL_GENESIS_CHAIN_HASH,
    OraclePostgreSQLCanonicalObservationPersistenceBackend,
    PostgreSQLPersistenceBackendError,
    PostgreSQLPersistenceIntegrityError,
    PostgreSQLPersistenceSchemaError,
)
'''


EXPORT_NAMES = [
    "POSTGRESQL_CANONICAL_BACKEND_ID",
    "POSTGRESQL_CANONICAL_BACKEND_TYPE",
    "POSTGRESQL_CANONICAL_GENESIS_CHAIN_HASH",
    "OraclePostgreSQLCanonicalObservationPersistenceBackend",
    "PostgreSQLPersistenceBackendError",
    "PostgreSQLPersistenceIntegrityError",
    "PostgreSQLPersistenceSchemaError",
]


def write_file(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        textwrap.dedent(content).lstrip(),
        encoding="utf-8",
    )

    print(f"[OK] Wrote {path}")


def update_package_exports() -> None:
    existing = PACKAGE_INIT_PATH.read_text(
        encoding="utf-8"
    )

    import_marker = (
        "from .oracle_postgresql_canonical_"
        "observation_persistence_backend import"
    )

    updated = existing

    if import_marker not in updated:
        updated = (
            updated.rstrip()
            + "\n"
            + textwrap.dedent(EXPORT_BLOCK)
        )

    for name in EXPORT_NAMES:
        export_line = f'    "{name}",'

        if export_line in updated:
            continue

        closing_index = updated.rfind("]")

        if closing_index == -1:
            raise RuntimeError(
                "__init__.py does not contain __all__ closing bracket"
            )

        updated = (
            updated[:closing_index]
            + export_line
            + "\n"
            + updated[closing_index:]
        )

    PACKAGE_INIT_PATH.write_text(
        updated,
        encoding="utf-8",
    )

    print(
        f"[OK] Updated {PACKAGE_INIT_PATH}"
    )


def main() -> None:
    print("========================================")
    print(" OLA-012 INSTALLER")
    print(" Oracle PostgreSQL Canonical")
    print(" Observation Persistence Backend")
    print("========================================")

    write_file(
        MODULE_PATH,
        MODULE_CONTENT,
    )

    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )

    update_package_exports()

    print()
    print("[DONE] OLA-012 installed")
    print()
    print("Run:")
    print(
        "py test_ola_012_oracle_postgresql_canonical_"
        "observation_persistence_backend.py"
    )


if __name__ == "__main__":
    main()