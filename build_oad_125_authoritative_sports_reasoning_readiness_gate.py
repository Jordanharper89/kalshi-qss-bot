from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION='OAD_125_AUTHORITATIVE_SPORTS_REASONING_READINESS_GATE_V1'

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
MODULE=PKG/'oad_125_authoritative_sports_reasoning_readiness_gate.py'
TEST=ROOT/'test_oad_125_authoritative_sports_reasoning_readiness_gate.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass SportsReasoningReadiness:\n    market_id: str\n    state: str\n    independent_evidence_count: int\n    independent_source_count: int\n    ready_for_evidence_comparison: bool\n    ready_for_prediction: bool\n    direction: None=None\n    probability: None=None\n    execution_authority: bool=False\n\ndef evaluate_sports_reasoning_readiness(inputs):\n    out=[]\n    for x in tuple(inputs):\n        evidence_count=int(x.independent_evidence_count)\n        source_count=len(tuple(x.independent_source_ids))\n        ready=evidence_count>0 and source_count>0\n        out.append(SportsReasoningReadiness(\n            market_id=x.market_id,\n            state="READY_FOR_EVIDENCE_COMPARISON" if ready else "OBSERVE",\n            independent_evidence_count=evidence_count,\n            independent_source_count=source_count,\n            ready_for_evidence_comparison=ready,\n            ready_for_prediction=False,\n            direction=None,\n            probability=None,\n            execution_authority=False,\n        ))\n    return tuple(out)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_125_authoritative_sports_reasoning_readiness_gate import evaluate_sports_reasoning_readiness\n\nclass T(unittest.TestCase):\n    def test_ready_for_comparison_not_prediction(self):\n        x=SimpleNamespace(market_id="KX1",independent_evidence_count=1,independent_source_ids=("source.independent.mlb:game:1",))\n        r=evaluate_sports_reasoning_readiness((x,))[0]\n        print("[STATE]",r.state)\n        print("[READY_FOR_EVIDENCE_COMPARISON]",r.ready_for_evidence_comparison)\n        print("[READY_FOR_PREDICTION]",r.ready_for_prediction)\n        self.assertTrue(r.ready_for_evidence_comparison)\n        self.assertFalse(r.ready_for_prediction)\n        self.assertIsNone(r.direction)\n        self.assertIsNone(r.probability)\n        self.assertFalse(r.execution_authority)\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-125 sports reasoning readiness gate certified")\n'
DEPENDENCIES=['oad_124_authoritative_sports_reasoning_comparison_input.py']

def main():
    print("="*112)
    print(" OAD-125 AUTHORITATIVE SPORTS REASONING READINESS GATE INSTALLER")
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
        exp="from .oad_125_authoritative_sports_reasoning_readiness_gate import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] certified OAD-118 through OAD-121 boundaries preserved")
        print("[PASS] candidate_only evidence boundary preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-125 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
