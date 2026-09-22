from __future__ import annotations

"""
INT-ORACLE-LIVE-001
Oracle Live Terminal Evidence Bridge

A narrow read-only bridge between the existing local PostgreSQL observation
corpus and the frozen Oracle Terminal display boundary.

This module does not perform prediction, scoring, publication, execution,
memory mutation, or market action.
"""

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "INT-ORACLE-LIVE-001"
ENGINE_ID = "INT-ORACLE-LIVE-001"
POLICY_ID = "oracle.live-terminal-evidence-bridge.v1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
ACTION_AUTHORIZATION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False

_PRICE_WORDS = (
    "price",
    "mark",
    "last_price",
    "last",
    "mid",
    "close",
    "value",
)

_SYMBOL_WORDS = (
    "symbol",
    "ticker",
    "asset",
    "asset_id",
    "instrument",
    "market_symbol",
    "underlying",
    "name",
)

_TIME_WORDS = (
    "observed_at",
    "timestamp",
    "created_at",
    "event_time",
    "received_at",
    "updated_at",
    "as_of",
    "time",
)

_JSON_WORDS = (
    "payload",
    "data",
    "observation",
    "record",
    "body",
    "raw",
    "normalized",
    "metadata",
)

_ASSET_ALIASES = {
    "bitcoin": ("bitcoin", "btc", "xbt", "btc/usd", "btcusd"),
    "btc": ("bitcoin", "btc", "xbt", "btc/usd", "btcusd"),
    "ethereum": ("ethereum", "eth", "eth/usd", "ethusd"),
    "eth": ("ethereum", "eth", "eth/usd", "ethusd"),
    "solana": ("solana", "sol", "sol/usd", "solusd"),
    "sol": ("solana", "sol", "sol/usd", "solusd"),
}


class OracleLiveTerminalEvidenceBridgeError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LiveTerminalEvidence:
    query: str
    asset: str
    source_table: str
    source_column: str
    source_identity: str
    price: float
    observed_at: str | None
    source_record: Mapping[str, Any]
    database_read_performed: bool
    read_only: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    evidence_hash: str


@dataclass(frozen=True, slots=True)
class LiveTerminalEvidenceResult:
    query: str
    matched: bool
    evidence: LiveTerminalEvidence | None
    reason: str
    database_read_performed: bool
    read_only: bool
    execution_allowed: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    result_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))

    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]

    if isinstance(value, datetime):
        return value.isoformat()

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    return str(value)


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def _load_env_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}

    if not path.is_file():
        return result

    for raw in path.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines():
        line = raw.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split("=", 1)

        key = key.strip()
        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        if key:
            result[key] = value

    return result


def _database_configuration(
    repository_root: str | Path,
) -> dict[str, str]:
    root = Path(repository_root).resolve()

    environment = dict(os.environ)
    environment.update(
        _load_env_file(root / ".env")
    )

    url = (
        environment.get("ORACLE_POSTGRES_URL")
        or environment.get("DATABASE_URL")
        or ""
    ).strip()

    if url:
        return {
            "url": url,
        }

    host = environment.get("ORACLE_POSTGRES_HOST", "localhost")
    port = environment.get("ORACLE_POSTGRES_PORT", "5432")
    database = environment.get("ORACLE_POSTGRES_DB", "postgres")
    user = (
        environment.get("ORACLE_POSTGRES_USER")
        or environment.get("POSTGRES_USER")
        or "postgres"
    )
    password = (
        environment.get("ORACLE_POSTGRES_PASSWORD")
        or environment.get("POSTGRES_PASSWORD")
        or ""
    )
    sslmode = environment.get(
        "ORACLE_POSTGRES_SSLMODE",
        "prefer",
    )

    return {
        "host": host,
        "port": port,
        "dbname": database,
        "user": user,
        "password": password,
        "sslmode": sslmode,
    }


def _connect_read_only(
    repository_root: str | Path,
):
    configuration = _database_configuration(
        repository_root
    )

    connection = None
    driver = None

    try:
        import psycopg  # type: ignore

        driver = "psycopg"

        if "url" in configuration:
            connection = psycopg.connect(
                configuration["url"],
            )
        else:
            connection = psycopg.connect(
                **configuration,
            )

    except ImportError:
        try:
            import psycopg2  # type: ignore

            driver = "psycopg2"

            if "url" in configuration:
                connection = psycopg2.connect(
                    configuration["url"],
                )
            else:
                connection = psycopg2.connect(
                    **configuration,
                )

        except ImportError as exc:
            raise OracleLiveTerminalEvidenceBridgeError(
                "Neither psycopg nor psycopg2 is installed."
            ) from exc

    if connection is None:
        raise OracleLiveTerminalEvidenceBridgeError(
            "Unable to create PostgreSQL connection."
        )

    connection.autocommit = False

    cursor = connection.cursor()

    cursor.execute(
        "SET TRANSACTION READ ONLY"
    )

    cursor.execute(
        "SET LOCAL statement_timeout = '5000ms'"
    )

    cursor.execute(
        "SELECT current_setting('transaction_read_only')"
    )

    row = cursor.fetchone()

    if not row or str(row[0]).lower() != "on":
        connection.rollback()
        connection.close()

        raise OracleLiveTerminalEvidenceBridgeError(
            "PostgreSQL transaction is not read-only."
        )

    cursor.close()

    return connection, driver


def _quote_identifier(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise OracleLiveTerminalEvidenceBridgeError(
            "Invalid SQL identifier."
        )

    return '"' + value.replace('"', '""') + '"'


def _query_asset(query: str) -> str | None:
    normalized = " ".join(
        str(query).strip().lower().split()
    )

    if not normalized:
        return None

    price_intent = bool(
        re.search(
            r"\b(current|latest|live|last|now)\b",
            normalized,
        )
        and re.search(
            r"\b(price|value|trading)\b",
            normalized,
        )
    )

    if not price_intent:
        return None

    for canonical, aliases in _ASSET_ALIASES.items():
        if canonical not in {
            "bitcoin",
            "ethereum",
            "solana",
        }:
            continue

        for alias in aliases:
            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(alias.lower())
                + r"(?![a-z0-9])"
            )

            if re.search(pattern, normalized):
                return canonical

    return None


def is_live_factual_price_query(
    query: str,
) -> bool:
    return _query_asset(query) is not None


def _column_inventory(cursor) -> dict[str, list[tuple[str, str]]]:
    cursor.execute(
        """
        SELECT
            table_name,
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
        """
    )

    inventory: dict[str, list[tuple[str, str]]] = {}

    for table_name, column_name, data_type in cursor.fetchall():
        inventory.setdefault(
            str(table_name),
            [],
        ).append(
            (
                str(column_name),
                str(data_type),
            )
        )

    return inventory


def _first_matching_column(
    columns: list[tuple[str, str]],
    candidates: tuple[str, ...],
) -> str | None:
    lowered = {
        name.lower(): name
        for name, _ in columns
    }

    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]

    for name, _ in columns:
        lower = name.lower()

        if any(
            token in lower
            for token in candidates
        ):
            return name

    return None


def _json_columns(
    columns: list[tuple[str, str]],
) -> tuple[str, ...]:
    result: list[str] = []

    for name, data_type in columns:
        lower = name.lower()

        if (
            data_type.lower() in {"json", "jsonb"}
            or any(token in lower for token in _JSON_WORDS)
        ):
            result.append(name)

    return tuple(result)


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None

    if isinstance(value, (int, float)):
        numeric = float(value)

        if numeric > 0:
            return numeric

        return None

    if isinstance(value, str):
        cleaned = (
            value.strip()
            .replace("$", "")
            .replace(",", "")
        )

        try:
            numeric = float(cleaned)

            if numeric > 0:
                return numeric

        except ValueError:
            return None

    return None


def _find_price_in_json(
    value: Any,
) -> tuple[str, float] | None:
    preferred = {
        "price",
        "last_price",
        "last",
        "mark",
        "mid",
        "close",
        "current_price",
        "index_price",
        "spot_price",
    }

    def walk(
        item: Any,
        path: str,
    ) -> tuple[str, float] | None:
        if isinstance(item, Mapping):
            keys = sorted(
                item,
                key=lambda key: str(key),
            )

            for key in keys:
                key_text = str(key).lower()

                if key_text in preferred:
                    numeric = _numeric(item[key])

                    if numeric is not None:
                        return (
                            f"{path}.{key}",
                            numeric,
                        )

            for key in keys:
                found = walk(
                    item[key],
                    f"{path}.{key}",
                )

                if found is not None:
                    return found

        elif isinstance(item, (tuple, list)):
            for index, child in enumerate(item):
                found = walk(
                    child,
                    f"{path}[{index}]",
                )

                if found is not None:
                    return found

        return None

    return walk(value, "$")


def _row_mapping(
    cursor,
    row: tuple[Any, ...],
) -> dict[str, Any]:
    names = tuple(
        str(description[0])
        for description in cursor.description
    )

    return {
        names[index]: row[index]
        for index in range(len(names))
    }


def _asset_text_matches(
    value: Any,
    aliases: tuple[str, ...],
) -> bool:
    text = str(value).lower()

    for alias in aliases:
        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(alias.lower())
            + r"(?![a-z0-9])"
        )

        if re.search(pattern, text):
            return True

    return False


def _direct_table_candidate(
    cursor,
    *,
    table: str,
    columns: list[tuple[str, str]],
    aliases: tuple[str, ...],
) -> tuple[
    str,
    float,
    str | None,
    dict[str, Any],
] | None:
    price_column = _first_matching_column(
        columns,
        _PRICE_WORDS,
    )

    symbol_column = _first_matching_column(
        columns,
        _SYMBOL_WORDS,
    )

    if price_column is None or symbol_column is None:
        return None

    time_column = _first_matching_column(
        columns,
        _TIME_WORDS,
    )

    quoted_table = _quote_identifier(table)
    quoted_price = _quote_identifier(price_column)
    quoted_symbol = _quote_identifier(symbol_column)

    ordering = ""

    if time_column is not None:
        ordering = (
            " ORDER BY "
            + _quote_identifier(time_column)
            + " DESC NULLS LAST"
        )

    sql = (
        "SELECT * FROM "
        + quoted_table
        + " WHERE "
        + quoted_symbol
        + " IS NOT NULL"
        + " AND "
        + quoted_price
        + " IS NOT NULL"
        + ordering
        + " LIMIT 250"
    )

    cursor.execute(sql)

    for row in cursor.fetchall():
        record = _row_mapping(
            cursor,
            row,
        )

        if not _asset_text_matches(
            record.get(symbol_column),
            aliases,
        ):
            continue

        price = _numeric(
            record.get(price_column)
        )

        if price is None:
            continue

        observed_at = None

        if time_column is not None:
            raw_time = record.get(time_column)

            if raw_time is not None:
                observed_at = (
                    raw_time.isoformat()
                    if hasattr(raw_time, "isoformat")
                    else str(raw_time)
                )

        return (
            price_column,
            price,
            observed_at,
            record,
        )

    return None


def _json_table_candidate(
    cursor,
    *,
    table: str,
    columns: list[tuple[str, str]],
    aliases: tuple[str, ...],
) -> tuple[
    str,
    float,
    str | None,
    dict[str, Any],
] | None:
    json_columns = _json_columns(columns)

    if not json_columns:
        return None

    time_column = _first_matching_column(
        columns,
        _TIME_WORDS,
    )

    ordering = ""

    if time_column is not None:
        ordering = (
            " ORDER BY "
            + _quote_identifier(time_column)
            + " DESC NULLS LAST"
        )

    cursor.execute(
        "SELECT * FROM "
        + _quote_identifier(table)
        + ordering
        + " LIMIT 250"
    )

    for row in cursor.fetchall():
        record = _row_mapping(
            cursor,
            row,
        )

        searchable = json.dumps(
            _canonical(record),
            sort_keys=True,
            ensure_ascii=True,
        ).lower()

        if not any(
            _asset_text_matches(
                searchable,
                (alias,),
            )
            for alias in aliases
        ):
            continue

        for column in json_columns:
            raw = record.get(column)

            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except Exception:
                    pass

            found = _find_price_in_json(raw)

            if found is None:
                continue

            json_path, price = found

            observed_at = None

            if time_column is not None:
                raw_time = record.get(time_column)

                if raw_time is not None:
                    observed_at = (
                        raw_time.isoformat()
                        if hasattr(raw_time, "isoformat")
                        else str(raw_time)
                    )

            return (
                f"{column}:{json_path}",
                price,
                observed_at,
                record,
            )

    return None


def read_live_price_evidence(
    repository_root: str | Path,
    query: str,
) -> LiveTerminalEvidenceResult:
    root = Path(repository_root).resolve()

    asset = _query_asset(query)

    if asset is None:
        body = {
            "query": str(query),
            "matched": False,
            "evidence": None,
            "reason": "query_not_supported_by_live_factual_bridge",
            "database_read_performed": False,
            "read_only": True,
            "execution_allowed": False,
            "publication_allowed": False,
            "action_authorization_allowed": False,
            "qseries_execution_allowed": False,
        }

        return LiveTerminalEvidenceResult(
            **body,
            result_hash=_stable_hash(body),
        )

    aliases = _ASSET_ALIASES[asset]

    connection = None

    try:
        connection, _driver = _connect_read_only(root)

        cursor = connection.cursor()

        inventory = _column_inventory(cursor)

        preferred_tables = sorted(
            inventory,
            key=lambda name: (
                0
                if any(
                    token in name.lower()
                    for token in (
                        "observation",
                        "market",
                        "price",
                        "quote",
                        "snapshot",
                        "tick",
                        "corpus",
                    )
                )
                else 1,
                name,
            ),
        )

        candidate = None

        for table in preferred_tables:
            try:
                candidate = _direct_table_candidate(
                    cursor,
                    table=table,
                    columns=inventory[table],
                    aliases=aliases,
                )
            except Exception:
                connection.rollback()

                cursor = connection.cursor()
                cursor.execute(
                    "SET TRANSACTION READ ONLY"
                )

                continue

            if candidate is not None:
                source_column, price, observed_at, record = candidate

                source_identity = (
                    table
                    + ":"
                    + _stable_hash(record)[:24]
                )

                evidence_body = {
                    "query": str(query),
                    "asset": asset,
                    "source_table": table,
                    "source_column": source_column,
                    "source_identity": source_identity,
                    "price": price,
                    "observed_at": observed_at,
                    "source_record": record,
                    "database_read_performed": True,
                    "read_only": True,
                    "publication_allowed": False,
                    "action_authorization_allowed": False,
                    "qseries_execution_allowed": False,
                }

                evidence = LiveTerminalEvidence(
                    **evidence_body,
                    evidence_hash=_stable_hash(
                        evidence_body
                    ),
                )

                body = {
                    "query": str(query),
                    "matched": True,
                    "evidence": evidence,
                    "reason": "live_read_only_evidence_found",
                    "database_read_performed": True,
                    "read_only": True,
                    "execution_allowed": False,
                    "publication_allowed": False,
                    "action_authorization_allowed": False,
                    "qseries_execution_allowed": False,
                }

                result = LiveTerminalEvidenceResult(
                    **body,
                    result_hash=_stable_hash(body),
                )

                cursor.close()
                connection.rollback()
                connection.close()

                return result

        for table in preferred_tables:
            try:
                candidate = _json_table_candidate(
                    cursor,
                    table=table,
                    columns=inventory[table],
                    aliases=aliases,
                )
            except Exception:
                connection.rollback()

                cursor = connection.cursor()
                cursor.execute(
                    "SET TRANSACTION READ ONLY"
                )

                continue

            if candidate is not None:
                source_column, price, observed_at, record = candidate

                source_identity = (
                    table
                    + ":"
                    + _stable_hash(record)[:24]
                )

                evidence_body = {
                    "query": str(query),
                    "asset": asset,
                    "source_table": table,
                    "source_column": source_column,
                    "source_identity": source_identity,
                    "price": price,
                    "observed_at": observed_at,
                    "source_record": record,
                    "database_read_performed": True,
                    "read_only": True,
                    "publication_allowed": False,
                    "action_authorization_allowed": False,
                    "qseries_execution_allowed": False,
                }

                evidence = LiveTerminalEvidence(
                    **evidence_body,
                    evidence_hash=_stable_hash(
                        evidence_body
                    ),
                )

                body = {
                    "query": str(query),
                    "matched": True,
                    "evidence": evidence,
                    "reason": "live_read_only_evidence_found",
                    "database_read_performed": True,
                    "read_only": True,
                    "execution_allowed": False,
                    "publication_allowed": False,
                    "action_authorization_allowed": False,
                    "qseries_execution_allowed": False,
                }

                result = LiveTerminalEvidenceResult(
                    **body,
                    result_hash=_stable_hash(body),
                )

                cursor.close()
                connection.rollback()
                connection.close()

                return result

        cursor.close()
        connection.rollback()
        connection.close()

        body = {
            "query": str(query),
            "matched": False,
            "evidence": None,
            "reason": "no_matching_live_price_evidence_found",
            "database_read_performed": True,
            "read_only": True,
            "execution_allowed": False,
            "publication_allowed": False,
            "action_authorization_allowed": False,
            "qseries_execution_allowed": False,
        }

        return LiveTerminalEvidenceResult(
            **body,
            result_hash=_stable_hash(body),
        )

    except Exception as exc:
        if connection is not None:
            try:
                connection.rollback()
            except Exception:
                pass

            try:
                connection.close()
            except Exception:
                pass

        body = {
            "query": str(query),
            "matched": False,
            "evidence": None,
            "reason": (
                "live_evidence_bridge_unavailable:"
                + type(exc).__name__
                + ":"
                + str(exc)
            ),
            "database_read_performed": False,
            "read_only": True,
            "execution_allowed": False,
            "publication_allowed": False,
            "action_authorization_allowed": False,
            "qseries_execution_allowed": False,
        }

        return LiveTerminalEvidenceResult(
            **body,
            result_hash=_stable_hash(body),
        )


def verify_live_terminal_evidence_result(
    result: LiveTerminalEvidenceResult,
) -> bool:
    body = asdict(result)
    supplied = body.pop("result_hash")

    if _stable_hash(body) != supplied:
        raise OracleLiveTerminalEvidenceBridgeError(
            "live terminal evidence result hash mismatch"
        )

    if result.read_only is not True:
        raise OracleLiveTerminalEvidenceBridgeError(
            "live terminal evidence bridge lost read-only boundary"
        )

    if (
        result.execution_allowed
        or result.publication_allowed
        or result.action_authorization_allowed
        or result.qseries_execution_allowed
    ):
        raise OracleLiveTerminalEvidenceBridgeError(
            "forbidden live terminal capability enabled"
        )

    if result.matched:
        if result.evidence is None:
            raise OracleLiveTerminalEvidenceBridgeError(
                "matched result has no evidence"
            )

        evidence_body = asdict(result.evidence)
        evidence_hash = evidence_body.pop(
            "evidence_hash"
        )

        if _stable_hash(evidence_body) != evidence_hash:
            raise OracleLiveTerminalEvidenceBridgeError(
                "live evidence hash mismatch"
            )

        if result.evidence.price <= 0:
            raise OracleLiveTerminalEvidenceBridgeError(
                "live evidence price invalid"
            )

        if not result.evidence.source_table:
            raise OracleLiveTerminalEvidenceBridgeError(
                "live evidence source table missing"
            )

        if not result.evidence.source_identity:
            raise OracleLiveTerminalEvidenceBridgeError(
                "live evidence source identity missing"
            )

    return True


def render_live_terminal_evidence(
    result: LiveTerminalEvidenceResult,
) -> tuple[str, ...]:
    verify_live_terminal_evidence_result(result)

    if not result.matched or result.evidence is None:
        return ()

    evidence = result.evidence

    asset_label = {
        "bitcoin": "Bitcoin",
        "ethereum": "Ethereum",
        "solana": "Solana",
    }.get(
        evidence.asset,
        evidence.asset.title(),
    )

    timestamp = (
        evidence.observed_at
        if evidence.observed_at
        else "timestamp unavailable in source row"
    )

    return (
        "=" * 64,
        "Oracle Live Evidence — FACTUAL READ-ONLY",
        f"ASSET: {asset_label}",
        f"PRICE: ${evidence.price:,.8f}".rstrip("0").rstrip("."),
        f"OBSERVED AT: {timestamp}",
        f"SOURCE TABLE: {evidence.source_table}",
        f"SOURCE FIELD: {evidence.source_column}",
        f"EVIDENCE ID: {evidence.source_identity}",
        f"EVIDENCE HASH: {evidence.evidence_hash}",
        "MODE: READ-ONLY | NO TRADE AUTHORIZATION",
        "=" * 64,
    )

# BEGIN OI-006 LIVE OBSERVATION FALLBACK
_int_oracle_live_001_database_reader = read_live_price_evidence

def read_live_price_evidence(repository_root, query):
    existing = _int_oracle_live_001_database_reader(repository_root, query)
    if existing.matched:
        return existing

    from qseries_v2.observation_intelligence.oi_006_live_observation_registry import query_factual_live_price

    try:
        observation = query_factual_live_price(query)
    except Exception:
        return existing

    if observation is None:
        return existing

    try:
        price = float(observation.facts.get("price"))
    except (TypeError, ValueError):
        return existing

    evidence_body = {
        "query": str(query),
        "asset": {"BTC":"bitcoin","ETH":"ethereum","SOL":"solana"}.get(
            observation.subject.upper(),
            observation.subject.lower(),
        ),
        "source_table": "oi_006.live_observation",
        "source_column": "facts.price",
        "source_identity": observation.canonical_observation_id,
        "price": price,
        "observed_at": observation.observed_at.isoformat(),
        "source_record": {
            "canonical_observation_id": observation.canonical_observation_id,
            "provider": observation.provider,
            "adapter_id": observation.adapter_id,
            "subject": observation.subject,
            "observation_type": observation.observation_type,
            "facts": dict(observation.facts),
            "metadata": dict(observation.metadata),
            "canonical_observation_hash": observation.canonical_observation_hash,
        },
        "database_read_performed": existing.database_read_performed,
        "read_only": True,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
    }

    evidence = LiveTerminalEvidence(
        **evidence_body,
        evidence_hash=_stable_hash(evidence_body),
    )

    body = {
        "query": str(query),
        "matched": True,
        "evidence": evidence,
        "reason": "oi_006_live_observation_found",
        "database_read_performed": existing.database_read_performed,
        "read_only": True,
        "execution_allowed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
    }

    return LiveTerminalEvidenceResult(
        **body,
        result_hash=_stable_hash(body),
    )
# END OI-006 LIVE OBSERVATION FALLBACK
