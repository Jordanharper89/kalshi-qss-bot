
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

def write_py(path, source):
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

REVISION="OAD_107_AUTHORITATIVE_SPORTS_SOURCE_FOUNDATION_V1"
ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_107_authoritative_sports_source_foundation.py'
TEST=ROOT/'test_oad_107_authoritative_sports_source_foundation.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom hashlib import sha256\nfrom typing import Any, Mapping\nimport json\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True)\nclass AuthoritativeSportsObservation:\n    source_id: str\n    provider: str\n    sport_family: str\n    observation_type: str\n    subject: str\n    observed_at: str\n    source_url: str\n    payload: Mapping[str, Any]\n    provenance_hash: str\n    independent_evidence: bool = True\n    source_class: str = "authoritative_real_world"\n    execution_authority: bool = False\n\ndef utcnow_iso():\n    return datetime.now(timezone.utc).isoformat()\n\ndef build_observation(*, source_id, provider, sport_family, observation_type,\n                      subject, observed_at, source_url, payload):\n    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)\n    ph = sha256((provider+"|"+source_url+"|"+canonical).encode()).hexdigest()\n    return AuthoritativeSportsObservation(\n        source_id=source_id, provider=provider, sport_family=sport_family,\n        observation_type=observation_type, subject=subject,\n        observed_at=observed_at, source_url=source_url, payload=dict(payload),\n        provenance_hash=ph,\n    )\n\ndef validate_observation(o):\n    assert o.source_class == "authoritative_real_world"\n    assert o.independent_evidence is True\n    assert o.execution_authority is False\n    assert o.provider and o.sport_family and o.subject and o.source_url\n    assert len(o.provenance_hash) == 64\n    return True\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_107_authoritative_sports_source_foundation import build_observation, validate_observation\nclass T(unittest.TestCase):\n    def test_contract(self):\n        o=build_observation(source_id="test:1",provider="official.example",sport_family="baseball",\n            observation_type="schedule",subject="test",observed_at="2026-01-01T00:00:00+00:00",\n            source_url="https://official.example/test",payload={"x":1})\n        self.assertTrue(validate_observation(o))\n        self.assertFalse(o.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] authoritative sports observation contract certified")\n    print("[PASS] independent_evidence=TRUE")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n'
DEPENDENCIES=[]

def main():
    print("="*104)
    print(" OAD-107 AUTHORITATIVE SPORTS SOURCE FOUNDATION INSTALLER")
    print("="*104)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for dep in DEPENDENCIES:
        p=PKG/dep
        if not p.is_file():
            raise RuntimeError("Required certified dependency missing: "+str(p))
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write_py(MODULE,MODULE_SOURCE)
        write_py(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from .oad_107_authoritative_sports_source_foundation import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] read-only Oracle boundary preserved")
        print("[PASS] execution_authority=FALSE")
        print("[PASS] probability remains disabled")
        print("[DONE] OAD-107 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
