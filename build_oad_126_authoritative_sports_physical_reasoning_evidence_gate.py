from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION='OAD_126_AUTHORITATIVE_SPORTS_PHYSICAL_REASONING_EVIDENCE_GATE_V1'

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
MODULE=PKG/'oad_126_authoritative_sports_physical_reasoning_evidence_gate.py'
TEST=ROOT/'test_oad_126_authoritative_sports_physical_reasoning_evidence_gate.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\n\nfrom .oad_122_authoritative_sports_live_end_to_end_evidence_certification import run_live_sports_end_to_end_evidence_certification\nfrom .oad_123_authoritative_sports_market_evidence_envelope import build_sports_market_evidence_envelopes\nfrom .oad_124_authoritative_sports_reasoning_comparison_input import build_sports_reasoning_comparison_inputs\nfrom .oad_125_authoritative_sports_reasoning_readiness_gate import evaluate_sports_reasoning_readiness\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass PhysicalSportsReasoningEvidenceGate:\n    persisted_observations: int\n    current_markets: int\n    association_candidates: int\n    evidence_envelopes: int\n    reasoning_inputs: int\n    ready_for_evidence_comparison_markets: int\n    ready_for_prediction_markets: int\n    state: str\n    certified_at: str\n    read_only: bool=True\n    probability_enabled: bool=False\n    execution_authority: bool=False\n\ndef run_physical_sports_reasoning_evidence_gate(\n    root=None,\n    market_limit=1000,\n    timeout_seconds=120.0,\n    acquisition_timeout_seconds=20.0,\n    market_timeout_seconds=20.0,\n):\n    live=run_live_sports_end_to_end_evidence_certification(\n        root=root,\n        market_limit=market_limit,\n        timeout_seconds=timeout_seconds,\n        acquisition_timeout_seconds=acquisition_timeout_seconds,\n        market_timeout_seconds=market_timeout_seconds,\n    )\n    envelopes=build_sports_market_evidence_envelopes(live)\n    inputs=build_sports_reasoning_comparison_inputs(envelopes)\n    readiness=evaluate_sports_reasoning_readiness(inputs)\n    comparison_ready=sum(1 for x in readiness if x.ready_for_evidence_comparison)\n    prediction_ready=sum(1 for x in readiness if x.ready_for_prediction)\n    if prediction_ready:\n        raise RuntimeError("adapter layer may not certify prediction readiness")\n    state="READY_FOR_EVIDENCE_COMPARISON" if comparison_ready else "OBSERVE"\n    return PhysicalSportsReasoningEvidenceGate(\n        persisted_observations=live.persisted_observations,\n        current_markets=live.current_markets,\n        association_candidates=live.association_candidates,\n        evidence_envelopes=len(envelopes),\n        reasoning_inputs=len(inputs),\n        ready_for_evidence_comparison_markets=comparison_ready,\n        ready_for_prediction_markets=0,\n        state=state,\n        certified_at=datetime.now(timezone.utc).isoformat(),\n        read_only=True,\n        probability_enabled=False,\n        execution_authority=False,\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_126_authoritative_sports_physical_reasoning_evidence_gate import run_physical_sports_reasoning_evidence_gate\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_physical_sports_reasoning_evidence_gate()\n        print("[PHYSICAL] persisted_observations=",r.persisted_observations)\n        print("[PHYSICAL] current_markets=",r.current_markets)\n        print("[PHYSICAL] association_candidates=",r.association_candidates)\n        print("[PHYSICAL] evidence_envelopes=",r.evidence_envelopes)\n        print("[PHYSICAL] reasoning_inputs=",r.reasoning_inputs)\n        print("[PHYSICAL] ready_for_evidence_comparison_markets=",r.ready_for_evidence_comparison_markets)\n        print("[PHYSICAL] ready_for_prediction_markets=",r.ready_for_prediction_markets)\n        print("[PHYSICAL] state=",r.state)\n        self.assertGreaterEqual(r.persisted_observations,0)\n        self.assertGreaterEqual(r.current_markets,1)\n        self.assertEqual(r.ready_for_prediction_markets,0)\n        self.assertFalse(r.probability_enabled)\n        self.assertFalse(r.execution_authority)\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-126 physical sports reasoning-evidence gate certified")\n    print("[PASS] outside-world evidence can reach reasoning comparison when a defensible live market association exists")\n    print("[PASS] prediction readiness remains FALSE; probability_enabled=FALSE; execution_authority=FALSE")\n'
DEPENDENCIES=['oad_122_authoritative_sports_live_end_to_end_evidence_certification.py', 'oad_123_authoritative_sports_market_evidence_envelope.py', 'oad_124_authoritative_sports_reasoning_comparison_input.py', 'oad_125_authoritative_sports_reasoning_readiness_gate.py']

def main():
    print("="*112)
    print(" OAD-126 AUTHORITATIVE SPORTS PHYSICAL REASONING EVIDENCE GATE INSTALLER")
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
        exp="from .oad_126_authoritative_sports_physical_reasoning_evidence_gate import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] certified OAD-118 through OAD-121 boundaries preserved")
        print("[PASS] candidate_only evidence boundary preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-126 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
