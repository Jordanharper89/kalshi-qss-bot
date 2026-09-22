from pathlib import Path
import json
import os

ROOT = Path.cwd().resolve()

PAIRS = (
    (
        "f59ee83d12b1443fe8bffa0659f7745471b6b456d2b3e4525dc9c67c96cc80a7",
        "7be151c8c2826c4ee18ace5b4c51dc679d858c491a607fc0bd647205a7a491c9",
    ),
    (
        "9a40698be46223e39622d16e03720264df7a31ff8778df849ca4c5aa38b736d9",
        "5b4a2c308228b224b3e0446110c62e83a9f871cefb2d79716fd2cacf7002f025",
    ),
)

def database_url():
    keys = (
        "ORACLE_POSTGRESQL_URL",
        "ORACLE_DATABASE_URL",
        "DATABASE_URL",
        "POSTGRES_URL",
    )

    for key in keys:
        value = os.environ.get(key)
        if value:
            return value

    env = ROOT / ".env"

    if env.exists():
        for raw in env.read_text(
            encoding="utf-8",
            errors="ignore",
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
            value = value.strip().strip('"').strip("'")

            if key in keys and value:
                return value

    raise RuntimeError("PostgreSQL URL not configured")

def ticker_from_json(raw):
    try:
        if isinstance(raw, str):
            raw = json.loads(raw)

        payload = (raw or {}).get("payload") or {}

        return (
            payload.get("source_market_id")
            or payload.get("source_symbol")
            or payload.get("ticker")
        )

    except Exception:
        return None

def main():
    import psycopg

    print("=" * 104)
    print(" OPH-018 CURRENT COMPETING WRITER IDENTIFICATION")
    print(" READ-ONLY — EXACT POST-OPH-017 CHAIN MOVEMENTS")
    print("=" * 104)

    with psycopg.connect(database_url()) as conn:
        with conn.cursor() as cur:
            for pair_number, (expected_hash, actual_hash) in enumerate(
                PAIRS,
                start=1,
            ):
                print("-" * 104)
                print(
                    f"[PAIR {pair_number}] "
                    f"expected={expected_hash}"
                )
                print(
                    f"[PAIR {pair_number}] "
                    f"actual={actual_hash}"
                )

                sql = (
                    "SELECT "
                    "sequence_number, "
                    "observation_id, "
                    "source_id, "
                    "observation_type, "
                    "canonical_observation_json, "
                    "previous_chain_hash, "
                    "chain_hash, "
                    "persisted_at "
                    "FROM public.oracle_canonical_observations "
                    "WHERE chain_hash IN (%s,%s) "
                    "OR previous_chain_hash IN (%s,%s) "
                    "ORDER BY sequence_number"
                )

                cur.execute(
                    sql,
                    (
                        expected_hash,
                        actual_hash,
                        expected_hash,
                        actual_hash,
                    ),
                )

                rows = cur.fetchall()

                print(
                    f"[PAIR {pair_number}] "
                    f"matching_rows={len(rows)}"
                )

                expected_seq = None
                actual_seq = None

                for row in rows:
                    (
                        sequence_number,
                        observation_id,
                        source_id,
                        observation_type,
                        canonical_json,
                        previous_chain_hash,
                        chain_hash,
                        persisted_at,
                    ) = row

                    ticker = ticker_from_json(canonical_json)

                    print(
                        "[ROW] "
                        f"sequence={sequence_number} "
                        f"source_id={source_id} "
                        f"type={observation_type} "
                        f"ticker={ticker}"
                    )
                    print(
                        f"[ROW] observation_id={observation_id}"
                    )
                    print(
                        f"[ROW] previous_chain_hash="
                        f"{previous_chain_hash}"
                    )
                    print(
                        f"[ROW] chain_hash={chain_hash}"
                    )
                    print(
                        f"[ROW] persisted_at={persisted_at}"
                    )

                    if chain_hash == expected_hash:
                        expected_seq = sequence_number

                    if chain_hash == actual_hash:
                        actual_seq = sequence_number

                if (
                    expected_seq is not None
                    and actual_seq is not None
                ):
                    print(
                        "[SEQUENCE ADVANCE] "
                        f"{actual_seq - expected_seq}"
                    )

                    if actual_seq - expected_seq == 1:
                        print(
                            "[CLASSIFICATION] "
                            "EXACT_SINGLE_COMPETING_APPEND"
                        )
                    elif actual_seq > expected_seq:
                        print(
                            "[CLASSIFICATION] "
                            "MULTIPLE_COMPETING_APPENDS"
                        )
                    else:
                        print(
                            "[CLASSIFICATION] "
                            "NON_FORWARD_HASH_RELATIONSHIP"
                        )
                else:
                    print(
                        "[CLASSIFICATION] "
                        "PARTIAL_HASH_OWNERSHIP"
                    )

    print("-" * 104)
    print("[PASS] PostgreSQL inspection performed read-only")
    print("[PASS] No Oracle runtime state modified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-018 COMPLETE")

if __name__ == "__main__":
    main()
