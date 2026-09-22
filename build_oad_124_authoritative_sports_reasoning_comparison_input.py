from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION='OAD_124_AUTHORITATIVE_SPORTS_REASONING_COMPARISON_INPUT_V1'

def find_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def write_py(path,src):
    src=textwrap.dedent(src).lstrip()
    ast.parse(src,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(src,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_124_authoritative_sports_reasoning_comparison_input.py'
TEST=ROOT/'test_oad_124_authoritative_sports_reasoning_comparison_input.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom collections import defaultdict\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass SportsReasoningComparisonInput:\n    market_id: str\n    evidence: tuple\n    independent_source_ids: tuple\n    evidence_count: int\n    independent_evidence_count: int\n    candidate_only: bool\n    direction: None=None\n    probability: None=None\n    execution_authority: bool=False\n\ndef build_sports_reasoning_comparison_inputs(envelopes):\n    groups=defaultdict(list)\n    for e in tuple(envelopes):\n        if e.independent_evidence is not True or e.candidate_only is not True:\n            raise RuntimeError("only independent candidate-only sports evidence may enter reasoning comparison")\n        if e.direction is not None or e.probability is not None:\n            raise RuntimeError("direction/probability must not be manufactured by adapter layer")\n        groups[e.market_id].append(e)\n    out=[]\n    for market_id in sorted(groups):\n        evidence=tuple(groups[market_id])\n        sources=tuple(sorted({e.source_id for e in evidence}))\n        out.append(SportsReasoningComparisonInput(\n            market_id=market_id,\n            evidence=evidence,\n            independent_source_ids=sources,\n            evidence_count=len(evidence),\n            independent_evidence_count=len(evidence),\n            candidate_only=True,\n            direction=None,\n            probability=None,\n            execution_authority=False,\n        ))\n    return tuple(out)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_124_authoritative_sports_reasoning_comparison_input import build_sports_reasoning_comparison_inputs\n\nclass T(unittest.TestCase):\n    def test_grouping(self):\n        e1=SimpleNamespace(market_id="KX1",source_id="source.independent.mlb:game:1",independent_evidence=True,candidate_only=True,direction=None,probability=None)\n        e2=SimpleNamespace(market_id="KX1",source_id="source.independent.mlb:game:2",independent_evidence=True,candidate_only=True,direction=None,probability=None)\n        r=build_sports_reasoning_comparison_inputs((e1,e2))\n        print("[MARKETS]",len(r))\n        print("[EVIDENCE_COUNT]",r[0].evidence_count)\n        print("[INDEPENDENT_SOURCES]",r[0].independent_source_ids)\n        self.assertEqual(len(r),1)\n        self.assertEqual(r[0].evidence_count,2)\n        self.assertIsNone(r[0].direction)\n        self.assertIsNone(r[0].probability)\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-124 authoritative sports reasoning comparison input certified")\n'
DEPENDENCIES=['oad_123_authoritative_sports_market_evidence_envelope.py']

def main():
    print("="*112)
    print(" OAD-124 AUTHORITATIVE SPORTS REASONING COMPARISON INPUT INSTALLER")
    print("="*112)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for dep in DEPENDENCIES:
        p=PKG/dep
        if not p.is_file(): raise RuntimeError("Required certified dependency missing: "+str(p))
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write_py(MODULE,MODULE_SOURCE)
        write_py(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from .oad_124_authoritative_sports_reasoning_comparison_input import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] certified OAD-118 through OAD-121 boundaries preserved")
        print("[PASS] candidate_only evidence boundary preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-124 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
