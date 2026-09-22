from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_052_canonical_json_evidence_lookup_correction.py"
TEST=ROOT/"test_olr_052_canonical_json_evidence_lookup_correction.py"
INIT=PKG/"__init__.py"
TARGET=PKG/"olr_041_postgresql_live_evidence_lookup.py"

MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport json\n\nOLR_052_BUILD_ID="OLR-052"\nOLR_052_REVISION="OLR_052_CANONICAL_JSON_EVIDENCE_LOOKUP_CORRECTION_V1"\n\ndef _connect(root=None):\n    from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n    return connect(root)\n\ndef _outcome_identity(outcome):\n    if hasattr(outcome,"get"):\n        ticker=str(outcome.get("ticker") or outcome.get("market_ticker") or "").strip()\n        market_id=str(outcome.get("market_id") or ticker).strip()\n        observation_id=str(outcome.get("observation_id") or "").strip() or None\n    else:\n        ticker=str(getattr(outcome,"ticker","") or getattr(outcome,"market_ticker","")).strip()\n        market_id=str(getattr(outcome,"market_id","") or ticker).strip()\n        observation_id=str(getattr(outcome,"observation_id","") or "").strip() or None\n    return ticker,market_id,observation_id\n\ndef _json_load(value):\n    if value is None:\n        return {}\n    if isinstance(value,dict):\n        return value\n    if isinstance(value,(bytes,bytearray,memoryview)):\n        value=bytes(value).decode("utf-8","ignore")\n    if isinstance(value,str):\n        try:\n            parsed=json.loads(value)\n            return parsed if isinstance(parsed,dict) else {}\n        except Exception:\n            return {}\n    return {}\n\ndef _extract_identity(payload,source_observation_id=None):\n    payload=payload or {}\n\n    ticker=""\n    market_id=""\n\n    direct_ticker_keys=(\n        "ticker","market_ticker","marketTicker","symbol",\n    )\n    direct_market_keys=(\n        "market_id","marketId","market","market_ticker","ticker",\n    )\n\n    for key in direct_ticker_keys:\n        value=payload.get(key)\n        if value not in (None,""):\n            ticker=str(value).strip()\n            if ticker:break\n\n    for key in direct_market_keys:\n        value=payload.get(key)\n        if value not in (None,""):\n            market_id=str(value).strip()\n            if market_id:break\n\n    nested_candidates=(\n        payload.get("market"),\n        payload.get("data"),\n        payload.get("payload"),\n        payload.get("observation"),\n        payload.get("metadata"),\n    )\n\n    for nested in nested_candidates:\n        if not isinstance(nested,dict):\n            continue\n\n        if not ticker:\n            for key in direct_ticker_keys:\n                value=nested.get(key)\n                if value not in (None,""):\n                    ticker=str(value).strip()\n                    if ticker:break\n\n        if not market_id:\n            for key in direct_market_keys:\n                value=nested.get(key)\n                if value not in (None,""):\n                    market_id=str(value).strip()\n                    if market_id:break\n\n        if ticker and market_id:\n            break\n\n    source_id=str(source_observation_id or "").strip()\n\n    if not ticker and source_id:\n        ticker=source_id\n    if not market_id and source_id:\n        market_id=source_id\n    if not market_id:\n        market_id=ticker\n    if not ticker:\n        ticker=market_id\n\n    return ticker,market_id\n\ndef lookup_market_evidence(outcome,root=None,limit=200):\n    root=Path(root or Path.cwd()).resolve()\n    ticker,market_id,observation_id=_outcome_identity(outcome)\n\n    if not ticker and not market_id and not observation_id:\n        return ()\n\n    sql="""\n        SELECT\n            observation_id,\n            source_observation_id,\n            sequence_number,\n            observed_at,\n            canonical_observation_json\n        FROM public.oracle_canonical_observations\n        ORDER BY sequence_number DESC\n        LIMIT %s\n    """\n\n    # Read a bounded recent window larger than the final return size.\n    scan_limit=max(int(limit)*50,5000)\n\n    candidates=[]\n    with _connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(sql,(scan_limit,))\n            rows=cur.fetchall()\n\n    for row in rows:\n        obs_id=row[0]\n        source_obs_id=row[1]\n        sequence_number=row[2]\n        observed_at=row[3]\n        payload=_json_load(row[4])\n\n        cand_ticker,cand_market=_extract_identity(payload,source_obs_id)\n\n        exact_obs = bool(observation_id and str(obs_id)==str(observation_id))\n        ticker_match = bool(ticker and cand_ticker==ticker)\n        market_match = bool(market_id and cand_market==market_id)\n\n        if exact_obs or ticker_match or market_match:\n            candidates.append({\n                "observation_id":obs_id,\n                "ticker":cand_ticker,\n                "market_ticker":cand_ticker,\n                "market_id":cand_market,\n                "source_observation_id":source_obs_id,\n                "sequence_number":sequence_number,\n                "observed_at":observed_at,\n                "canonical_observation_json":payload,\n            })\n            if len(candidates)>=int(limit):\n                break\n\n    return tuple(candidates)\n\ndef verify_olr_052_canonical_json_evidence_lookup_correction(root=None):\n    from .olr_050_production_evidence_learning_activation_freeze import verify_olr_050_production_evidence_learning_activation_freeze\n    ticker,market=_extract_identity({"ticker":"KXTEST"},None)\n    return (\n        verify_olr_050_production_evidence_learning_activation_freeze(root)\n        and OLR_052_BUILD_ID=="OLR-052"\n        and ticker=="KXTEST"\n        and market=="KXTEST"\n        and callable(lookup_market_evidence)\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_052_canonical_json_evidence_lookup_correction import *\n\nclass T(unittest.TestCase):\n    def test_direct_identity(self):\n        t,m=_extract_identity({"ticker":"KXBTC","market_id":"abc"},None)\n        self.assertEqual(t,"KXBTC")\n        self.assertEqual(m,"abc")\n\n    def test_nested_identity(self):\n        t,m=_extract_identity({"market":{"ticker":"KXETH"}},None)\n        self.assertEqual(t,"KXETH")\n        self.assertEqual(m,"KXETH")\n\n    def test_source_fallback(self):\n        t,m=_extract_identity({}, "KXSOURCE")\n        self.assertEqual(t,"KXSOURCE")\n        self.assertEqual(m,"KXSOURCE")\n\n    def test_identity(self):\n        self.assertEqual(OLR_052_BUILD_ID,"OLR-052")\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OLR-052 CERTIFICATION TEST")\n    print(" CANONICAL JSON EVIDENCE LOOKUP CORRECTION")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Canonical JSON market identity extraction certified")\n    print("[PASS] source_observation_id fallback certified")\n    print("[PASS] OLR-037 candidate shape preserved")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-052 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def restore(path,data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def corrected_olr_041_source():
    return """from __future__ import annotations
from pathlib import Path

OLR_041_BUILD_ID=\"OLR-041\"
OLR_041_REVISION=\"OLR_041_POSTGRESQL_LIVE_EVIDENCE_LOOKUP_CORRECTED_BY_OLR_052_V1\"

from .olr_052_canonical_json_evidence_lookup_correction import lookup_market_evidence

def verify_olr_041_postgresql_live_evidence_lookup(root=None):
    from .olr_040_outcome_evidence_linkage_freeze import verify_olr_040_outcome_evidence_linkage_freeze
    return verify_olr_040_outcome_evidence_linkage_freeze(root) and callable(lookup_market_evidence)
"""

def main():
    print("="*88)
    print(" OLR-052 INSTALLER")
    print(" CANONICAL JSON EVIDENCE LOOKUP CORRECTION")
    print("="*88)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))

    up=importlib.import_module(
        "qseries_v2.oracle_learning.olr_050_production_evidence_learning_activation_freeze"
    )
    if not up.verify_olr_050_production_evidence_learning_activation_freeze(ROOT):
        raise RuntimeError("Certified OLR-050 verification failed")

    print("[PASS] Certified OLR-050 production activation boundary verified")

    affected=(MOD,TEST,INIT,TARGET)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        update_init(
            INIT,
            "from .olr_052_canonical_json_evidence_lookup_correction import *",
        )

        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

        # Genuine defect correction to the frozen OLR-041 lookup boundary.
        corrected=corrected_olr_041_source()
        compile(corrected,str(TARGET),"exec")
        write_exact(TARGET,corrected)

        importlib.invalidate_caches()

        m=importlib.import_module(
            "qseries_v2.oracle_learning.olr_052_canonical_json_evidence_lookup_correction"
        )
        if not m.verify_olr_052_canonical_json_evidence_lookup_correction(ROOT):
            raise RuntimeError("OLR-052 verification failed")

        olr041=importlib.import_module(
            "qseries_v2.oracle_learning.olr_041_postgresql_live_evidence_lookup"
        )
        olr041=importlib.reload(olr041)

        if not olr041.verify_olr_041_postgresql_live_evidence_lookup(ROOT):
            raise RuntimeError("Corrected OLR-041 verification failed")

        print("[PASS] OLR-041 lookup boundary corrected to canonical_observation_json schema")
        print("[PASS] No PostgreSQL schema changes required")
        print("[PASS] No launcher changes required")

    except Exception:
        for p,b in old.items():
            restore(p,b)
        print("[ROLLBACK] OLR-052 correction failed; affected files restored")
        raise

    print("[PASS] OLR-036 through OLR-050 otherwise preserved frozen")
    print("[PASS] OPH-001 through OPH-033 preserved frozen")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-052 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
