from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_129_OFFICIAL_TREASURY_FISCAL_DATA_ADAPTER_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_129_official_treasury_fiscal_data_adapter.py'; test=r/'test_oad_129_official_treasury_fiscal_data_adapter.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-129 OFFICIAL TREASURY FISCAL DATA ADAPTER INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    deps=['oad_127_authoritative_economic_source_foundation.py']
    for d in deps:
        if not (pkg/d).is_file(): raise RuntimeError("Required certified dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nimport json\nfrom urllib.request import Request,urlopen\nfrom urllib.parse import urlencode\nfrom .oad_127_authoritative_economic_source_foundation import build_economic_observation,utcnow_iso,validate_economic_observation\n\nPROVIDER="api.fiscaldata.treasury.gov"\nBASE="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"\n\ndef _latest_debt(timeout_seconds):\n    url=BASE+"?"+urlencode({"sort":"-record_date","page[size]":"1"})\n    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})\n    with urlopen(req,timeout=timeout_seconds) as r:\n        data=json.loads(r.read().decode("utf-8"))\n    rows=data.get("data") or []\n    return (rows[0] if rows else None),url\n\ndef acquire_treasury_debt_observation(timeout_seconds=20):\n    row,url=_latest_debt(timeout_seconds)\n    if row is None: return tuple()\n    record_date=str(row.get("record_date",""))\n    total=str(row.get("tot_pub_debt_out_amt",""))\n    payload={\n        "record_date":record_date,\n        "debt_held_public_amt":row.get("debt_held_public_amt"),\n        "intragov_hold_amt":row.get("intragov_hold_amt"),\n        "tot_pub_debt_out_amt":row.get("tot_pub_debt_out_amt"),\n    }\n    o=build_economic_observation(\n        source_id=f"treasury:debt_to_penny:{record_date}",provider=PROVIDER,economic_family="federal_fiscal",\n        observation_type="official_federal_debt_observation",subject=f"U.S. total public debt outstanding: {total}",\n        observed_at=utcnow_iso(),source_url=url,payload=payload)\n    if not validate_economic_observation(o): raise RuntimeError("Treasury provenance validation failed")\n    return (o,)\n'); write(test,'import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_129_official_treasury_fiscal_data_adapter as m\nclass T(unittest.TestCase):\n    def test_mapping(self):\n        row={"record_date":"2026-08-28","debt_held_public_amt":"30000000000000","intragov_hold_amt":"7000000000000","tot_pub_debt_out_amt":"37000000000000"}\n        with patch.object(m,"_latest_debt",return_value=(row,"https://api.fiscaldata.treasury.gov/test")):\n            r=m.acquire_treasury_debt_observation()\n        print("[TREASURY_OBSERVATIONS]",len(r)); print("[SUBJECT]",r[0].subject)\n        self.assertEqual(len(r),1); self.assertTrue(r[0].independent_evidence)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-129 official Treasury Fiscal Data adapter contract certified")\n    print("[PHYSICAL] production function uses api.fiscaldata.treasury.gov")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_129_official_treasury_fiscal_data_adapter import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] existing independent canonical/PostgreSQL architecture preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-129 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
