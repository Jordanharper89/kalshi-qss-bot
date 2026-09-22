from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_178_CRYPTO_EXPERIENCE_EVIDENCE_LINEAGE_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\ndef _h(v):\n    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\n\n@dataclass(frozen=True,slots=True)\nclass CryptoExperienceEvidenceLineage:\n    experience_id:str\n    asset:str\n    evidence_hash:str\n    condition_hash:str\n    source_families:tuple\n    market_native_metric_names:tuple\n    independent_metric_names:tuple\n    comparable_metric_names:tuple\n    lineage_hash:str\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef build_crypto_experience_evidence_lineage(candidate):\n    source_families=tuple(sorted({x[0] for x in candidate.condition_vector}))\n    market_native=tuple(sorted(x[1] for x in candidate.condition_vector if x[0]=="coinbase"))\n    independent=tuple(sorted(x[1] for x in candidate.condition_vector if x[0]!="coinbase"))\n    comparable=tuple(sorted(x[1] for x in candidate.temporal_vector if bool(x[5])))\n    raw={\n        "experience_id":candidate.experience_id,"asset":candidate.asset,\n        "evidence_hash":candidate.evidence_hash,"condition_hash":candidate.condition_hash,\n        "source_families":source_families,"market_native_metric_names":market_native,\n        "independent_metric_names":independent,"comparable_metric_names":comparable,\n        "read_only":True,"execution_authority":False,\n    }\n    return CryptoExperienceEvidenceLineage(\n        candidate.experience_id,candidate.asset,candidate.evidence_hash,candidate.condition_hash,\n        source_families,market_native,independent,comparable,_h(raw),True,False\n    )\n\ndef verify_crypto_experience_evidence_lineage(x):\n    raw={\n        "experience_id":x.experience_id,"asset":x.asset,"evidence_hash":x.evidence_hash,\n        "condition_hash":x.condition_hash,"source_families":x.source_families,\n        "market_native_metric_names":x.market_native_metric_names,\n        "independent_metric_names":x.independent_metric_names,\n        "comparable_metric_names":x.comparable_metric_names,\n        "read_only":True,"execution_authority":False,\n    }\n    return x.read_only and not x.execution_authority and x.lineage_hash==_h(raw)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_178_crypto_experience_evidence_lineage import build_crypto_experience_evidence_lineage,verify_crypto_experience_evidence_lineage\nclass T(unittest.TestCase):\n    def test_lineage(self):\n        c=SimpleNamespace(experience_id="e1",asset="BTC",evidence_hash="a"*64,condition_hash="b"*64,\n            condition_vector=(("coinbase","spot_price",1.0,"OBSERVED"),("bitcoin","fastest_fee_rate",10.0,"ELEVATED")),\n            temporal_vector=(("coinbase","spot_price","INCREASED",1.0,2.0,True),("bitcoin","fastest_fee_rate","UNCHANGED",0.0,0.0,True)))\n        x=build_crypto_experience_evidence_lineage(c)\n        print("[SOURCES]",x.source_families)\n        print("[COMPARABLE]",x.comparable_metric_names)\n        self.assertTrue(verify_crypto_experience_evidence_lineage(x))\n        self.assertEqual(x.source_families,("bitcoin","coinbase"))\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-178 crypto experience evidence lineage certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_178_crypto_experience_evidence_lineage.py'; test=r/'test_oad_178_crypto_experience_evidence_lineage.py'; init=pkg/"__init__.py"
    print("="*118); print(" OAD-178 CRYPTO EXPERIENCE EVIDENCE LINEAGE INSTALLER"); print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_177_crypto_historical_experience_candidate.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in []:
        if not (r/dep).is_file(): raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_178_crypto_experience_evidence_lineage import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-178 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
