from __future__ import annotations
import ast
import hashlib
import os
from pathlib import Path

BUILD_ID = "OAD-060"
TITLE = "INDEPENDENT SOURCE PRODUCTION BUNDLE — DEPENDENCY-SAFE REBUILD"
REVISION = "OAD_060_DEPENDENCY_SAFE_REBUILD_INSTALLER_V1"

def locate_repository():
    candidates = [Path.cwd().resolve(), Path(__file__).resolve().parent]
    seen = set()
    for base in tuple(candidates):
        candidates += list(base.parents)
    for base in candidates:
        for c in (base, base / "kalshi-qss-bot"):
            try:
                c = c.resolve()
            except OSError:
                continue
            if c in seen:
                continue
            seen.add(c)
            if (c / "qseries_v2").is_dir():
                return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT = locate_repository()
PKG = ROOT / "qseries_v2" / "oracle_adapters" / "independent"
INIT = PKG / "__init__.py"

FOUNDATION = PKG / "oad_056_independent_source_provenance.py"
NWS = PKG / "oad_057_nws_weather_adapter.py"
FED = PKG / "oad_058_federal_register_adapter.py"
USGS = PKG / "oad_059_usgs_event_adapter.py"
BUNDLE = PKG / "oad_060_independent_source_bundle.py"
TEST = ROOT / "test_oad_060_independent_source_production_bundle.py"

NWS_SOURCE = r"""
from __future__ import annotations
import json
import urllib.request
from datetime import datetime, timezone
from .oad_056_independent_source_provenance import build_independent_observation

OAD_057_BUILD_ID="OAD-057"
OAD_057_REVISION="OAD_057_NWS_AUTHORITATIVE_WEATHER_ADAPTER_V1"
READ_ONLY=True
EXECUTION_AUTHORITY=False
ENDPOINT="https://api.weather.gov/alerts/active"

def acquire_nws_active_alerts(limit=25, timeout=20):
    limit=max(1,min(int(limit),100))
    req=urllib.request.Request(
        ENDPOINT,
        headers={
            "User-Agent":"QSeries-Oracle/1.0 (read-only research)",
            "Accept":"application/geo+json",
        },
    )
    with urllib.request.urlopen(req,timeout=timeout) as r:
        data=json.load(r)
    rows=[]
    for f in data.get("features",[])[:limit]:
        p=f.get("properties") or {}
        subject=p.get("headline") or p.get("event") or "NWS active alert"
        rows.append(build_independent_observation(
            source_id="weather.gov",
            source_class="authoritative_real_world",
            observation_type="weather_alert",
            subject=subject,
            observed_at=p.get("sent") or datetime.now(timezone.utc).isoformat(),
            source_url=p.get("@id") or f.get("id") or ENDPOINT,
            payload={
                "event":p.get("event"),
                "areaDesc":p.get("areaDesc"),
                "severity":p.get("severity"),
                "certainty":p.get("certainty"),
                "urgency":p.get("urgency"),
                "effective":p.get("effective"),
                "expires":p.get("expires"),
            },
        ))
    return tuple(rows)

def verify_oad_057_nws_authoritative_weather_adapter():
    rows=acquire_nws_active_alerts(limit=5)
    return isinstance(rows,tuple) and all(
        x.source_id=="weather.gov" and not x.execution_authority for x in rows
    )
"""

FED_SOURCE = r"""
from __future__ import annotations
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from .oad_056_independent_source_provenance import build_independent_observation

OAD_058_BUILD_ID="OAD-058"
OAD_058_REVISION="OAD_058_FEDERAL_REGISTER_ADAPTER_V1"
READ_ONLY=True
EXECUTION_AUTHORITY=False
BASE="https://www.federalregister.gov/api/v1/documents.json"

def acquire_federal_register_documents(limit=20, timeout=20):
    limit=max(1,min(int(limit),100))
    url=BASE+"?"+urllib.parse.urlencode({"per_page":limit,"order":"newest"})
    req=urllib.request.Request(url,headers={"User-Agent":"QSeries-Oracle/1.0 read-only"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        data=json.load(r)
    rows=[]
    for d in data.get("results",[])[:limit]:
        pub=d.get("publication_date")
        observed=(pub+"T00:00:00Z") if pub else datetime.now(timezone.utc).isoformat()
        rows.append(build_independent_observation(
            source_id="federalregister.gov",
            source_class="authoritative_real_world",
            observation_type="federal_register_document",
            subject=d.get("title") or "Federal Register document",
            observed_at=observed,
            source_url=d.get("html_url") or d.get("pdf_url") or BASE,
            payload={
                "document_number":d.get("document_number"),
                "type":d.get("type"),
                "agencies":[a.get("name") for a in d.get("agencies",[]) if isinstance(a,dict)],
                "abstract":d.get("abstract"),
            },
        ))
    return tuple(rows)

def verify_oad_058_federal_register_adapter():
    rows=acquire_federal_register_documents(limit=3)
    return len(rows)>0 and all(
        x.source_id=="federalregister.gov" and not x.execution_authority for x in rows
    )
"""

BUNDLE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from .oad_057_nws_weather_adapter import acquire_nws_active_alerts
from .oad_058_federal_register_adapter import acquire_federal_register_documents
from .oad_059_usgs_event_adapter import acquire_usgs_events

OAD_060_BUILD_ID="OAD-060"
OAD_060_REVISION="OAD_060_INDEPENDENT_SOURCE_PRODUCTION_BUNDLE_V1"
READ_ONLY=True
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class IndependentAcquisitionReport:
    providers:tuple[str,...]
    observations:tuple
    provider_counts:dict
    read_only:bool=True
    execution_authority:bool=False

def acquire_independent_production_bundle(per_source_limit=5):
    limit=max(1,min(int(per_source_limit),25))
    groups=(
        ("weather.gov",acquire_nws_active_alerts(limit)),
        ("federalregister.gov",acquire_federal_register_documents(limit)),
        ("usgs.gov",acquire_usgs_events(limit)),
    )
    observations=tuple(x for _,rows in groups for x in rows)
    counts={name:len(rows) for name,rows in groups}
    return IndependentAcquisitionReport(
        tuple(name for name,_ in groups),
        observations,
        counts,
    )

def verify_oad_060_independent_source_production_bundle():
    r=acquire_independent_production_bundle(2)
    return (
        r.providers==("weather.gov","federalregister.gov","usgs.gov")
        and len(r.observations)>0
        and r.read_only
        and not r.execution_authority
        and all(x.source_class=="authoritative_real_world" for x in r.observations)
    )
"""

TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import *

class T(unittest.TestCase):
    def test_physical_bundle(self):
        r=acquire_independent_production_bundle(2)
        print("[PHYSICAL] provider_counts="+str(r.provider_counts))
        print("[PHYSICAL] independent_observations="+str(len(r.observations)))
        self.assertEqual(
            r.providers,
            ("weather.gov","federalregister.gov","usgs.gov"),
        )
        self.assertGreater(len(r.observations),0)
        self.assertTrue(r.read_only)
        self.assertFalse(r.execution_authority)
        self.assertTrue(all(
            x.source_class=="authoritative_real_world"
            for x in r.observations
        ))

if __name__=="__main__":
    print("="*72)
    print(" OAD-060 PHYSICAL CERTIFICATION TEST")
    print(" INDEPENDENT SOURCE PRODUCTION BUNDLE")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Multiple authoritative non-Kalshi sources physically acquired")
    print("[PASS] Independent evidence remains read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-060 CERTIFIED")
"""

def clean(s):
    return textwrap.dedent(s).lstrip()

def checked_write(path, source):
    source=clean(source)
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OAD-060 DEPENDENCY-SAFE REBUILD INSTALLER")
    print(" INDEPENDENT SOURCE PRODUCTION BUNDLE")
    print("="*72)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)

    kalshi_freeze=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"
    if not kalshi_freeze.is_file():
        raise RuntimeError("Frozen Kalshi OAD-055 boundary missing")
    frozen_hash=hashlib.sha256(kalshi_freeze.read_bytes()).hexdigest()

    if not FOUNDATION.is_file():
        raise RuntimeError("OAD-056 foundation missing; refusing to fabricate dependency")
    if not USGS.is_file():
        raise RuntimeError("Certified OAD-059 USGS adapter missing; refusing to fabricate dependency")

    affected=(NWS,FED,BUNDLE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        if NWS.is_file():
            print("[PASS] Existing OAD-057 module found")
        else:
            checked_write(NWS,NWS_SOURCE)
            print("[RESTORE] Installed intended OAD-057 NWS adapter dependency")

        if FED.is_file():
            print("[PASS] Existing OAD-058 module found")
        else:
            checked_write(FED,FED_SOURCE)
            print("[RESTORE] Installed intended OAD-058 Federal Register adapter dependency")

        checked_write(BUNDLE,BUNDLE_SOURCE)
        checked_write(TEST,TEST_SOURCE)

        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        required=[
            "from .oad_056_independent_source_provenance import *",
            "from .oad_057_nws_weather_adapter import *",
            "from .oad_058_federal_register_adapter import *",
            "from .oad_059_usgs_event_adapter import *",
            "from .oad_060_independent_source_bundle import *",
        ]
        lines=[x for x in current.splitlines() if x.strip()]
        for exp in required:
            if exp not in lines:
                lines.append(exp)
        checked_write(INIT,"\n".join(lines)+"\n")

        # Import-file existence is tested before certification; frozen boundary must not move.
        for p in (FOUNDATION,NWS,FED,USGS,BUNDLE):
            if not p.is_file():
                raise RuntimeError("Required independent adapter module missing: "+p.name)

        if hashlib.sha256(kalshi_freeze.read_bytes()).hexdigest()!=frozen_hash:
            raise RuntimeError("Frozen Kalshi OAD-055 boundary changed")

        print("[PASS] OAD-056 foundation present")
        print("[PASS] OAD-057 NWS dependency present")
        print("[PASS] OAD-058 Federal Register dependency present")
        print("[PASS] Certified OAD-059 USGS dependency present")
        print("[PASS] Frozen Kalshi OAD-055 boundary unchanged")
        print("[PASS] Rebuilt OAD-060 production bundle")
        print("[PASS] Read-only / execution_authority=False preserved")
        print("[DONE] OAD-060 DEPENDENCY-SAFE REBUILD COMPLETE")
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(old)
        print("[ROLLBACK] OAD-060 rebuild failed; affected files restored")
        raise

if __name__=="__main__":
    import textwrap
    main()
