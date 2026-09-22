from __future__ import annotations

import json
import os
import ssl
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .oad_127_authoritative_economic_source_foundation import (
    build_economic_observation,
    utcnow_iso,
    validate_economic_observation,
)

PROVIDER="api.fiscaldata.treasury.gov"
BASE="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False


def _is_certificate_verification_failure(exc):
    reason=getattr(exc,"reason",exc)
    if isinstance(reason,ssl.SSLCertVerificationError):
        return True
    text=str(reason).upper()
    return "CERTIFICATE_VERIFY_FAILED" in text or "CERTIFICATE VERIFY FAILED" in text


def _windows_trust_context():
    """
    Build a verified TLS context that keeps Python's normal CA roots and,
    on Windows, additionally loads certificates trusted by the Windows ROOT
    certificate store. Verification and hostname checking stay enabled.
    """
    ctx=ssl.create_default_context()
    enum=getattr(ssl,"enum_certificates",None)
    if os.name!="nt" or not callable(enum):
        return ctx

    pem=[]
    for cert_bytes,encoding,_trust in enum("ROOT"):
        if encoding=="x509_asn":
            pem.append(ssl.DER_cert_to_PEM_cert(cert_bytes))
        elif encoding=="pkcs_7_asn":
            # Python's ssl module cannot directly add PKCS#7 bundles here.
            # Normal/default roots remain active; individual X.509 roots are added.
            continue

    if not pem:
        raise RuntimeError("Windows ROOT certificate store returned no X.509 certificates")

    ctx.load_verify_locations(cadata="\n".join(pem))
    if ctx.verify_mode!=ssl.CERT_REQUIRED:
        raise RuntimeError("verified TLS context unexpectedly disabled certificate verification")
    if ctx.check_hostname is not True:
        raise RuntimeError("verified TLS context unexpectedly disabled hostname checking")
    return ctx


def _verified_open(req,timeout_seconds):
    try:
        return urlopen(req,timeout=timeout_seconds)
    except URLError as exc:
        if os.name!="nt" or not _is_certificate_verification_failure(exc):
            raise
        ctx=_windows_trust_context()
        return urlopen(req,timeout=timeout_seconds,context=ctx)


def _latest_debt(timeout_seconds):
    url=BASE+"?"+urlencode({"sort":"-record_date","page[size]":"1"})
    req=Request(
        url,
        headers={
            "User-Agent":"Oracle-Q-Series/1.0 read-only",
            "Accept":"application/json",
        },
    )
    with _verified_open(req,timeout_seconds) as r:
        data=json.loads(r.read().decode("utf-8"))
    rows=data.get("data") or []
    return (rows[0] if rows else None),url


def acquire_treasury_debt_observation(timeout_seconds=20):
    row,url=_latest_debt(timeout_seconds)
    if row is None:
        return tuple()

    record_date=str(row.get("record_date",""))
    total=str(row.get("tot_pub_debt_out_amt",""))
    payload={
        "record_date":record_date,
        "debt_held_public_amt":row.get("debt_held_public_amt"),
        "intragov_hold_amt":row.get("intragov_hold_amt"),
        "tot_pub_debt_out_amt":row.get("tot_pub_debt_out_amt"),
    }
    o=build_economic_observation(
        source_id=f"treasury:debt_to_penny:{record_date}",
        provider=PROVIDER,
        economic_family="federal_fiscal",
        observation_type="official_federal_debt_observation",
        subject=f"U.S. total public debt outstanding: {total}",
        observed_at=utcnow_iso(),
        source_url=url,
        payload=payload,
    )
    if not validate_economic_observation(o):
        raise RuntimeError("Treasury provenance validation failed")
    return (o,)
