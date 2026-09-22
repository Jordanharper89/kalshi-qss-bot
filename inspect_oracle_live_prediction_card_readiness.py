from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent
RUNTIME_ROOT = ROOT / "runtime" / "oracle_live_shadow"
ENV_PATH = ROOT / ".env"

MAX_JSON_FILES = 12
MAX_TABLES = 20
MAX_ROWS_PER_TABLE = 3
MAX_VALUE_LENGTH = 220

KEYWORDS = (
    "observation",
    "market",
    "opportunity",
    "candidate",
    "ranking",
    "priority",
    "research",
    "analytics",
    "prediction",
    "card",
    "probability",
    "confidence",
    "calibration",
    "edge",
    "price",
)

SENSITIVE_KEYS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
)


def heading(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
            os.environ.setdefault(key, value)
    return values


def redact_url(value: str) -> str:
    try:
        parts = urlsplit(value)
        if not parts.scheme or not parts.netloc:
            return "<configured>"
        hostname = parts.hostname or ""
        port = f":{parts.port}" if parts.port else ""
        username = parts.username or ""
        auth = f"{username}:***@" if username else ""
        netloc = f"{auth}{hostname}{port}"
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        return "<configured>"


def safe_value(value: Any, key: str = "") -> Any:
    if any(marker in key.lower() for marker in SENSITIVE_KEYS):
        return "<redacted>"

    if isinstance(value, dict):
        return {
            str(k): safe_value(v, str(k))
            for k, v in list(value.items())[:30]
        }
    if isinstance(value, list):
        return [safe_value(item) for item in value[:10]]
    if isinstance(value, tuple):
        return tuple(safe_value(item) for item in value[:10])
    if isinstance(value, bytes):
        return f"<{len(value)} bytes>"

    text = str(value)
    if "://" in text and ("postgres" in text.lower() or "password" in text.lower()):
        return redact_url(text)
    if len(text) > MAX_VALUE_LENGTH:
        return text[:MAX_VALUE_LENGTH] + "..."
    return value


def age_seconds(path: Path) -> float:
    return max(0.0, datetime.now(timezone.utc).timestamp() - path.stat().st_mtime)


def human_age(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds / 60:.1f}m"
    if seconds < 86400:
        return f"{seconds / 3600:.1f}h"
    return f"{seconds / 86400:.1f}d"


def iter_recent_json_files(root: Path) -> list[Path]:
    if not root.exists():
        return []

    files: list[Path] = []
    for path in root.rglob("*.json"):
        try:
            if path.is_file():
                files.append(path)
        except OSError:
            continue

    files.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return files[:MAX_JSON_FILES]


def summarize_json(path: Path) -> tuple[bool, set[str]]:
    keys: set[str] = set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        print(f"[WARN] Could not parse {path.relative_to(ROOT)}: {exc}")
        return False, keys

    def collect(value: Any, depth: int = 0) -> None:
        if depth > 4:
            return
        if isinstance(value, dict):
            for key, item in list(value.items())[:80]:
                keys.add(str(key).lower())
                collect(item, depth + 1)
        elif isinstance(value, list):
            for item in value[:20]:
                collect(item, depth + 1)

    collect(payload)

    print(f"[FILE] {path.relative_to(ROOT)}")
    print(f"       modified={datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat()}")
    print(f"       age={human_age(age_seconds(path))} size={path.stat().st_size:,} bytes")

    if isinstance(payload, dict):
        sample = {k: safe_value(v, str(k)) for k, v in list(payload.items())[:12]}
        print(f"       top-level keys={list(payload.keys())[:20]}")
        print(f"       sample={json.dumps(sample, ensure_ascii=False, default=str)}")
    elif isinstance(payload, list):
        print(f"       list_length={len(payload)}")
        if payload:
            print(f"       first_item={json.dumps(safe_value(payload[0]), ensure_ascii=False, default=str)}")
    else:
        print(f"       value={safe_value(payload)}")

    return True, keys


def import_db_driver():
    try:
        import psycopg  # type: ignore
        return "psycopg", psycopg
    except Exception:
        pass

    try:
        import psycopg2  # type: ignore
        return "psycopg2", psycopg2
    except Exception:
        return None, None


def database_dsn(env: dict[str, str]) -> str | None:
    for key in (
        "DATABASE_URL",
        "POSTGRES_URL",
        "POSTGRESQL_URL",
        "ORACLE_DATABASE_URL",
    ):
        value = env.get(key) or os.environ.get(key)
        if value:
            return value
    return None


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def read_database(env: dict[str, str]) -> tuple[bool, set[str], set[str]]:
    driver_name, driver = import_db_driver()
    if not driver:
        print("[WARN] Neither psycopg nor psycopg2 is installed in this environment.")
        return False, set(), set()

    dsn = database_dsn(env)
    if not dsn:
        print("[WARN] No DATABASE_URL/POSTGRES_URL/POSTGRESQL_URL found.")
        return False, set(), set()

    print(f"[OK] Database driver: {driver_name}")
    print(f"[OK] Database target: {redact_url(dsn)}")

    conn = None
    discovered_columns: set[str] = set()
    discovered_tables: set[str] = set()

    try:
        conn = driver.connect(dsn)
        conn.autocommit = False

        cur = conn.cursor()
        cur.execute("SET TRANSACTION READ ONLY")
        cur.execute("SET LOCAL statement_timeout = '12000ms'")

        cur.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
            """
        )
        all_tables = [(str(schema), str(table)) for schema, table in cur.fetchall()]
        discovered_tables = {table.lower() for _, table in all_tables}

        candidates = [
            (schema, table)
            for schema, table in all_tables
            if any(keyword in table.lower() for keyword in KEYWORDS)
        ][:MAX_TABLES]

        print(f"[OK] Read-only transaction established")
        print(f"[INFO] User tables discovered: {len(all_tables)}")
        print(f"[INFO] Relevant candidate tables: {len(candidates)}")

        if not candidates:
            print("[WARN] No table names matched prediction-card keywords.")

        for schema, table in candidates:
            print()
            print(f"[TABLE] {schema}.{table}")
            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                (schema, table),
            )
            columns = [(str(name), str(dtype)) for name, dtype in cur.fetchall()]
            discovered_columns.update(name.lower() for name, _ in columns)
            print(f"        columns={[name for name, _ in columns][:40]}")

            try:
                cur.execute(
                    f"SELECT COUNT(*) FROM {quote_ident(schema)}.{quote_ident(table)}"
                )
                count = int(cur.fetchone()[0])
                print(f"        row_count={count:,}")
            except Exception as exc:
                conn.rollback()
                cur = conn.cursor()
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute("SET LOCAL statement_timeout = '12000ms'")
                print(f"        row_count=<unavailable: {exc}>")
                continue

            if not columns or count == 0:
                continue

            column_names = [name for name, _ in columns]
            order_candidates = [
                name for name in column_names
                if name.lower() in (
                    "created_at",
                    "observed_at",
                    "recorded_at",
                    "updated_at",
                    "persisted_at",
                    "timestamp",
                    "ts",
                    "id",
                )
            ]
            order_clause = (
                f" ORDER BY {quote_ident(order_candidates[0])} DESC"
                if order_candidates else ""
            )

            try:
                cur.execute(
                    f"SELECT * FROM {quote_ident(schema)}.{quote_ident(table)}"
                    f"{order_clause} LIMIT {MAX_ROWS_PER_TABLE}"
                )
                rows = cur.fetchall()
                for index, row in enumerate(rows, start=1):
                    record = {
                        column_names[position]: safe_value(value, column_names[position])
                        for position, value in enumerate(row)
                    }
                    print(
                        f"        row_{index}="
                        + json.dumps(record, ensure_ascii=False, default=str)
                    )
            except Exception as exc:
                conn.rollback()
                cur = conn.cursor()
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute("SET LOCAL statement_timeout = '12000ms'")
                print(f"        sample_rows=<unavailable: {exc}>")

        conn.rollback()
        print()
        print("[PASS] Database inspection completed with rollback; no writes committed.")
        return True, discovered_tables, discovered_columns

    except Exception as exc:
        print(f"[FAIL] PostgreSQL read-only inspection failed: {exc}")
        try:
            if conn is not None:
                conn.rollback()
        except Exception:
            pass
        return False, discovered_tables, discovered_columns
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass


def inspect_code() -> set[str]:
    roots = [
        ROOT / "qseries_v2" / "oracle_intelligence",
        ROOT / "qseries_v2" / "oracle_operator",
        ROOT / "qseries_v2" / "oracle_operator_runtime",
    ]
    matches: list[Path] = []
    found_tokens: set[str] = set()

    for code_root in roots:
        if not code_root.exists():
            continue
        for path in code_root.rglob("*.py"):
            lowered = path.name.lower()
            if any(keyword in lowered for keyword in KEYWORDS):
                matches.append(path)
                found_tokens.update(
                    keyword for keyword in KEYWORDS if keyword in lowered
                )

    matches.sort()
    for path in matches[:80]:
        print(f"[MODULE] {path.relative_to(ROOT)}")

    if len(matches) > 80:
        print(f"[INFO] Additional matching modules omitted: {len(matches) - 80}")

    print(f"[INFO] Matching modules found: {len(matches)}")
    return found_tokens


def main() -> int:
    print("=" * 72)
    print(" ORACLE LIVE PREDICTION CARD READINESS INSPECTION")
    print(" READ-ONLY / NO EXECUTION / NO DATABASE MUTATION")
    print("=" * 72)
    print(f"[INFO] Repository root: {ROOT}")

    env = load_env(ENV_PATH)
    print(f"[INFO] Environment file present: {ENV_PATH.exists()}")
    print(f"[INFO] Database URL present: {database_dsn(env) is not None}")

    heading("1. LIVE RUNTIME ARTIFACTS")
    json_files = iter_recent_json_files(RUNTIME_ROOT)
    runtime_keys: set[str] = set()
    parsed_count = 0

    if not json_files:
        print(f"[WARN] No JSON artifacts found under {RUNTIME_ROOT}")
    else:
        for path in json_files:
            parsed, keys = summarize_json(path)
            parsed_count += int(parsed)
            runtime_keys.update(keys)

    freshest_age = age_seconds(json_files[0]) if json_files else None
    runtime_fresh = freshest_age is not None and freshest_age <= 120

    heading("2. POSTGRESQL LIVE DATA")
    db_ok, db_tables, db_columns = read_database(env)

    heading("3. INSTALLED ANALYTICS AND OPERATOR MODULES")
    code_tokens = inspect_code()

    heading("4. READINESS VERDICT")
    evidence_tokens = runtime_keys | db_tables | db_columns | code_tokens

    acquisition_evidence = (
        runtime_fresh
        or any("observation" in token or "market" in token for token in evidence_tokens)
    )
    analytics_evidence = any(
        marker in token
        for token in evidence_tokens
        for marker in ("opportunity", "ranking", "analytics", "candidate", "research")
    )
    card_fields_evidence = all(
        any(marker in token for token in evidence_tokens)
        for marker in ("probability", "confidence")
    ) and any(
        marker in token for token in evidence_tokens
        for marker in ("price", "edge")
    )
    presentation_evidence = any(
        marker in token for token in evidence_tokens
        for marker in ("presentation", "console", "card")
    )

    print(f"[{'PASS' if runtime_fresh else 'WARN'}] Fresh runtime JSON within 120 seconds: {runtime_fresh}")
    print(f"[{'PASS' if parsed_count else 'WARN'}] Parseable runtime JSON files: {parsed_count}")
    print(f"[{'PASS' if db_ok else 'WARN'}] PostgreSQL read-only inspection: {db_ok}")
    print(f"[{'PASS' if acquisition_evidence else 'WARN'}] Live market/acquisition evidence: {acquisition_evidence}")
    print(f"[{'PASS' if analytics_evidence else 'WARN'}] Analytics/ranking evidence: {analytics_evidence}")
    print(f"[{'PASS' if card_fields_evidence else 'WARN'}] Probability/confidence/price-or-edge fields: {card_fields_evidence}")
    print(f"[{'PASS' if presentation_evidence else 'WARN'}] Presentation/card surface evidence: {presentation_evidence}")

    print()
    if acquisition_evidence and analytics_evidence and card_fields_evidence and presentation_evidence:
        print("[READY] Repository appears to contain the ingredients for a real live prediction card.")
        print("[NEXT] Use the discovered canonical tables/contracts to build the card runner.")
    elif acquisition_evidence and analytics_evidence:
        print("[PARTIAL] Live acquisition and analytics appear present, but the complete card")
        print("          field set or presentation surface was not verified.")
    elif acquisition_evidence:
        print("[PARTIAL] Live acquisition appears active, but current ranked/card-ready")
        print("          analytics were not verified.")
    else:
        print("[NOT READY] This inspection did not verify a live card-producing data path.")

    print()
    print("[SAFETY] No orders placed.")
    print("[SAFETY] No funds moved.")
    print("[SAFETY] No portfolio state mutated.")
    print("[SAFETY] PostgreSQL transaction rolled back.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
