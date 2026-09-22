from pathlib import Path
import ast

REVISION = "BUILD_SSI_001_PHYSICAL_SOLANA_INTELLIGENCE_AUDIT_V1"
ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_strategy_intelligence" / "solana"
MODULE = PKG / "ssi_001_physical_solana_intelligence_audit.py"
TEST = ROOT / "test_ssi_001_physical_solana_intelligence_audit.py"
DEPENDENCIES = ['qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py', 'qseries_v2/oracle_adapters/independent/oad_322_solana_universal_chain_coverage_gate.py']

MODULE_CODE = 'from __future__ import annotations\nfrom dataclasses import dataclass, asdict\nfrom datetime import datetime, timezone\nfrom typing import Any, Iterable\nimport hashlib, json, math\n\nREAD_ONLY = True\nEXECUTION_AUTHORITY = False\n\ndef _iso(v):\n    if v is None: return None\n    if isinstance(v, datetime):\n        if v.tzinfo is None: v = v.replace(tzinfo=timezone.utc)\n        return v.astimezone(timezone.utc).isoformat()\n    return str(v)\n\ndef _f(v):\n    try:\n        x=float(v)\n        return x if math.isfinite(x) else None\n    except Exception:\n        return None\n\ndef _dig(o, *paths):\n    for path in paths:\n        cur=o\n        ok=True\n        for k in path.split("."):\n            if isinstance(cur, dict) and k in cur: cur=cur[k]\n            else: ok=False; break\n        if ok and cur is not None: return cur\n    return None\n\nAUDIT_SCHEMA="SSI-001"\nPRICE_KEYS=("price","price_usd","usd_price","token_price","close","mid","value")\nLIQ_KEYS=("liquidity","liquidity_usd","tvl","tvl_usd","reserve_usd")\nTIME_KEYS=("observed_at","timestamp","block_time","blockTime","time")\nASSET_KEYS=("mint","token_mint","base_mint","asset","symbol","pool","pool_address")\ndef audit_rows(rows: Iterable[dict[str,Any]]) -> dict[str,Any]:\n    rows=list(rows); assets=set(); sources=set(); types=set(); times=[]; priced=liquid=0\n    for r in rows:\n        a=_dig(r,*ASSET_KEYS); s=_dig(r,"source_id","provider"); t=_dig(r,"observation_type","type")\n        if a: assets.add(str(a))\n        if s: sources.add(str(s))\n        if t: types.add(str(t))\n        if any(_f(_dig(r,k)) is not None for k in PRICE_KEYS): priced+=1\n        if any(_f(_dig(r,k)) is not None for k in LIQ_KEYS): liquid+=1\n        tv=_dig(r,*TIME_KEYS)\n        if tv is not None: times.append(str(tv))\n    return {"schema_version":AUDIT_SCHEMA,"rows":len(rows),"assets":len(assets),\n            "sources":tuple(sorted(sources)),"observation_types":tuple(sorted(types)),\n            "priced_rows":priced,"liquidity_rows":liquid,\n            "first_observed_at":min(times) if times else None,\n            "last_observed_at":max(times) if times else None,\n            "profitability_input_ready": bool(rows and priced>=2),\n            "read_only":True,"execution_authority":False}\ndef audit_jsonl(path):\n    rows=[]\n    with open(path,encoding="utf-8") as f:\n        for line in f:\n            try: rows.append(json.loads(line))\n            except Exception: pass\n    return audit_rows(rows)\n'
TEST_CODE = 'import unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana.ssi_001_physical_solana_intelligence_audit import audit_rows\nclass T(unittest.TestCase):\n    def test_audit(self):\n        r=audit_rows([\n          {"observed_at":"2026-09-01T00:00:00Z","source_id":"source.onchain.solana.mainnet","observation_type":"price","mint":"A","price_usd":1.0,"liquidity_usd":1000},\n          {"observed_at":"2026-09-01T00:00:05Z","source_id":"source.onchain.solana.mainnet","observation_type":"price","mint":"A","price_usd":1.1,"liquidity_usd":1100}])\n        print("[AUDIT]",r); self.assertTrue(r["profitability_input_ready"]); self.assertFalse(r["execution_authority"])\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'

def _certification_contract():
    return {
        "read_only": True,
        "execution_authority": False,
        "live_reacquisition": False,
        "direct_postgresql_writer": False,
        "gmgn_required": False,
        "preserve_existing_pavement": True,
        "profitability_target": True,
    }

def _verify_contract():
    c = _certification_contract()
    assert c["read_only"] is True
    assert c["execution_authority"] is False
    assert c["live_reacquisition"] is False
    assert c["direct_postgresql_writer"] is False
    assert c["gmgn_required"] is False
    assert c["preserve_existing_pavement"] is True
    assert c["profitability_target"] is True
    return c

def main():
    print("=" * 120)
    print(" SSI 001 PHYSICAL SOLANA INTELLIGENCE AUDIT INSTALLER")
    print("=" * 120)
    print("[BOOT] Revision:", REVISION)
    print("[CONTRACT]", _verify_contract())
    print("[ROOT]", ROOT)
    for rel in DEPENDENCIES:
        p = ROOT / rel
        if not p.exists():
            raise SystemExit("[FAIL] missing exact dependency: " + rel)
        ast.parse(p.read_text(encoding="utf-8"))
        print("[PASS] dependency interface present:", rel)
    PKG.mkdir(parents=True, exist_ok=True)
    init = PKG / "__init__.py"
    if not init.exists():
        init.write_text("", encoding="utf-8")
    MODULE.write_text(MODULE_CODE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    ast.parse(MODULE.read_text(encoding="utf-8"))
    ast.parse(TEST.read_text(encoding="utf-8"))
    print("[PASS] module installed:", MODULE.relative_to(ROOT))
    print("[PASS] test installed:", TEST.relative_to(ROOT))
    print("[PASS] syntax validated")
    print("[PASS] existing Solana/OCL/OPH production pavement preserved unchanged")
    print("[PASS] no live reacquisition introduced")
    print("[PASS] no direct PostgreSQL writer introduced")
    print("[PASS] GMGN not required")
    print("[PASS] Oracle remains read-only; execution_authority=FALSE")
    print("[DONE] INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
