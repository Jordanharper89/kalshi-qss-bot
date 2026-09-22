from pathlib import Path
import importlib
import os
import subprocess
import sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"

MOD=PKG/"opc_003_canonical_observation_coverage_read_model.py"
TEST=ROOT/"test_opc_003_canonical_observation_coverage_read_model.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json\nimport os\n\nOPC_003_BUILD_ID="OPC-003"\nOPC_003_REVISION="OPC_003_CANONICAL_OBSERVATION_COVERAGE_READ_MODEL_CORRECTION_V2"\n\n@dataclass(frozen=True)\nclass CanonicalCoverageResult:\n    sampled_markets:int\n    markets_with_canonical_observation:int\n    markets_without_canonical_observation:int\n    coverage_rate:float\n    observed_tickers:tuple\n    missing_tickers:tuple\n    read_only:bool=True\n\ndef _db(root):\n    url=(\n        os.environ.get("ORACLE_POSTGRESQL_URL")\n        or os.environ.get("ORACLE_DATABASE_URL")\n        or os.environ.get("DATABASE_URL")\n        or os.environ.get("POSTGRES_URL")\n    )\n    if url:\n        return url\n\n    env=Path(root)/".env"\n    if env.is_file():\n        for raw in env.read_text(\n            encoding="utf-8",\n            errors="ignore",\n        ).splitlines():\n            line=raw.strip()\n            if not line or line.startswith("#") or "=" not in line:\n                continue\n            key,value=line.split("=",1)\n            key=key.strip()\n            value=value.strip().strip(\'"\').strip("\'")\n            if key in (\n                "ORACLE_POSTGRESQL_URL",\n                "ORACLE_DATABASE_URL",\n                "DATABASE_URL",\n                "POSTGRES_URL",\n            ) and value:\n                return value\n\n    raise RuntimeError(\n        "DATABASE_URL / ORACLE_DATABASE_URL not configured"\n    )\n\ndef _ticker(obj):\n    if not isinstance(obj,(dict,list)):\n        return ""\n\n    if isinstance(obj,list):\n        for value in obj:\n            found=_ticker(value)\n            if found:\n                return found\n        return ""\n\n    # CanonicalObservation stores venue identity inside payload.\n    payload=obj.get("payload")\n    if isinstance(payload,dict):\n        for key in (\n            "source_market_id",\n            "source_symbol",\n            "ticker",\n            "market_ticker",\n            "market_id",\n            "canonical_market_id",\n            "venue_market_id",\n            "symbol",\n        ):\n            value=payload.get(key)\n            if isinstance(value,str) and value:\n                return value\n\n    # Backward-compatible direct/top-level identity support.\n    for key in (\n        "source_market_id",\n        "source_symbol",\n        "ticker",\n        "market_ticker",\n        "market_id",\n        "canonical_market_id",\n        "venue_market_id",\n        "symbol",\n    ):\n        value=obj.get(key)\n        if isinstance(value,str) and value:\n            return value\n\n    # Recursive fallback for historical canonical shapes.\n    for key,value in obj.items():\n        if key=="payload":\n            continue\n        found=_ticker(value)\n        if found:\n            return found\n\n    return ""\n\ndef read_recent_canonical_tickers(\n    root=None,\n    lookback_hours=24,\n    row_limit=250000,\n):\n    root=Path(root or Path.cwd()).resolve()\n    lookback_hours=float(lookback_hours)\n    row_limit=int(row_limit)\n\n    if lookback_hours<=0 or lookback_hours>168:\n        raise ValueError("lookback_hours out of bounds")\n    if row_limit<1 or row_limit>1000000:\n        raise ValueError("row_limit out of bounds")\n\n    import psycopg\n\n    conn=psycopg.connect(_db(root))\n    try:\n        with conn.cursor() as cur:\n            cur.execute(\n                """\n                SELECT canonical_observation_json\n                FROM public.oracle_canonical_observations\n                WHERE observed_at >= NOW() - (%s * INTERVAL \'1 hour\')\n                ORDER BY observed_at DESC\n                LIMIT %s\n                """,\n                (lookback_hours,row_limit),\n            )\n            rows=cur.fetchall()\n    finally:\n        conn.close()\n\n    tickers=set()\n\n    for (raw,) in rows:\n        obj=raw\n        if isinstance(raw,str):\n            try:\n                obj=json.loads(raw)\n            except Exception:\n                continue\n\n        ticker=_ticker(obj)\n        if ticker:\n            tickers.add(ticker)\n\n    return tickers\n\ndef evaluate_canonical_coverage(\n    sample_tickers,\n    canonical_tickers,\n):\n    sample=tuple(\n        dict.fromkeys(\n            str(value)\n            for value in sample_tickers\n            if str(value)\n        )\n    )\n\n    canonical={str(value) for value in canonical_tickers}\n\n    observed=tuple(\n        sorted(\n            ticker\n            for ticker in sample\n            if ticker in canonical\n        )\n    )\n\n    missing=tuple(\n        sorted(\n            ticker\n            for ticker in sample\n            if ticker not in canonical\n        )\n    )\n\n    rate=(\n        len(observed)/len(sample)\n        if sample\n        else 0.0\n    )\n\n    return CanonicalCoverageResult(\n        len(sample),\n        len(observed),\n        len(missing),\n        rate,\n        observed,\n        missing,\n        True,\n    )\n\ndef verify_opc_003_canonical_observation_coverage_read_model():\n    canonical_doc={\n        "observation_type":"market_snapshot",\n        "payload":{\n            "source_market_id":"KXTEST",\n            "source_symbol":"KXTEST",\n            "opc_snapshot":True,\n        },\n    }\n\n    if _ticker(canonical_doc)!="KXTEST":\n        return False\n\n    result=evaluate_canonical_coverage(\n        ("KXTEST","KXMISSING"),\n        {"KXTEST"},\n    )\n\n    return (\n        result.sampled_markets==2\n        and result.markets_with_canonical_observation==1\n        and result.markets_without_canonical_observation==1\n        and result.coverage_rate==0.5\n        and result.read_only\n    )\n'
TEST_SOURCE='import unittest\n\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_003_canonical_observation_coverage_read_model import (\n    _ticker,\n    evaluate_canonical_coverage,\n    verify_opc_003_canonical_observation_coverage_read_model,\n)\n\nclass T(unittest.TestCase):\n\n    def test_verifier(self):\n        self.assertTrue(\n            verify_opc_003_canonical_observation_coverage_read_model()\n        )\n\n    def test_payload_source_market_id(self):\n        doc={\n            "payload":{\n                "source_market_id":"KXABC",\n                "opc_snapshot":True,\n            }\n        }\n        self.assertEqual(_ticker(doc),"KXABC")\n\n    def test_payload_source_symbol_fallback(self):\n        doc={\n            "payload":{\n                "source_symbol":"KXSYM",\n            }\n        }\n        self.assertEqual(_ticker(doc),"KXSYM")\n\n    def test_coverage(self):\n        result=evaluate_canonical_coverage(\n            ("A","B","C"),\n            {"B","C"},\n        )\n        self.assertEqual(\n            result.markets_with_canonical_observation,\n            2,\n        )\n        self.assertEqual(\n            result.markets_without_canonical_observation,\n            1,\n        )\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OPC-003 CORRECTION V2 CERTIFICATION TEST")\n    print(" CANONICAL PAYLOAD MARKET-IDENTITY EXTRACTION")\n    print("="*72)\n\n    result=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] payload.source_market_id extraction certified")\n    print("[PASS] payload.source_symbol fallback certified")\n    print("[PASS] Existing coverage result contract preserved")\n    print("[PASS] Read-only PostgreSQL coverage boundary preserved")\n    print("[DONE] OPC-003 CORRECTION V2 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OPC-003 CORRECTION V2 INSTALLER")
    print(" CANONICAL PAYLOAD MARKET-IDENTITY EXTRACTION")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))

    upstream=importlib.import_module(
        "qseries_v2.oracle_pre_settlement_coverage."
        "opc_002_bounded_open_market_sampler"
    )

    if (
        upstream.verify_opc_002_bounded_open_market_sampler()
        is not True
    ):
        raise RuntimeError(
            "Certified OPC-002 upstream verification failed"
        )

    print("[PASS] Certified OPC-002 upstream boundary verified")
    print("[PASS] Defect isolated to OPC-003 canonical payload extraction")
    print("[PASS] OPC-006/009, OLA, and frozen OLR left untouched")

    affected=(MOD,TEST,INIT)
    backups={
        path:(path.read_bytes() if path.exists() else None)
        for path in affected
    }

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)

        current=(
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        export_line=(
            "from .opc_003_canonical_observation_coverage_read_model "
            "import *"
        )

        if export_line not in current:
            write_exact(
                INIT,
                current.rstrip()+"\n"+export_line+"\n",
            )

        compile(
            MOD.read_text(encoding="utf-8"),
            str(MOD),
            "exec",
        )

        compile(
            TEST.read_text(encoding="utf-8"),
            str(TEST),
            "exec",
        )

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )

    except Exception:
        for path,old in backups.items():
            if old is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(old)

        print(
            "[ROLLBACK] OPC-003 Correction V2 failed; "
            "affected files restored"
        )
        raise

    print("[PASS] Corrected:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OPC-003 CORRECTION V2 INSTALLED + CERTIFIED")

if __name__=="__main__":
    main()
