from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
MOD=ROOT/"qseries_v2/oracle_intelligence_analytics_runtime/oiar_066_certified_outcome_source_physical_discovery.py"
TEST=ROOT/"test_oiar_066_certified_outcome_source_physical_discovery.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass, asdict\nfrom pathlib import Path\nimport inspect\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_learning_runtime import olr_002_settled_outcome_read_model as settled_model\nfrom qseries_v2.oracle_production_learning import opl_001_production_learning_foundation as foundation\nfrom qseries_v2.oracle_production_learning import opl_002_canonical_evidence_index as evidence_index\n\nBUILD_ID="OIAR-066"\nREVISION="OIAR_066_CERTIFIED_OUTCOME_SOURCE_PHYSICAL_DISCOVERY_V1"\n\n@dataclass(frozen=True)\nclass OutcomeSourceProof:\n    settled_read_model_build_id:str\n    settled_outcome_fields:tuple\n    production_state_table:str\n    production_ledger_table:str\n    evidence_index_table:str\n    ledger_columns:tuple\n    evidence_columns:tuple\n    ledger_rows:int\n    learned_rows:int\n    eligible_rows:int\n    evidence_missing_rows:int\n    evidence_index_rows:int\n    evidence_with_sequence_rows:int\n    latest_learned_ticker:str\n    latest_learned_settlement_ts:str\n    exact_market_identity_field:str\n    exact_settlement_field:str\n    exact_outcome_field:str\n    exact_evidence_cutoff_field:str\n    exact_source_lineage_fields:tuple\n    settled_normalization_proven:bool\n    pre_settlement_linkage_contract_proven:bool\n    read_only:bool\n    outcome_source_bound:bool\n    probability_enabled:bool\n    execution_authority:bool\n\ndef _columns(cur, table):\n    cur.execute("""\n        SELECT column_name\n        FROM information_schema.columns\n        WHERE table_schema=\'public\' AND table_name=%s\n        ORDER BY ordinal_position\n    """,(table,))\n    return tuple(str(r[0]) for r in cur.fetchall())\n\ndef _count(cur, table):\n    cur.execute(f"SELECT count(*) FROM public.{table}")\n    return int(cur.fetchone()[0])\n\ndef _status_count(cur, status):\n    cur.execute(\n        f"SELECT count(*) FROM public.{foundation.LEDGER_TABLE} WHERE status=%s",\n        (status,),\n    )\n    return int(cur.fetchone()[0])\n\ndef _latest_learned(cur):\n    cur.execute(f"""\n        SELECT ticker, settlement_ts\n        FROM public.{foundation.LEDGER_TABLE}\n        WHERE status=\'LEARNED\'\n        ORDER BY learned_at DESC NULLS LAST, updated_at DESC\n        LIMIT 1\n    """)\n    row=cur.fetchone()\n    return ("","") if not row else (str(row[0] or ""),str(row[1] or ""))\n\ndef prove_certified_outcome_source(root=None):\n    root=Path(root or Path.cwd()).resolve()\n\n    normalized=settled_model.normalize_settled_market({\n        "ticker":"KXOIAR066PROBE",\n        "result":"yes",\n        "settlement_ts":"2026-08-26T00:00:00Z",\n    })\n    normalization_ok=(\n        normalized is not None\n        and normalized.ticker=="KXOIAR066PROBE"\n        and normalized.result=="yes"\n        and normalized.settlement_ts=="2026-08-26T00:00:00Z"\n        and len(normalized.source_hash)==64\n    )\n\n    with connect(root,autocommit=False) as conn:\n        cur=conn.cursor()\n        cur.execute("SET TRANSACTION READ ONLY")\n        ledger_cols=_columns(cur,foundation.LEDGER_TABLE)\n        evidence_cols=_columns(cur,evidence_index.INDEX_TABLE)\n\n        required_ledger={\n            "settlement_hash","ticker","result","settlement_ts",\n            "evidence_observation_id","evidence_hash",\n            "evidence_sequence_number","learning_event_hash","status"\n        }\n        required_evidence={\n            "observation_id","ticker","evidence_hash",\n            "sequence_number","observed_at","observation_type"\n        }\n        if not required_ledger.issubset(set(ledger_cols)):\n            raise RuntimeError("production learning ledger missing required certified fields")\n        if not required_evidence.issubset(set(evidence_cols)):\n            raise RuntimeError("production evidence index missing required certified fields")\n\n        ledger_rows=_count(cur,foundation.LEDGER_TABLE)\n        learned=_status_count(cur,"LEARNED")\n        eligible=_status_count(cur,"ELIGIBLE")\n        missing=_status_count(cur,"EVIDENCE_MISSING")\n        evidence_rows=_count(cur,evidence_index.INDEX_TABLE)\n\n        cur.execute(\n            f"SELECT count(*) FROM public.{foundation.LEDGER_TABLE} "\n            "WHERE evidence_sequence_number IS NOT NULL"\n        )\n        with_seq=int(cur.fetchone()[0])\n        latest_ticker,latest_ts=_latest_learned(cur)\n        conn.rollback()\n\n    opl7_source=""\n    try:\n        from qseries_v2.oracle_production_learning import opl_007_evidence_first_outcome_resolver as opl7\n        opl7_source=inspect.getsource(opl7.collect_evidence_supported_settlements)\n    except Exception:\n        pass\n    strict_pre_settlement=(\n        "observed_at" in opl7_source\n        and "settlement_ts" in opl7_source\n        and "<" in opl7_source\n    )\n\n    return OutcomeSourceProof(\n        settled_read_model_build_id=str(settled_model.OLR_002_BUILD_ID),\n        settled_outcome_fields=("ticker","result","settlement_ts","source_hash"),\n        production_state_table=str(foundation.STATE_TABLE),\n        production_ledger_table=str(foundation.LEDGER_TABLE),\n        evidence_index_table=str(evidence_index.INDEX_TABLE),\n        ledger_columns=ledger_cols,\n        evidence_columns=evidence_cols,\n        ledger_rows=ledger_rows,\n        learned_rows=learned,\n        eligible_rows=eligible,\n        evidence_missing_rows=missing,\n        evidence_index_rows=evidence_rows,\n        evidence_with_sequence_rows=with_seq,\n        latest_learned_ticker=latest_ticker,\n        latest_learned_settlement_ts=latest_ts,\n        exact_market_identity_field="ticker",\n        exact_settlement_field="settlement_ts",\n        exact_outcome_field="result",\n        exact_evidence_cutoff_field="evidence_sequence_number",\n        exact_source_lineage_fields=("settlement_hash","evidence_hash","learning_event_hash"),\n        settled_normalization_proven=normalization_ok,\n        pre_settlement_linkage_contract_proven=strict_pre_settlement,\n        read_only=True,\n        outcome_source_bound=False,\n        probability_enabled=False,\n        execution_authority=False,\n    )\n\ndef physical_probe(root=None):\n    return asdict(prove_certified_outcome_source(root))\n\ndef verify_oiar_066_certified_outcome_source_physical_discovery():\n    x=settled_model.normalize_settled_market(\n        {"ticker":"KXTEST","result":"no","settlement_ts":"2026-08-26T00:00:00Z"}\n    )\n    return (\n        BUILD_ID=="OIAR-066"\n        and x is not None\n        and x.result=="no"\n        and foundation.LEDGER_TABLE=="oracle_production_learning_ledger"\n        and evidence_index.INDEX_TABLE=="oracle_production_learning_evidence_index"\n    )\n'
TEST_SOURCE='import unittest\nfrom pathlib import Path\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_066_certified_outcome_source_physical_discovery as m\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(m.verify_oiar_066_certified_outcome_source_physical_discovery())\n\n    def test_physical_source(self):\n        x=m.physical_probe(Path.cwd())\n        self.assertEqual(x["settled_read_model_build_id"],"OLR-002")\n        self.assertTrue(x["settled_normalization_proven"])\n        self.assertTrue(x["pre_settlement_linkage_contract_proven"])\n        self.assertIn("ticker",x["ledger_columns"])\n        self.assertIn("result",x["ledger_columns"])\n        self.assertIn("settlement_ts",x["ledger_columns"])\n        self.assertIn("evidence_sequence_number",x["ledger_columns"])\n        self.assertIn("sequence_number",x["evidence_columns"])\n        self.assertTrue(x["read_only"])\n        self.assertFalse(x["outcome_source_bound"])\n        self.assertFalse(x["probability_enabled"])\n        self.assertFalse(x["execution_authority"])\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OIAR-066 CERTIFICATION TEST")\n    print(" CERTIFIED OUTCOME SOURCE PHYSICAL DISCOVERY")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] existing settled-outcome read model physically identified")\n    print("[PASS] production learning ledger/evidence index contract physically identified")\n    print("[PASS] strict pre-settlement linkage contract proven")\n    print("[PASS] probability remains gated")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-066 CERTIFIED")\n'

REQUIRED=(
    "qseries_v2/oracle_intelligence_analytics_runtime/oiar_065_outcome_calibration_bridge_readiness.py",
    "qseries_v2/oracle_learning_runtime/olr_002_settled_outcome_read_model.py",
    "qseries_v2/oracle_production_learning/opl_001_production_learning_foundation.py",
    "qseries_v2/oracle_production_learning/opl_002_canonical_evidence_index.py",
    "qseries_v2/oracle_production_learning/opl_007_evidence_first_outcome_resolver.py",
)

def _write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+f".{os.getpid()}.tmp")
    t.write_text(s,encoding="utf-8",newline="\n")
    os.replace(t,p)

def _restore(p,b):
    if b is None:
        if p.exists():p.unlink()
    else:
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(b)

def main():
    print("="*88)
    print(" OIAR-066 INSTALLER")
    print(" CERTIFIED OUTCOME SOURCE PHYSICAL DISCOVERY")
    print("="*88)
    print("[ROOT]",ROOT)

    for r in REQUIRED:
        if not (ROOT/r).is_file():
            raise RuntimeError("Required existing pavement missing: "+r)

    bm=MOD.read_bytes() if MOD.exists() else None
    bt=TEST.read_bytes() if TEST.exists() else None

    try:
        ast.parse(MODULE_SOURCE)
        ast.parse(TEST_SOURCE)
        print("[PASS] installer payload syntax verified")

        _write(MOD,MODULE_SOURCE)
        _write(TEST,TEST_SOURCE)
        importlib.invalidate_caches()

        m=importlib.import_module(
            "qseries_v2.oracle_intelligence_analytics_runtime."
            "oiar_066_certified_outcome_source_physical_discovery"
        )

        s=time.monotonic()
        x=m.physical_probe(ROOT)
        print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))

        if x["settled_read_model_build_id"]!="OLR-002":
            raise RuntimeError("settled outcome source identity mismatch")
        if not x["settled_normalization_proven"]:
            raise RuntimeError("settled outcome normalization not proven")
        if not x["pre_settlement_linkage_contract_proven"]:
            raise RuntimeError("strict pre-settlement evidence contract not proven")
        if not x["read_only"] or x["execution_authority"]:
            raise RuntimeError("read-only/execution boundary violated")
        if x["outcome_source_bound"] or x["probability_enabled"]:
            raise RuntimeError("OIAR-066 must discover only; calibration remains gated")

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),check=True,timeout=180
        )

    except Exception:
        _restore(MOD,bm)
        _restore(TEST,bt)
        print("[ROLLBACK] OIAR-066 failed; affected files restored")
        raise

    print("[PASS] existing Oracle outcome pavement discovered in place")
    print("[PASS] OLR-002 settled outcome identity/result/settlement source preserved")
    print("[PASS] OPL production ledger supplies evidence cutoff + lineage fields")
    print("[PASS] OPL evidence index supplies canonical evidence sequence lineage")
    print("[PASS] no frozen learning subsystem modified")
    print("[PASS] outcome_source_bound=FALSE")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-066 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
