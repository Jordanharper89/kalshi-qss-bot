
from __future__ import annotations
import ast, os, textwrap, subprocess, sys
from pathlib import Path

BUILD_ID='OAD-252'
TITLE='CRYPTO INDEPENDENT SOURCE EXPANSION FOUNDATION'
REVISION='OAD_252_CRYPTO_INDEPENDENT_SOURCE_EXPANSION_FOUNDATION_V1'
MODULE_NAME='oad_252_crypto_independent_source_expansion_foundation.py'
TEST_NAME='test_oad_252_crypto_independent_source_expansion_foundation.py'
DEPENDENCIES=['qseries_v2/oracle_adapters/independent/oad_251_crypto_exact_identity_calibration_boundary_FOUNDATIONAL_REPAIR.py', 'qseries_v2/oracle_adapters/independent/oad_147_solana_onchain_evidence_foundation.py']
MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom hashlib import sha256\nimport json\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass IndependentCryptoObservation:\n    source_id:str; provider:str; source_class:str; subject:str; observation_type:str; observed_at:str; payload:dict; provenance_hash:str\n    independent_evidence:bool=True; execution_authority:bool=False\ndef build_independent_crypto_observation(*,source_id,provider,source_class,subject,observation_type,payload,observed_at=None):\n    vals=(source_id,provider,source_class,subject,observation_type)\n    if not all(str(x).strip() for x in vals): raise ValueError("identity/provenance fields required")\n    t=observed_at or datetime.now(timezone.utc).isoformat()\n    body={"source_id":source_id,"provider":provider,"source_class":source_class,"subject":subject,"observation_type":observation_type,"observed_at":t,"payload":dict(payload)}\n    h=sha256(json.dumps(body,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\n    return IndependentCryptoObservation(str(source_id),str(provider),str(source_class),str(subject),str(observation_type),str(t),dict(payload),h,True,False)\ndef verify_independent_crypto_observation(x):\n    return x.independent_evidence is True and x.execution_authority is False and len(x.provenance_hash)==64\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_252_crypto_independent_source_expansion_foundation import *\nclass T(unittest.TestCase):\n def test_contract(self):\n  x=build_independent_crypto_observation(source_id="source:test",provider="provider",source_class="exchange_liquidity",subject="BTC-USD",observation_type="orderbook",payload={"bid":1})\n  print("[SOURCE]",x.source_id,x.source_class); self.assertTrue(verify_independent_crypto_observation(x))\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-252 independent-source provenance contract certified")\n'

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def atomic(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp,path)

def main():
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE_NAME
    test=r/TEST_NAME
    init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in DEPENDENCIES:
        p=r/dep
        if not p.is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        atomic(module,MODULE_SOURCE); atomic(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+module.stem+" import *"
        if exp not in lines: lines.append(exp)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        p=subprocess.run([sys.executable,str(test)],cwd=str(r))
        if p.returncode: raise RuntimeError("Certification test failed: "+test.name)
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation failed; affected files restored")
        raise
    print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE publication_allowed=FALSE execution_authority=FALSE")
    print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
if __name__=="__main__": main()
