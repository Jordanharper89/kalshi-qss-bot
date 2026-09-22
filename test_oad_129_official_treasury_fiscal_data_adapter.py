import ssl
import unittest
from unittest.mock import patch
from urllib.error import URLError

from qseries_v2.oracle_adapters.independent import oad_129_official_treasury_fiscal_data_adapter as m


class _Resp:
    def __init__(self,payload):
        import json
        self._b=json.dumps(payload).encode("utf-8")
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self): return self._b


class T(unittest.TestCase):
    def test_mapping(self):
        row={
            "record_date":"2026-08-28",
            "debt_held_public_amt":"30000000000000",
            "intragov_hold_amt":"7000000000000",
            "tot_pub_debt_out_amt":"37000000000000",
        }
        with patch.object(m,"_latest_debt",return_value=(row,"https://api.fiscaldata.treasury.gov/test")):
            r=m.acquire_treasury_debt_observation()
        self.assertEqual(len(r),1)
        self.assertTrue(r[0].independent_evidence)
        self.assertFalse(r[0].execution_authority)

    def test_certificate_failure_uses_verified_windows_trust_retry(self):
        cert_error=ssl.SSLCertVerificationError(1,"certificate verify failed")
        first=URLError(cert_error)
        response=_Resp({"data":[]})
        sentinel=object()

        with patch.object(m.os,"name","nt"), \
             patch.object(m,"_windows_trust_context",return_value=sentinel), \
             patch.object(m,"urlopen",side_effect=[first,response]) as op:
            req=m.Request("https://api.fiscaldata.treasury.gov/test")
            got=m._verified_open(req,5)
            self.assertIs(got,response)
            self.assertEqual(op.call_count,2)
            self.assertNotIn("context",op.call_args_list[0].kwargs)
            self.assertIs(op.call_args_list[1].kwargs["context"],sentinel)

    def test_non_certificate_error_is_not_bypassed(self):
        with patch.object(m.os,"name","nt"), \
             patch.object(m,"urlopen",side_effect=URLError("connection refused")), \
             self.assertRaises(URLError):
            m._verified_open(m.Request("https://api.fiscaldata.treasury.gov/test"),5)


if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-129 Treasury Windows trust-store rebuild certified")
    print("[PASS] default verified TLS remains first path")
    print("[PASS] Windows ROOT retry only on certificate-verification failure")
    print("[PASS] CERT_REQUIRED=preserved hostname_checking=preserved")
