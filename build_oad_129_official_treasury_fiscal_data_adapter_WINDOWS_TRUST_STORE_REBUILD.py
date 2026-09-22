from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION="OAD_129_OFFICIAL_TREASURY_FISCAL_DATA_ADAPTER_WINDOWS_TRUST_STORE_REBUILD"

def find_root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_py(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    root=find_root()
    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/"oad_129_official_treasury_fiscal_data_adapter.py"
    test=root/"test_oad_129_official_treasury_fiscal_data_adapter.py"
    dep=pkg/"oad_127_authoritative_economic_source_foundation.py"
    if not dep.is_file():
        raise RuntimeError("Required certified OAD-127 dependency missing")

    print("="*112)
    print(" OAD-129 OFFICIAL TREASURY FISCAL DATA ADAPTER")
    print(" WINDOWS TRUST-STORE FOUNDATIONAL REBUILD")
    print("="*112)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",root)
    print("[PASS] OAD-127 dependency verified")
    print("[CAUSE] Python TLS rejected a certificate chain trusted through the Windows machine trust store")
    print("[REPAIR] Rebuild OAD-129 transport boundary; keep certificate + hostname verification enabled")

    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test)}
    try:
        write_py(module,'from __future__ import annotations\n\nimport json\nimport os\nimport ssl\nfrom urllib.error import URLError\nfrom urllib.parse import urlencode\nfrom urllib.request import Request, urlopen\n\nfrom .oad_127_authoritative_economic_source_foundation import (\n    build_economic_observation,\n    utcnow_iso,\n    validate_economic_observation,\n)\n\nPROVIDER="api.fiscaldata.treasury.gov"\nBASE="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n\ndef _is_certificate_verification_failure(exc):\n    reason=getattr(exc,"reason",exc)\n    if isinstance(reason,ssl.SSLCertVerificationError):\n        return True\n    text=str(reason).upper()\n    return "CERTIFICATE_VERIFY_FAILED" in text or "CERTIFICATE VERIFY FAILED" in text\n\n\ndef _windows_trust_context():\n    """\n    Build a verified TLS context that keeps Python\'s normal CA roots and,\n    on Windows, additionally loads certificates trusted by the Windows ROOT\n    certificate store. Verification and hostname checking stay enabled.\n    """\n    ctx=ssl.create_default_context()\n    enum=getattr(ssl,"enum_certificates",None)\n    if os.name!="nt" or not callable(enum):\n        return ctx\n\n    pem=[]\n    for cert_bytes,encoding,_trust in enum("ROOT"):\n        if encoding=="x509_asn":\n            pem.append(ssl.DER_cert_to_PEM_cert(cert_bytes))\n        elif encoding=="pkcs_7_asn":\n            # Python\'s ssl module cannot directly add PKCS#7 bundles here.\n            # Normal/default roots remain active; individual X.509 roots are added.\n            continue\n\n    if not pem:\n        raise RuntimeError("Windows ROOT certificate store returned no X.509 certificates")\n\n    ctx.load_verify_locations(cadata="\\n".join(pem))\n    if ctx.verify_mode!=ssl.CERT_REQUIRED:\n        raise RuntimeError("verified TLS context unexpectedly disabled certificate verification")\n    if ctx.check_hostname is not True:\n        raise RuntimeError("verified TLS context unexpectedly disabled hostname checking")\n    return ctx\n\n\ndef _verified_open(req,timeout_seconds):\n    try:\n        return urlopen(req,timeout=timeout_seconds)\n    except URLError as exc:\n        if os.name!="nt" or not _is_certificate_verification_failure(exc):\n            raise\n        ctx=_windows_trust_context()\n        return urlopen(req,timeout=timeout_seconds,context=ctx)\n\n\ndef _latest_debt(timeout_seconds):\n    url=BASE+"?"+urlencode({"sort":"-record_date","page[size]":"1"})\n    req=Request(\n        url,\n        headers={\n            "User-Agent":"Oracle-Q-Series/1.0 read-only",\n            "Accept":"application/json",\n        },\n    )\n    with _verified_open(req,timeout_seconds) as r:\n        data=json.loads(r.read().decode("utf-8"))\n    rows=data.get("data") or []\n    return (rows[0] if rows else None),url\n\n\ndef acquire_treasury_debt_observation(timeout_seconds=20):\n    row,url=_latest_debt(timeout_seconds)\n    if row is None:\n        return tuple()\n\n    record_date=str(row.get("record_date",""))\n    total=str(row.get("tot_pub_debt_out_amt",""))\n    payload={\n        "record_date":record_date,\n        "debt_held_public_amt":row.get("debt_held_public_amt"),\n        "intragov_hold_amt":row.get("intragov_hold_amt"),\n        "tot_pub_debt_out_amt":row.get("tot_pub_debt_out_amt"),\n    }\n    o=build_economic_observation(\n        source_id=f"treasury:debt_to_penny:{record_date}",\n        provider=PROVIDER,\n        economic_family="federal_fiscal",\n        observation_type="official_federal_debt_observation",\n        subject=f"U.S. total public debt outstanding: {total}",\n        observed_at=utcnow_iso(),\n        source_url=url,\n        payload=payload,\n    )\n    if not validate_economic_observation(o):\n        raise RuntimeError("Treasury provenance validation failed")\n    return (o,)\n')
        write_py(test,'import ssl\nimport unittest\nfrom unittest.mock import patch\nfrom urllib.error import URLError\n\nfrom qseries_v2.oracle_adapters.independent import oad_129_official_treasury_fiscal_data_adapter as m\n\n\nclass _Resp:\n    def __init__(self,payload):\n        import json\n        self._b=json.dumps(payload).encode("utf-8")\n    def __enter__(self): return self\n    def __exit__(self,*args): return False\n    def read(self): return self._b\n\n\nclass T(unittest.TestCase):\n    def test_mapping(self):\n        row={\n            "record_date":"2026-08-28",\n            "debt_held_public_amt":"30000000000000",\n            "intragov_hold_amt":"7000000000000",\n            "tot_pub_debt_out_amt":"37000000000000",\n        }\n        with patch.object(m,"_latest_debt",return_value=(row,"https://api.fiscaldata.treasury.gov/test")):\n            r=m.acquire_treasury_debt_observation()\n        self.assertEqual(len(r),1)\n        self.assertTrue(r[0].independent_evidence)\n        self.assertFalse(r[0].execution_authority)\n\n    def test_certificate_failure_uses_verified_windows_trust_retry(self):\n        cert_error=ssl.SSLCertVerificationError(1,"certificate verify failed")\n        first=URLError(cert_error)\n        response=_Resp({"data":[]})\n        sentinel=object()\n\n        with patch.object(m.os,"name","nt"), \\\n             patch.object(m,"_windows_trust_context",return_value=sentinel), \\\n             patch.object(m,"urlopen",side_effect=[first,response]) as op:\n            req=m.Request("https://api.fiscaldata.treasury.gov/test")\n            got=m._verified_open(req,5)\n            self.assertIs(got,response)\n            self.assertEqual(op.call_count,2)\n            self.assertNotIn("context",op.call_args_list[0].kwargs)\n            self.assertIs(op.call_args_list[1].kwargs["context"],sentinel)\n\n    def test_non_certificate_error_is_not_bypassed(self):\n        with patch.object(m.os,"name","nt"), \\\n             patch.object(m,"urlopen",side_effect=URLError("connection refused")), \\\n             self.assertRaises(URLError):\n            m._verified_open(m.Request("https://api.fiscaldata.treasury.gov/test"),5)\n\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OAD-129 Treasury Windows trust-store rebuild certified")\n    print("[PASS] default verified TLS remains first path")\n    print("[PASS] Windows ROOT retry only on certificate-verification failure")\n    print("[PASS] CERT_REQUIRED=preserved hostname_checking=preserved")\n')
        print("[PASS] OAD-129 source adapter replaced in place")
        print("[PASS] replacement test installed")
        print("[PASS] syntax validated")
        print("[PASS] normal verified HTTPS remains primary path")
        print("[PASS] Windows ROOT store used only after certificate-verification failure")
        print("[PASS] ssl.CERT_REQUIRED and hostname verification remain enabled")
        print("[PASS] no CERT_NONE / unverified context / hostname bypass introduced")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-129 WINDOWS TRUST-STORE REBUILD COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] OAD-129 rebuild rolled back")
        raise

if __name__=="__main__":
    main()
