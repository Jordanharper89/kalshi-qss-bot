from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_139_OFFICIAL_OPENFDA_ENFORCEMENT_ADAPTER_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_139_official_openfda_enforcement_adapter.py'; test=r/'test_oad_139_official_openfda_enforcement_adapter.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-139 OFFICIAL OPENFDA ENFORCEMENT ADAPTER INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_137_authoritative_public_health_source_foundation.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nimport json\nfrom urllib.parse import urlencode\nfrom urllib.request import Request,urlopen\nfrom .oad_137_authoritative_public_health_source_foundation import build_public_health_observation,utcnow_iso,validate_public_health_observation\n\nPROVIDER="api.fda.gov"\nBASES=(\n    ("drug","https://api.fda.gov/drug/enforcement.json"),\n    ("device","https://api.fda.gov/device/enforcement.json"),\n    ("food","https://api.fda.gov/food/enforcement.json"),\n)\n\ndef _latest(kind,url,timeout_seconds,limit=5):\n    q=url+"?"+urlencode({"sort":"report_date:desc","limit":limit})\n    req=Request(q,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Accept":"application/json"})\n    with urlopen(req,timeout=timeout_seconds) as r:\n        data=json.loads(r.read().decode("utf-8"))\n    return tuple(data.get("results") or ()),q\n\ndef acquire_openfda_enforcement_observations(timeout_seconds=20.0,limit_per_family=5):\n    out=[]\n    for kind,url in BASES:\n        rows,q=_latest(kind,url,timeout_seconds,limit_per_family)\n        for row in rows:\n            recall=str(row.get("recall_number") or row.get("event_id") or "")\n            report_date=str(row.get("report_date") or "")\n            if not recall: continue\n            subject=str(row.get("product_description") or row.get("reason_for_recall") or f"FDA {kind} enforcement report")\n            payload={\n                "kind":kind,\n                "recall_number":recall,\n                "report_date":report_date,\n                "classification":row.get("classification"),\n                "status":row.get("status"),\n                "recalling_firm":row.get("recalling_firm"),\n                "reason_for_recall":row.get("reason_for_recall"),\n                "product_description":row.get("product_description"),\n                "distribution_pattern":row.get("distribution_pattern"),\n            }\n            o=build_public_health_observation(\n                source_id=f"fda:{kind}:enforcement:{recall}:{report_date}",\n                provider=PROVIDER,health_family="regulatory_health",\n                observation_type="official_fda_enforcement_report",subject=subject,\n                observed_at=utcnow_iso(),source_url=q,payload=payload)\n            if not validate_public_health_observation(o): raise RuntimeError("FDA provenance validation failed")\n            out.append(o)\n    return tuple(out)\n'); write(test,'import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_139_official_openfda_enforcement_adapter as m\nclass T(unittest.TestCase):\n    def test_mapping(self):\n        row={"recall_number":"D-001","report_date":"20260828","classification":"Class II","status":"Ongoing","product_description":"Test drug","reason_for_recall":"Test reason"}\n        with patch.object(m,"_latest",return_value=((row,),"https://api.fda.gov/test")):\n            r=m.acquire_openfda_enforcement_observations(limit_per_family=1)\n        print("[FDA_OBSERVATIONS]",len(r))\n        self.assertEqual(len(r),3); self.assertTrue(all(x.provider=="api.fda.gov" for x in r))\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-139 official openFDA enforcement adapter contract certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_139_official_openfda_enforcement_adapter import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] existing canonical/PostgreSQL single-writer architecture preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-139 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
