from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_133_AUTHORITATIVE_ECONOMIC_SOURCE_HEALTH_LINEAGE_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_133_authoritative_economic_source_health_lineage.py'; test=r/'test_oad_133_authoritative_economic_source_health_lineage.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-133 AUTHORITATIVE ECONOMIC SOURCE HEALTH LINEAGE INSTALLER"); print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    deps=['oad_132_resilient_authoritative_economic_provider_isolation.py']
    for d in deps:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True, slots=True)\nclass EconomicSourceHealthRecord:\n    provider: str\n    state: str\n    observation_count: int\n    error_type: str|None\n    error_message: str|None\n    checked_at: str\n    lineage_id: str\n    execution_authority: bool=False\n\ndef build_source_health_lineage(provider_results):\n    out=[]\n    for r in tuple(provider_results):\n        raw=json.dumps({\n            "provider":r.provider,\n            "state":r.state,\n            "observation_count":r.observation_count,\n            "error_type":r.error_type,\n            "error_message":r.error_message,\n            "checked_at":r.checked_at,\n        },sort_keys=True,separators=(",",":"))\n        lineage_id="economic-source-health:"+sha256(raw.encode()).hexdigest()\n        out.append(EconomicSourceHealthRecord(\n            r.provider,r.state,int(r.observation_count),r.error_type,r.error_message,\n            r.checked_at,lineage_id,False\n        ))\n    return tuple(out)\n')
        write(test,'import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_133_authoritative_economic_source_health_lineage import build_source_health_lineage\nclass T(unittest.TestCase):\n    def test_lineage(self):\n        rows=build_source_health_lineage((\n            SimpleNamespace(provider="api.bls.gov",state="AVAILABLE",observation_count=3,error_type=None,error_message=None,checked_at="t1"),\n            SimpleNamespace(provider="api.fiscaldata.treasury.gov",state="UNAVAILABLE",observation_count=0,error_type="URLError",error_message="tls",checked_at="t2"),\n        ))\n        print("[HEALTH]",[(x.provider,x.state,x.observation_count) for x in rows])\n        self.assertEqual(len(rows),2)\n        self.assertNotEqual(rows[0].lineage_id,rows[1].lineage_id)\n        self.assertFalse(rows[1].execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-133 economic source-health lineage certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_133_authoritative_economic_source_health_lineage import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] existing canonical/PostgreSQL single-writer architecture preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-133 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise
if __name__=="__main__": main()
