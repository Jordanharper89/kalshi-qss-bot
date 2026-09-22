from __future__ import annotations
from dataclasses import dataclass

OPH_029_BUILD_ID="OPH-029"
OPH_029_REVISION="OPH_029_POSTGRESQL_ROUTING_FAILURE_CLASSIFICATION_V1"

RETRYABLE_MARKERS=(
    "not committed",
    "timeout",
    "timed out",
    "connection",
    "closed",
    "serialization",
    "deadlock",
    "could not serialize",
    "server closed",
    "connection reset",
)

TERMINAL_MARKERS=(
    "expected_terminal_chain_hash_mismatch",
    "duplicate key value violates unique constraint",
    "invalid observation",
    "schema mismatch",
)

@dataclass(frozen=True)
class PersistenceFailureClassification:
    category:str
    retryable:bool
    terminal:bool
    fingerprint:str

def classify_persistence_failure(exc):
    name=type(exc).__name__
    message=str(exc)
    text=(name+" "+message).lower()

    if any(marker in text for marker in TERMINAL_MARKERS):
        category="TERMINAL_INTEGRITY"
        retryable=False
        terminal=True
    elif any(marker in text for marker in RETRYABLE_MARKERS):
        category="TRANSIENT_POSTGRESQL"
        retryable=True
        terminal=False
    elif "postgresqlpersistenceroutingfailure" in text:
        category="TRANSIENT_POSTGRESQL"
        retryable=True
        terminal=False
    else:
        category="UNKNOWN"
        retryable=True
        terminal=False

    fingerprint=f"{name}:{message}"[:512]
    return PersistenceFailureClassification(category,retryable,terminal,fingerprint)

def verify_oph_029_postgresql_routing_failure_classification(root=None):
    class PostgreSQLPersistenceRoutingFailure(Exception):
        pass
    c=classify_persistence_failure(
        PostgreSQLPersistenceRoutingFailure("PostgreSQL batch append was not committed")
    )
    return (
        OPH_029_BUILD_ID=="OPH-029"
        and c.category=="TRANSIENT_POSTGRESQL"
        and c.retryable
        and not c.terminal
    )
