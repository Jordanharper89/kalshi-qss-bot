from __future__ import annotations
import os,sys,subprocess
from pathlib import Path

REVISION="OAD_218_EXISTING_OCL_STATE_HASH_ENVELOPE_IDENTITY_SAFE_REBUILD"
EXPECTED_INSTALLER="build_oad_218_existing_ocl_state_hash_envelope_IDENTITY_SAFE_REBUILD.py"
MODULE_NAME="oad_218_existing_ocl_state_hash_envelope.py"
TEST_NAME="test_oad_218_existing_ocl_state_hash_envelope.py"

MODULE=r"""
from __future__ import annotations
from dataclasses import asdict,is_dataclass,dataclass
from hashlib import sha256
import json

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

def _normalize(value):
    if is_dataclass(value):
        return _normalize(asdict(value))
    if isinstance(value,dict):
        return {str(k):_normalize(v) for k,v in sorted(value.items(),key=lambda x:str(x[0]))}
    if isinstance(value,(list,tuple)):
        return [_normalize(v) for v in value]
    return value

def certified_state_hash(capability,state):
    if state is None:
        raise ValueError("physical certified state required")
    body={"capability":str(capability),"state":_normalize(state)}
    return sha256(json.dumps(body,sort_keys=True,separators=(",",":"),default=str).encode("utf-8")).hexdigest()

@dataclass(frozen=True,slots=True)
class StateHashEnvelope:
    capability:str
    state_hash:str
    evidence_present:bool=True
    fabricated:bool=False
    read_only:bool=True
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def envelope(capability,state):
    return StateHashEnvelope(str(capability),certified_state_hash(capability,state))
"""

TEST=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_218_existing_ocl_state_hash_envelope import (
    envelope,certified_state_hash,
)

class T(unittest.TestCase):
    def test_deterministic_hash(self):
        a=envelope("maturity",{"b":2,"a":1})
        b=envelope("maturity",{"a":1,"b":2})
        print("[HASH]",a.state_hash)
        self.assertEqual(a.state_hash,b.state_hash)
        self.assertEqual(len(a.state_hash),64)
        self.assertFalse(a.fabricated)
        self.assertFalse(a.probability_enabled)
        self.assertFalse(a.execution_authority)

    def test_missing_state_rejected(self):
        with self.assertRaises(ValueError):
            certified_state_hash("calibration",None)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-218 deterministic physical-state hash envelope certified")
"""

def root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for candidate in (base,base/"kalshi-qss-bot",*base.parents):
            if (candidate/"qseries_v2").is_dir():
                return candidate
    raise RuntimeError("Could not locate Q Series repository")

def write_atomic(path,source):
    path.parent.mkdir(parents=True,exist_ok=True)
    compile(source,str(path),"exec")
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    if Path(__file__).name != EXPECTED_INSTALLER:
        raise RuntimeError(
            f"Installer identity mismatch: expected {EXPECTED_INSTALLER}, got {Path(__file__).name}"
        )

    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE_NAME
    test=r/TEST_NAME
    dep=pkg/"oad_217_certified_ocl_state_contract_resolution.py"

    print("="*108)
    print(" OAD-218 EXISTING OCL PHYSICAL STATE HASH ENVELOPE — IDENTITY-SAFE REBUILD")
    print("="*108)
    print("[BOOT]",REVISION)
    print("[INSTALLER]",Path(__file__).name)
    print("[ROOT]",r)

    if not dep.is_file():
        raise RuntimeError("Required certified OAD-217 dependency missing: "+str(dep))
    print("[PASS] OAD-217 dependency verified")
    print("[PASS] installer identity verified as OAD-218")

    old={x:(x.read_bytes() if x.exists() else None) for x in (module,test)}
    try:
        write_atomic(module,MODULE)
        write_atomic(test,TEST)
        print("[PASS] OAD-218 production module installed:",module.relative_to(r))
        print("[PASS] OAD-218 certification test installed:",test.name)

        q=subprocess.run([sys.executable,str(test)],cwd=str(r))
        if q.returncode:
            raise RuntimeError("OAD-218 certification test failed")

        print("[PASS] missing physical states cannot generate hashes")
        print("[PASS] deterministic state hashing certified")
        print("[PASS] probability=FALSE direction=FALSE execution=FALSE")
        print("[DONE] OAD-218 INSTALLATION COMPLETE")
    except Exception:
        for x,data in old.items():
            if data is None:
                if x.exists():
                    x.unlink()
            else:
                x.write_bytes(data)
        print("[ROLLBACK] OAD-218 rebuild rolled back")
        raise

if __name__=="__main__":
    main()
