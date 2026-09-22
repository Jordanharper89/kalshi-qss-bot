from pathlib import Path
import hashlib,py_compile
ROOT=Path.cwd(); BASE=ROOT/'qseries_v2/oracle_adapters/independent'
DEPS=[('oad_416_kalshi_market_evidence_requirement_resolver.py', None)]
for name,expected in DEPS:
 p=BASE/name
 if not p.exists(): raise SystemExit(f'[ERROR] required repo dependency missing: {p}')
 if expected and hashlib.sha256(p.read_bytes()).hexdigest()!=expected: raise SystemExit(f'[ERROR] repo dependency changed: {name}')
source="from __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_415_universal_source_registry import registry_by_family\nfrom qseries_v2.oracle_adapters.independent.oad_416_kalshi_market_evidence_requirement_resolver import resolve_market_cohort\nREAD_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False\n@dataclass(frozen=True,slots=True)\nclass MarketCoverage:\n ticker:str; domain:str; required:tuple[str,...]; available:tuple[str,...]; missing:tuple[str,...]; state:str\ndef build_source_to_market_coverage_matrix(markets,root='.'):\n reg=registry_by_family(root); out=[]\n for r in resolve_market_cohort(markets):\n  available=tuple(x for x in r.source_families if x in reg and reg[x].active)\n  missing=tuple(x for x in r.source_families if x not in available)\n  state='UNMAPPED' if r.state=='UNMAPPED' else ('COVERED' if not missing else ('PARTIAL' if available else 'NOT_COVERED'))\n  out.append(MarketCoverage(r.ticker,r.domain,r.source_families,available,missing,state))\n return tuple(out)\n"
test="import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_417_source_to_market_coverage_matrix import *\nclass T(unittest.TestCase):\n def test_matrix(self):\n  x=build_source_to_market_coverage_matrix([{'ticker':'WX','title':'Will temperature exceed 100 F?'},{'ticker':'BTC','title':'Will Bitcoin exceed 100000?'}],'.'); self.assertEqual(len(x),2); self.assertEqual(x[0].state,'COVERED'); self.assertIn(x[1].state,('PARTIAL','COVERED'))\nif __name__=='__main__':unittest.main(verbosity=2)\n"
target=BASE/'oad_417_source_to_market_coverage_matrix.py'; tpath=ROOT/'test_oad_417_source_to_market_coverage_matrix.py'
if target.exists(): raise SystemExit(f'[ERROR] target already exists; refusing overwrite: {target}')
target.write_text(source,encoding='utf-8'); tpath.write_text(test,encoding='utf-8')
py_compile.compile(str(target),doraise=True); py_compile.compile(str(tpath),doraise=True)
print('[PASS] OAD-417 source to market coverage matrix installed')
print('[PASS] exact current-repo dependency boundary verified')
print('[PASS] READ_ONLY=TRUE execution_authority=FALSE probability=FALSE')
