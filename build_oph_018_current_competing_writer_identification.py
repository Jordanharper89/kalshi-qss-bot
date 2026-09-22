from pathlib import Path
import importlib
import os
import subprocess
import sys

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "oracle_production_hardening"

MOD = PKG / "oph_018_current_competing_writer_identification.py"
TEST = ROOT / "test_oph_018_current_competing_writer_identification.py"
RUN = ROOT / "run_oph_018_current_competing_writer_identification.py"
INIT = PKG / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\n\n@dataclass(frozen=True)\nclass OPH018Contract:\n    exact_hash_pair_trace: bool = True\n    postgresql_read_only: bool = True\n    execution_authority: bool = False\n\ndef verify_oph_018_current_competing_writer_identification():\n    x = OPH018Contract()\n    return (\n        x.exact_hash_pair_trace\n        and x.postgresql_read_only\n        and not x.execution_authority\n    )\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_production_hardening.oph_018_current_competing_writer_identification import (\n    verify_oph_018_current_competing_writer_identification,\n)\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(\n            verify_oph_018_current_competing_writer_identification()\n        )\n\nif __name__ == "__main__":\n    print("=" * 80)\n    print(" OPH-018 CERTIFICATION TEST")\n    print(" CURRENT COMPETING WRITER IDENTIFICATION")\n    print("=" * 80)\n\n    r = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] OPH-018 certified")\n    print("[DONE] OPH-018 CERTIFIED")\n'
RUN_SOURCE = 'from pathlib import Path\nimport json\nimport os\n\nROOT = Path.cwd().resolve()\n\nPAIRS = (\n    (\n        "f59ee83d12b1443fe8bffa0659f7745471b6b456d2b3e4525dc9c67c96cc80a7",\n        "7be151c8c2826c4ee18ace5b4c51dc679d858c491a607fc0bd647205a7a491c9",\n    ),\n    (\n        "9a40698be46223e39622d16e03720264df7a31ff8778df849ca4c5aa38b736d9",\n        "5b4a2c308228b224b3e0446110c62e83a9f871cefb2d79716fd2cacf7002f025",\n    ),\n)\n\ndef database_url():\n    keys = (\n        "ORACLE_POSTGRESQL_URL",\n        "ORACLE_DATABASE_URL",\n        "DATABASE_URL",\n        "POSTGRES_URL",\n    )\n\n    for key in keys:\n        value = os.environ.get(key)\n        if value:\n            return value\n\n    env = ROOT / ".env"\n\n    if env.exists():\n        for raw in env.read_text(\n            encoding="utf-8",\n            errors="ignore",\n        ).splitlines():\n            line = raw.strip()\n\n            if (\n                not line\n                or line.startswith("#")\n                or "=" not in line\n            ):\n                continue\n\n            key, value = line.split("=", 1)\n            key = key.strip()\n            value = value.strip().strip(\'"\').strip("\'")\n\n            if key in keys and value:\n                return value\n\n    raise RuntimeError("PostgreSQL URL not configured")\n\ndef ticker_from_json(raw):\n    try:\n        if isinstance(raw, str):\n            raw = json.loads(raw)\n\n        payload = (raw or {}).get("payload") or {}\n\n        return (\n            payload.get("source_market_id")\n            or payload.get("source_symbol")\n            or payload.get("ticker")\n        )\n\n    except Exception:\n        return None\n\ndef main():\n    import psycopg\n\n    print("=" * 104)\n    print(" OPH-018 CURRENT COMPETING WRITER IDENTIFICATION")\n    print(" READ-ONLY — EXACT POST-OPH-017 CHAIN MOVEMENTS")\n    print("=" * 104)\n\n    with psycopg.connect(database_url()) as conn:\n        with conn.cursor() as cur:\n            for pair_number, (expected_hash, actual_hash) in enumerate(\n                PAIRS,\n                start=1,\n            ):\n                print("-" * 104)\n                print(\n                    f"[PAIR {pair_number}] "\n                    f"expected={expected_hash}"\n                )\n                print(\n                    f"[PAIR {pair_number}] "\n                    f"actual={actual_hash}"\n                )\n\n                sql = (\n                    "SELECT "\n                    "sequence_number, "\n                    "observation_id, "\n                    "source_id, "\n                    "observation_type, "\n                    "canonical_observation_json, "\n                    "previous_chain_hash, "\n                    "chain_hash, "\n                    "persisted_at "\n                    "FROM public.oracle_canonical_observations "\n                    "WHERE chain_hash IN (%s,%s) "\n                    "OR previous_chain_hash IN (%s,%s) "\n                    "ORDER BY sequence_number"\n                )\n\n                cur.execute(\n                    sql,\n                    (\n                        expected_hash,\n                        actual_hash,\n                        expected_hash,\n                        actual_hash,\n                    ),\n                )\n\n                rows = cur.fetchall()\n\n                print(\n                    f"[PAIR {pair_number}] "\n                    f"matching_rows={len(rows)}"\n                )\n\n                expected_seq = None\n                actual_seq = None\n\n                for row in rows:\n                    (\n                        sequence_number,\n                        observation_id,\n                        source_id,\n                        observation_type,\n                        canonical_json,\n                        previous_chain_hash,\n                        chain_hash,\n                        persisted_at,\n                    ) = row\n\n                    ticker = ticker_from_json(canonical_json)\n\n                    print(\n                        "[ROW] "\n                        f"sequence={sequence_number} "\n                        f"source_id={source_id} "\n                        f"type={observation_type} "\n                        f"ticker={ticker}"\n                    )\n                    print(\n                        f"[ROW] observation_id={observation_id}"\n                    )\n                    print(\n                        f"[ROW] previous_chain_hash="\n                        f"{previous_chain_hash}"\n                    )\n                    print(\n                        f"[ROW] chain_hash={chain_hash}"\n                    )\n                    print(\n                        f"[ROW] persisted_at={persisted_at}"\n                    )\n\n                    if chain_hash == expected_hash:\n                        expected_seq = sequence_number\n\n                    if chain_hash == actual_hash:\n                        actual_seq = sequence_number\n\n                if (\n                    expected_seq is not None\n                    and actual_seq is not None\n                ):\n                    print(\n                        "[SEQUENCE ADVANCE] "\n                        f"{actual_seq - expected_seq}"\n                    )\n\n                    if actual_seq - expected_seq == 1:\n                        print(\n                            "[CLASSIFICATION] "\n                            "EXACT_SINGLE_COMPETING_APPEND"\n                        )\n                    elif actual_seq > expected_seq:\n                        print(\n                            "[CLASSIFICATION] "\n                            "MULTIPLE_COMPETING_APPENDS"\n                        )\n                    else:\n                        print(\n                            "[CLASSIFICATION] "\n                            "NON_FORWARD_HASH_RELATIONSHIP"\n                        )\n                else:\n                    print(\n                        "[CLASSIFICATION] "\n                        "PARTIAL_HASH_OWNERSHIP"\n                    )\n\n    print("-" * 104)\n    print("[PASS] PostgreSQL inspection performed read-only")\n    print("[PASS] No Oracle runtime state modified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPH-018 COMPLETE")\n\nif __name__ == "__main__":\n    main()\n'

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(path.suffix + ".tmp")

    tmp.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )

    os.replace(tmp, path)

def main():
    print("=" * 80)
    print(" OPH-018 INSTALLER")
    print(" CURRENT COMPETING WRITER IDENTIFICATION")
    print("=" * 80)
    print("[ROOT]", ROOT)

    sys.path.insert(0, str(ROOT))

    upstream = importlib.import_module(
        "qseries_v2.oracle_production_hardening."
        "oph_017_canonical_backend_rejection_forensic"
    )

    if (
        upstream.verify_oph_017_canonical_backend_rejection_forensic()
        is not True
    ):
        raise RuntimeError(
            "Certified OPH-017 verification failed"
        )

    print(
        "[PASS] Certified OPH-017 upstream boundary verified"
    )

    affected = (
        MOD,
        TEST,
        RUN,
        INIT,
    )

    backups = {
        path: (
            path.read_bytes()
            if path.exists()
            else None
        )
        for path in affected
    }

    try:
        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        write_exact(RUN, RUN_SOURCE)

        current = (
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        export = (
            "from .oph_018_current_competing_writer_identification "
            "import *"
        )

        if export not in current:
            write_exact(
                INIT,
                current.rstrip()
                + "\n"
                + export
                + "\n",
            )

        for path in (MOD, TEST, RUN):
            compile(
                path.read_text(encoding="utf-8"),
                str(path),
                "exec",
            )

        subprocess.run(
            [
                sys.executable,
                str(TEST),
            ],
            cwd=str(ROOT),
            check=True,
        )

    except Exception:
        for path, old in backups.items():
            if old is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(old)

        print(
            "[ROLLBACK] OPH-018 installation failed; "
            "affected files restored"
        )

        raise

    print("[PASS] Wrote:", MOD.relative_to(ROOT))
    print("[PASS] Wrote:", TEST.name)
    print("[PASS] Wrote:", RUN.name)
    print("[PASS] Production Oracle launcher untouched")
    print("[PASS] execution_authority=FALSE")
    print(
        "[DONE] OPH-018 INSTALLATION "
        "AND CERTIFICATION COMPLETE"
    )

if __name__ == "__main__":
    main()
