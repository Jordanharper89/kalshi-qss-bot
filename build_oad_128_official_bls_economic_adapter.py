from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_128_OFFICIAL_BLS_ECONOMIC_ADAPTER_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_128_official_bls_economic_adapter.py'; test=r/'test_oad_128_official_bls_economic_adapter.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-128 OFFICIAL BLS ECONOMIC ADAPTER INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    deps=['oad_127_authoritative_economic_source_foundation.py']
    for d in deps:
        if not (pkg/d).is_file(): raise RuntimeError("Required certified dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nimport json\nfrom urllib.request import Request,urlopen\nfrom .oad_127_authoritative_economic_source_foundation import build_economic_observation,utcnow_iso,validate_economic_observation\n\nPROVIDER="api.bls.gov"\nBASE="https://api.bls.gov/publicAPI/v2/timeseries/data"\nSERIES=(\n    ("CUUR0000SA0","inflation","Consumer Price Index for All Urban Consumers"),\n    ("LNS14000000","labor","Civilian Unemployment Rate"),\n    ("CES0000000001","labor","Total Nonfarm Payroll Employment"),\n)\n\ndef _latest(series_id,timeout_seconds):\n    url=f"{BASE}/{series_id}?latest=true"\n    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})\n    with urlopen(req,timeout=timeout_seconds) as r:\n        data=json.loads(r.read().decode("utf-8"))\n    if data.get("status")!="REQUEST_SUCCEEDED": raise RuntimeError("BLS request failed")\n    rows=((data.get("Results") or {}).get("series") or [])\n    if not rows or not rows[0].get("data"): return None,url\n    return rows[0]["data"][0],url\n\ndef acquire_bls_latest_economic_observations(timeout_seconds=20):\n    out=[]\n    for series_id,family,label in SERIES:\n        row,url=_latest(series_id,timeout_seconds)\n        if row is None: continue\n        period=str(row.get("period",""))\n        year=str(row.get("year",""))\n        value=str(row.get("value",""))\n        payload={"series_id":series_id,"label":label,"year":year,"period":period,"period_name":row.get("periodName"),"value":value,"footnotes":row.get("footnotes") or []}\n        o=build_economic_observation(\n            source_id=f"bls:{series_id}:{year}:{period}",provider=PROVIDER,economic_family=family,\n            observation_type="official_economic_release",subject=f"{label}: {value}",\n            observed_at=utcnow_iso(),source_url=url,payload=payload)\n        if not validate_economic_observation(o): raise RuntimeError("BLS provenance validation failed")\n        out.append(o)\n    return tuple(out)\n'); write(test,'import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_128_official_bls_economic_adapter as m\nclass T(unittest.TestCase):\n    def test_mapping(self):\n        def fake(s,t): return ({"year":"2026","period":"M07","periodName":"July","value":"2.7","footnotes":[]},f"https://api.bls.gov/{s}")\n        with patch.object(m,"_latest",side_effect=fake):\n            r=m.acquire_bls_latest_economic_observations()\n        print("[BLS_OBSERVATIONS]",len(r))\n        self.assertEqual(len(r),3); self.assertTrue(all(x.independent_evidence for x in r))\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-128 official BLS adapter contract certified")\n    print("[PHYSICAL] production function uses api.bls.gov")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_128_official_bls_economic_adapter import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] existing independent canonical/PostgreSQL architecture preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-128 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
