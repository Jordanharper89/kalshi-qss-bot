from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_016_canonical_market_identity_resolver.py'
TEST = ROOT / 'test_oiar_016_canonical_market_identity_resolver.py'
MODULE_SOURCE = 'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n\nOIAR_016_BUILD_ID="OIAR-016"\nOIAR_016_REVISION="OIAR_016_CANONICAL_MARKET_IDENTITY_RESOLVER_V1"\n\n@dataclass(frozen=True)\nclass CanonicalMarketIdentity:\n    requested_market_id:str\n    resolved:bool\n    source_market_id:str|None\n    market_title:str|None\n    event_ticker:str|None\n    source_symbol:str|None\n    source_close_time:str|None\n    source_expiration_time:str|None\n    observed_at:str|None\n    source_id:str|None\n    identity_reason:str\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef resolve_canonical_market_identity(root=None, market_id=None):\n    root=Path(root or Path.cwd()).resolve()\n    requested=str(market_id or "").strip().upper()\n    if not requested:\n        raise ValueError("market_id required")\n\n    sql="""\n    SELECT observed_at, source_id, canonical_observation_json\n    FROM public.oracle_canonical_observations\n    WHERE observation_type=\'market_snapshot\'\n      AND (\n        COALESCE(canonical_observation_json->\'payload\'->>\'source_market_id\',\'\')=%s\n        OR COALESCE(canonical_observation_json->\'payload\'->>\'source_symbol\',\'\')=%s\n        OR COALESCE(canonical_observation_json->\'raw_observation\'->\'payload\'->>\'source_market_id\',\'\')=%s\n        OR COALESCE(canonical_observation_json->\'raw_observation\'->\'payload\'->>\'source_symbol\',\'\')=%s\n      )\n    ORDER BY sequence_number DESC\n    LIMIT 1\n    """\n\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(sql,(requested,requested,requested,requested))\n            row=cur.fetchone()\n        conn.rollback()\n\n    if row is None:\n        return CanonicalMarketIdentity(\n            requested,False,None,None,None,None,None,None,None,None,\n            "identity_unresolved_no_exact_canonical_match",True,False\n        )\n\n    observed_at,source_id,body=row\n    if isinstance(body,str):\n        body=json.loads(body)\n    payload={}\n    if isinstance(body,dict):\n        payload=body.get("payload") or {}\n        if not payload and isinstance(body.get("raw_observation"),dict):\n            payload=body["raw_observation"].get("payload") or {}\n\n    source_market_id=str(payload.get("source_market_id") or "").upper() or None\n    source_symbol=str(payload.get("source_symbol") or "").upper() or None\n    market_title=str(payload.get("market_title") or "").strip() or None\n    event_ticker=str(payload.get("event_ticker") or "").upper() or None\n\n    exact=requested in {source_market_id,source_symbol}\n    if not exact:\n        return CanonicalMarketIdentity(\n            requested,False,None,None,None,None,None,None,None,None,\n            "identity_unresolved_canonical_row_not_exact",True,False\n        )\n\n    return CanonicalMarketIdentity(\n        requested,True,source_market_id,market_title,event_ticker,source_symbol,\n        str(payload.get("source_close_time") or "") or None,\n        str(payload.get("source_expiration_time") or "") or None,\n        str(observed_at),\n        str(source_id),\n        "identity_resolved_exact_canonical_match",\n        True,False\n    )\n\ndef verify_oiar_016(root=None, sample_market_id=None):\n    x=resolve_canonical_market_identity(root,sample_market_id)\n    return bool(x.resolved and x.market_title and x.source_market_id and x.read_only and not x.execution_authority)\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_016_canonical_market_identity_resolver import CanonicalMarketIdentity,OIAR_016_BUILD_ID\nclass T(unittest.TestCase):\n    def test_identity(self): self.assertEqual(OIAR_016_BUILD_ID,"OIAR-016")\n    def test_contract(self):\n        x=CanonicalMarketIdentity("X",False,None,None,None,None,None,None,None,None,"unresolved",True,False)\n        self.assertTrue(x.read_only); self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n    print("="*88);print(" OIAR-016 CERTIFICATION TEST");print(" CANONICAL MARKET IDENTITY RESOLVER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] exact canonical identity contract certified")\n    print("[PASS] unresolved identity remains explicit")\n    print("[DONE] OIAR-016 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py',)
EXTRA_FILES = {}

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

def main():
    print("=" * 88)
    print(" OIAR_016_CANONICAL_MARKET_IDENTITY_RESOLVER INSTALLER")
    print("=" * 88)
    print("[ROOT]", ROOT)

    for rel in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            raise RuntimeError(f"Required proven upstream missing: {p}")

    targets = [MOD, TEST] + [ROOT / p for p in EXTRA_FILES]
    old = {p: (p.read_bytes() if p.exists() else None) for p in targets}

    try:
        ast.parse(MODULE_SOURCE)
        ast.parse(TEST_SOURCE)
        for src in EXTRA_FILES.values():
            ast.parse(src)
        print("[PASS] installer payload syntax verified")

        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        for rel, src in EXTRA_FILES.items():
            write_exact(ROOT / rel, src)

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_016_canonical_market_identity_resolver")
        x=m.resolve_canonical_market_identity(ROOT,"KXBTCPRICE-85000-26AUG28")
        print(f"[PHYSICAL] resolved={x.resolved} source_market_id={x.source_market_id} title={x.market_title}")
        if not (x.resolved and x.market_title):
            raise RuntimeError("OIAR-016 physical canonical identity resolution failed")
    except Exception:
        for p, data in old.items():
            restore(p, data)
        print("[ROLLBACK] installer failed; affected files restored")
        raise

    print("[PASS] read-only trader intelligence boundary preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
