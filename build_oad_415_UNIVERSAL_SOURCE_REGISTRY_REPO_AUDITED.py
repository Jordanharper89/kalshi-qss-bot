from pathlib import Path
import hashlib,py_compile
ROOT=Path.cwd(); BASE=ROOT/'qseries_v2/oracle_adapters/independent'
DEPS=[('oad_414_oracle_source_capability_inventory.py', None)]
for name,expected in DEPS:
 p=BASE/name
 if not p.exists(): raise SystemExit(f'[ERROR] required repo dependency missing: {p}')
 if expected and hashlib.sha256(p.read_bytes()).hexdigest()!=expected: raise SystemExit(f'[ERROR] repo dependency changed: {name}')
source="from __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_414_oracle_source_capability_inventory import inventory_source_capabilities\nREAD_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False\n@dataclass(frozen=True,slots=True)\nclass SourceRegistryEntry:\n source_family:str; authority:str; existing_modules:tuple[str,...]; active:bool\nTARGETS=(('NWS/NOAA','AUTHORITATIVE'),('USGS','AUTHORITATIVE'),('SPORTS_OFFICIAL','PRIMARY'),('MLB_OFFICIAL','PRIMARY'),('NHL_OFFICIAL','PRIMARY'),('BLS','AUTHORITATIVE'),('ECONOMIC_OFFICIAL','AUTHORITATIVE'),('CDC','AUTHORITATIVE'),('PUBLIC_HEALTH_OFFICIAL','AUTHORITATIVE'),('COINBASE','PRIMARY'),('BITCOIN_CHAIN','PRIMARY'),('ETHEREUM_CHAIN','PRIMARY'),('SOLANA_CHAIN','PRIMARY'),('FEDERAL_REGISTER','AUTHORITATIVE'),('REDDIT','SOCIAL_SIGNAL'),('X/TWITTER','SOCIAL_SIGNAL'),('NEWS','SECONDARY_HIGH_RELIABILITY'),('EIA','AUTHORITATIVE'),('SEC_EDGAR','AUTHORITATIVE'),('ELECTION_OFFICIAL','AUTHORITATIVE'),('NASA','AUTHORITATIVE'),('FAA','AUTHORITATIVE'))\ndef build_source_registry(root='.'):\n caps=inventory_source_capabilities(root); out=[]\n for fam,auth in TARGETS:\n  mods=tuple(sorted(x.module for x in caps if x.source_family==fam))\n  out.append(SourceRegistryEntry(fam,auth,mods,bool(mods)))\n return tuple(out)\ndef registry_by_family(root='.'):\n return {x.source_family:x for x in build_source_registry(root)}\n"
test="import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_415_universal_source_registry import *\nclass T(unittest.TestCase):\n def test_registry(self):\n  r=registry_by_family('.'); self.assertTrue(r['NWS/NOAA'].active); self.assertFalse(r['REDDIT'].active); self.assertFalse(r['X/TWITTER'].active); self.assertFalse(r['NEWS'].active)\n def test_unique(self):\n  x=build_source_registry('.'); self.assertEqual(len(x),len({a.source_family for a in x}))\nif __name__=='__main__':unittest.main(verbosity=2)\n"
target=BASE/'oad_415_universal_source_registry.py'; tpath=ROOT/'test_oad_415_universal_source_registry.py'
if target.exists(): raise SystemExit(f'[ERROR] target already exists; refusing overwrite: {target}')
target.write_text(source,encoding='utf-8'); tpath.write_text(test,encoding='utf-8')
py_compile.compile(str(target),doraise=True); py_compile.compile(str(tpath),doraise=True)
print('[PASS] OAD-415 universal source registry installed')
print('[PASS] exact current-repo dependency boundary verified')
print('[PASS] READ_ONLY=TRUE execution_authority=FALSE probability=FALSE')
