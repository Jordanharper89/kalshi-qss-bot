from pathlib import Path
import hashlib,py_compile
ROOT=Path.cwd(); BASE=ROOT/'qseries_v2/oracle_adapters/independent'
DEPS=[('oad_415_universal_source_registry.py', None)]
for name,expected in DEPS:
 p=BASE/name
 if not p.exists(): raise SystemExit(f'[ERROR] required repo dependency missing: {p}')
 if expected and hashlib.sha256(p.read_bytes()).hexdigest()!=expected: raise SystemExit(f'[ERROR] repo dependency changed: {name}')
source="from __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_076_precision_current_market_topic_classifier import classify_market_topic\nfrom qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router import assign_source_requirement\nREAD_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False\n@dataclass(frozen=True,slots=True)\nclass MarketEvidenceRequirement:\n ticker:str; domain:str; source_families:tuple[str,...]; state:str\nEXTRA={'weather':('NWS/NOAA',),'crypto':('COINBASE','BITCOIN_CHAIN','ETHEREUM_CHAIN','SOLANA_CHAIN'),'macroeconomics':('BLS','ECONOMIC_OFFICIAL'),'health':('CDC','PUBLIC_HEALTH_OFFICIAL'),'sports':('SPORTS_OFFICIAL',),'energy_commodities':('EIA',),'corporate_finance':('SEC_EDGAR',),'politics_elections':('ELECTION_OFFICIAL',),'science_space':('NASA',),'transport':('FAA',)}\ndef resolve_market_evidence_requirement(market):\n c=classify_market_topic(market); r=assign_source_requirement(c.primary_topic)\n fam=EXTRA.get(c.primary_topic,tuple(r.authoritative_source_families))\n state='RESOLVED' if fam and c.primary_topic!='other' else 'UNMAPPED'\n return MarketEvidenceRequirement(str(market.get('ticker','')),c.primary_topic,tuple(fam),state)\ndef resolve_market_cohort(markets):return tuple(resolve_market_evidence_requirement(x) for x in markets)\n"
test="import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_416_kalshi_market_evidence_requirement_resolver import *\nclass T(unittest.TestCase):\n def test_weather(self):\n  x=resolve_market_evidence_requirement({'ticker':'WX','title':'Will temperature exceed 100 F?'}); self.assertEqual(x.domain,'weather'); self.assertIn('NWS/NOAA',x.source_families)\n def test_crypto(self):\n  x=resolve_market_evidence_requirement({'ticker':'BTC','title':'Will Bitcoin exceed 100000?'}); self.assertEqual(x.domain,'crypto'); self.assertIn('COINBASE',x.source_families)\n def test_unknown(self): self.assertEqual(resolve_market_evidence_requirement({'ticker':'X','title':'Completely novel thing'}).state,'UNMAPPED')\nif __name__=='__main__':unittest.main(verbosity=2)\n"
target=BASE/'oad_416_kalshi_market_evidence_requirement_resolver.py'; tpath=ROOT/'test_oad_416_kalshi_market_evidence_requirement_resolver.py'
if target.exists(): raise SystemExit(f'[ERROR] target already exists; refusing overwrite: {target}')
target.write_text(source,encoding='utf-8'); tpath.write_text(test,encoding='utf-8')
py_compile.compile(str(target),doraise=True); py_compile.compile(str(tpath),doraise=True)
print('[PASS] OAD-416 kalshi market evidence requirement resolver installed')
print('[PASS] exact current-repo dependency boundary verified')
print('[PASS] READ_ONLY=TRUE execution_authority=FALSE probability=FALSE')
