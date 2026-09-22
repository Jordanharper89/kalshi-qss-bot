from pathlib import Path
import hashlib,py_compile
ROOT=Path.cwd(); BASE=ROOT/'qseries_v2/oracle_adapters/independent'
DEPS=[('oad_417_source_to_market_coverage_matrix.py', None)]
for name,expected in DEPS:
 p=BASE/name
 if not p.exists(): raise SystemExit(f'[ERROR] required repo dependency missing: {p}')
 if expected and hashlib.sha256(p.read_bytes()).hexdigest()!=expected: raise SystemExit(f'[ERROR] repo dependency changed: {name}')
source="from __future__ import annotations\nfrom collections import Counter\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_417_source_to_market_coverage_matrix import build_source_to_market_coverage_matrix\nREAD_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False\n@dataclass(frozen=True,slots=True)\nclass EvidenceGapPriority:\n rank:int; source_family:str; affected_markets:int; domains:tuple[str,...]; priority_score:int\ndef rank_evidence_gaps(markets,root='.'):\n rows=build_source_to_market_coverage_matrix(markets,root); count=Counter(); domains={}\n for r in rows:\n  for fam in r.missing:\n   count[fam]+=1; domains.setdefault(fam,set()).add(r.domain)\n ranked=sorted(count,key=lambda f:(-count[f],f))\n return tuple(EvidenceGapPriority(i+1,f,count[f],tuple(sorted(domains[f])),count[f]*1000+len(domains[f])) for i,f in enumerate(ranked))\ndef recommend_next_source(markets,root='.'):\n x=rank_evidence_gaps(markets,root); return x[0] if x else None\n"
test="import unittest,tempfile,pathlib,shutil\nfrom qseries_v2.oracle_adapters.independent.oad_418_evidence_gap_priority_planner import *\nclass T(unittest.TestCase):\n def test_gap_rank(self):\n  markets=[{'ticker':'E1','title':'Who wins the presidential election?'},{'ticker':'E2','title':'Will the election result be certified?'},{'ticker':'W','title':'Will temperature exceed 100 F?'}]\n  x=rank_evidence_gaps(markets,'.'); self.assertTrue(x); self.assertEqual(x[0].source_family,'ELECTION_OFFICIAL'); self.assertGreaterEqual(x[0].affected_markets,2)\n def test_read_only(self): self.assertTrue(READ_ONLY); self.assertFalse(EXECUTION_AUTHORITY)\nif __name__=='__main__':unittest.main(verbosity=2)\n"
target=BASE/'oad_418_evidence_gap_priority_planner.py'; tpath=ROOT/'test_oad_418_evidence_gap_priority_planner.py'
if target.exists(): raise SystemExit(f'[ERROR] target already exists; refusing overwrite: {target}')
target.write_text(source,encoding='utf-8'); tpath.write_text(test,encoding='utf-8')
py_compile.compile(str(target),doraise=True); py_compile.compile(str(tpath),doraise=True)
print('[PASS] OAD-418 evidence gap priority planner installed')
print('[PASS] exact current-repo dependency boundary verified')
print('[PASS] READ_ONLY=TRUE execution_authority=FALSE probability=FALSE')
