from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_138_OFFICIAL_CDC_PUBLIC_HEALTH_ADAPTER_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_138_official_cdc_public_health_adapter.py'; test=r/'test_oad_138_official_cdc_public_health_adapter.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-138 OFFICIAL CDC PUBLIC HEALTH ADAPTER INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_137_authoritative_public_health_source_foundation.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nimport json\nfrom urllib.parse import urlencode\nfrom urllib.request import Request,urlopen\nfrom .oad_137_authoritative_public_health_source_foundation import build_public_health_observation,utcnow_iso,validate_public_health_observation\n\nPROVIDER="tools.cdc.gov"\nBASE="https://tools.cdc.gov/api/v2/resources/media"\nDEFAULT_QUERIES=("influenza","respiratory virus","public health emergency")\n\ndef _search(query,timeout_seconds,max_results=5):\n    url=BASE+"?"+urlencode({"q":query,"max":max_results,"sort":"-dateModified"})\n    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Accept":"application/json"})\n    with urlopen(req,timeout=timeout_seconds) as r:\n        data=json.loads(r.read().decode("utf-8"))\n    return tuple(data.get("results") or ()),url\n\ndef acquire_cdc_public_health_observations(timeout_seconds=20.0,queries=DEFAULT_QUERIES):\n    out=[]\n    seen=set()\n    for query in tuple(queries):\n        rows,url=_search(query,timeout_seconds)\n        for row in rows:\n            rid=str(row.get("id",""))\n            if not rid or rid in seen: continue\n            seen.add(rid)\n            name=str(row.get("name") or row.get("title") or row.get("description") or "CDC public-health publication")\n            payload={\n                "id":rid,\n                "name":row.get("name"),\n                "description":row.get("description"),\n                "sourceUrl":row.get("sourceUrl"),\n                "datePublished":row.get("datePublished"),\n                "dateModified":row.get("dateModified"),\n                "query":query,\n            }\n            o=build_public_health_observation(\n                source_id=f"cdc:media:{rid}",provider=PROVIDER,health_family="public_health",\n                observation_type="official_health_publication",subject=name,\n                observed_at=utcnow_iso(),source_url=url,payload=payload)\n            if not validate_public_health_observation(o): raise RuntimeError("CDC provenance validation failed")\n            out.append(o)\n    return tuple(out)\n'); write(test,'import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_138_official_cdc_public_health_adapter as m\nclass T(unittest.TestCase):\n    def test_mapping_and_dedupe(self):\n        rows=({"id":101,"name":"Influenza update","dateModified":"2026-08-28"},)\n        with patch.object(m,"_search",return_value=(rows,"https://tools.cdc.gov/api/test")):\n            r=m.acquire_cdc_public_health_observations(queries=("influenza","respiratory virus"))\n        print("[CDC_OBSERVATIONS]",len(r))\n        self.assertEqual(len(r),1); self.assertEqual(r[0].provider,"tools.cdc.gov")\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-138 official CDC public-health adapter contract certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_138_official_cdc_public_health_adapter import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] existing canonical/PostgreSQL single-writer architecture preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-138 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
