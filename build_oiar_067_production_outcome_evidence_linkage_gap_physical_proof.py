from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
MOD=ROOT/"qseries_v2/oracle_intelligence_analytics_runtime/oiar_067_production_outcome_evidence_linkage_gap_physical_proof.py"
TEST=ROOT/"test_oiar_067_production_outcome_evidence_linkage_gap_physical_proof.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass, asdict\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_production_learning import opl_001_production_learning_foundation as foundation\nfrom qseries_v2.oracle_production_learning import opl_002_canonical_evidence_index as evidence_index\n\nBUILD_ID="OIAR-067"\nREVISION="OIAR_067_PRODUCTION_OUTCOME_EVIDENCE_LINKAGE_GAP_PHYSICAL_PROOF_V1"\n\n@dataclass(frozen=True)\nclass LinkageGapProof:\n    sampled_missing_settlements:int\n    exact_ticker_evidence_found:int\n    exact_ticker_pre_settlement_found:int\n    exact_ticker_only_post_settlement:int\n    exact_ticker_no_evidence:int\n    evidence_rows_examined:int\n    candidate_pre_settlement_rows:int\n    distinct_tickers_with_pre_settlement_evidence:int\n    sample_examples:tuple\n    read_only:bool\n    repaired_rows:int\n    probability_enabled:bool\n    execution_authority:bool\n\ndef _iso(v):\n    return "" if v is None else (v.isoformat() if hasattr(v,"isoformat") else str(v))\n\ndef prove_linkage_gap(root=None,sample_size=100):\n    root=Path(root or Path.cwd()).resolve()\n    n=max(1,min(int(sample_size),500))\n    with connect(root,autocommit=False) as conn:\n        cur=conn.cursor()\n        cur.execute("SET TRANSACTION READ ONLY")\n        cur.execute("SET LOCAL statement_timeout=\'30000ms\'")\n\n        cur.execute(f"""\n            SELECT settlement_hash,ticker,result,settlement_ts\n            FROM public.{foundation.LEDGER_TABLE}\n            WHERE status=\'EVIDENCE_MISSING\'\n            ORDER BY updated_at DESC, settlement_ts DESC\n            LIMIT %s\n        """,(n,))\n        missing=cur.fetchall()\n\n        found=pre=post_only=noev=examined=pre_rows=0\n        pre_tickers=set()\n        examples=[]\n\n        sql=f"""\n            SELECT observation_id,evidence_hash,sequence_number,observed_at,observation_type\n            FROM public.{evidence_index.INDEX_TABLE}\n            WHERE ticker=%s\n            ORDER BY sequence_number DESC\n            LIMIT 200\n        """\n\n        for settlement_hash,ticker,result,settlement_ts in missing:\n            cur.execute(sql,(ticker,))\n            rows=cur.fetchall()\n            examined+=len(rows)\n            if rows:\n                found+=1\n            before=[r for r in rows if r[3] is not None and settlement_ts is not None and r[3] < settlement_ts]\n            after=[r for r in rows if r[3] is not None and settlement_ts is not None and r[3] >= settlement_ts]\n            if before:\n                pre+=1\n                pre_rows+=len(before)\n                pre_tickers.add(str(ticker))\n                cls="PRE_SETTLEMENT_EVIDENCE_EXISTS"\n            elif rows and after:\n                post_only+=1\n                cls="ONLY_POST_SETTLEMENT_EVIDENCE"\n            else:\n                noev+=1\n                cls="NO_EXACT_TICKER_EVIDENCE"\n            if len(examples)<20:\n                newest_pre=max(before,key=lambda r:r[2]) if before else None\n                examples.append({\n                    "ticker":str(ticker),\n                    "result":str(result),\n                    "settlement_ts":_iso(settlement_ts),\n                    "classification":cls,\n                    "evidence_rows":len(rows),\n                    "pre_settlement_rows":len(before),\n                    "post_settlement_rows":len(after),\n                    "newest_pre_sequence":None if newest_pre is None else int(newest_pre[2]),\n                    "newest_pre_observed_at":"" if newest_pre is None else _iso(newest_pre[3]),\n                    "newest_pre_observation_type":"" if newest_pre is None else str(newest_pre[4]),\n                    "settlement_hash":str(settlement_hash),\n                })\n\n        conn.rollback()\n\n    return LinkageGapProof(\n        sampled_missing_settlements=len(missing),\n        exact_ticker_evidence_found=found,\n        exact_ticker_pre_settlement_found=pre,\n        exact_ticker_only_post_settlement=post_only,\n        exact_ticker_no_evidence=noev,\n        evidence_rows_examined=examined,\n        candidate_pre_settlement_rows=pre_rows,\n        distinct_tickers_with_pre_settlement_evidence=len(pre_tickers),\n        sample_examples=tuple(examples),\n        read_only=True,\n        repaired_rows=0,\n        probability_enabled=False,\n        execution_authority=False,\n    )\n\ndef physical_probe(root=None,sample_size=100):\n    return asdict(prove_linkage_gap(root,sample_size))\n\ndef verify_oiar_067_production_outcome_evidence_linkage_gap_physical_proof():\n    return (\n        BUILD_ID=="OIAR-067"\n        and foundation.LEDGER_TABLE=="oracle_production_learning_ledger"\n        and evidence_index.INDEX_TABLE=="oracle_production_learning_evidence_index"\n    )\n'
TEST_SOURCE='import unittest\nfrom pathlib import Path\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_067_production_outcome_evidence_linkage_gap_physical_proof as m\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(m.verify_oiar_067_production_outcome_evidence_linkage_gap_physical_proof())\n\n    def test_physical_gap(self):\n        x=m.physical_probe(Path.cwd(),25)\n        self.assertGreater(x["sampled_missing_settlements"],0)\n        self.assertEqual(\n            x["exact_ticker_pre_settlement_found"]+\n            x["exact_ticker_only_post_settlement"]+\n            x["exact_ticker_no_evidence"],\n            x["sampled_missing_settlements"],\n        )\n        self.assertTrue(x["read_only"])\n        self.assertEqual(x["repaired_rows"],0)\n        self.assertFalse(x["probability_enabled"])\n        self.assertFalse(x["execution_authority"])\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OIAR-067 CERTIFICATION TEST")\n    print(" PRODUCTION OUTCOME/EVIDENCE LINKAGE GAP PHYSICAL PROOF")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] EVIDENCE_MISSING sample physically classified")\n    print("[PASS] exact ticker evidence checked")\n    print("[PASS] strict pre-settlement evidence checked")\n    print("[PASS] read-only proof preserved")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-067 CERTIFIED")\n'

REQUIRED=(
 "qseries_v2/oracle_intelligence_analytics_runtime/oiar_066_certified_outcome_source_physical_discovery.py",
 "qseries_v2/oracle_production_learning/opl_001_production_learning_foundation.py",
 "qseries_v2/oracle_production_learning/opl_002_canonical_evidence_index.py",
)

def _write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+f".{os.getpid()}.tmp")
    t.write_text(s,encoding="utf-8",newline="\n")
    os.replace(t,p)

def _restore(p,b):
    if b is None:
        if p.exists(): p.unlink()
    else:
        p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b)

def main():
    print("="*88)
    print(" OIAR-067 INSTALLER")
    print(" PRODUCTION OUTCOME/EVIDENCE LINKAGE GAP PHYSICAL PROOF")
    print("="*88)
    print("[ROOT]",ROOT)
    for r in REQUIRED:
        if not (ROOT/r).is_file(): raise RuntimeError("Required proven pavement missing: "+r)

    bm=MOD.read_bytes() if MOD.exists() else None
    bt=TEST.read_bytes() if TEST.exists() else None
    try:
        ast.parse(MODULE_SOURCE); ast.parse(TEST_SOURCE)
        print("[PASS] installer payload syntax verified")
        _write(MOD,MODULE_SOURCE); _write(TEST,TEST_SOURCE)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_067_production_outcome_evidence_linkage_gap_physical_proof")
        s=time.monotonic(); x=m.physical_probe(ROOT,100)
        print("[PHYSICAL SUMMARY]",{k:v for k,v in x.items() if k!="sample_examples"},"elapsed_seconds=",round(time.monotonic()-s,3))
        print("[SAMPLE CLASSIFICATIONS]")
        for row in x["sample_examples"]: print(row)
        if x["sampled_missing_settlements"]<=0: raise RuntimeError("no EVIDENCE_MISSING settlements available to prove")
        if not x["read_only"] or x["repaired_rows"]!=0 or x["execution_authority"]:
            raise RuntimeError("proof boundary violated")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=180)
    except Exception:
        _restore(MOD,bm); _restore(TEST,bt)
        print("[ROLLBACK] OIAR-067 failed; affected files restored")
        raise

    print("[PASS] linkage gap physically measured without modifying learning state")
    print("[PASS] missing settlements classified as pre-settlement evidence / post-only / no exact evidence")
    print("[PASS] repaired_rows=0")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-067 INSTALLATION COMPLETE")

if __name__=="__main__": main()
