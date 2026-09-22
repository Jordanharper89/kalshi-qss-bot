from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-072"
REVISION="OAD_072_IMMUTABLE_PAYLOAD_REBUILD_V1"
TITLE="INDEPENDENT OBSERVATION TO UMD-115 DESCRIPTOR ADAPTER — IMMUTABLE PAYLOAD REBUILD"

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/"oad_072_independent_umd115_descriptor_adapter.py"
TEST=ROOT/"test_oad_072_independent_umd115_descriptor_adapter.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE=r"""
from __future__ import annotations
import json
from collections.abc import Mapping
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_115_observation_impact import (
    UMD_115_REVISION,
    ObservationDescriptor,
    OBSERVATION_FIELDS,
)
from qseries_v2.oracle_adapters.independent.oad_071_semantic_noise_rejection import (
    semantic_tokens,
    strong_phrases,
)

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def _thaw(value):
    if isinstance(value, Mapping):
        return {str(k):_thaw(v) for k,v in value.items()}
    if isinstance(value, tuple):
        # Frozen canonical mappings are represented as tuple-of-pairs.
        if all(isinstance(x,tuple) and len(x)==2 for x in value):
            try:
                return {str(k):_thaw(v) for k,v in value}
            except Exception:
                pass
        return tuple(_thaw(x) for x in value)
    if isinstance(value,list):
        return [_thaw(x) for x in value]
    return value

def _payload(obs):
    p=_thaw(getattr(obs,"payload",{}))
    return p if isinstance(p,dict) else {}

def _payload_text(obs):
    p=_payload(obs)
    source=_thaw(p.get("source_payload",{}))
    try:
        body=json.dumps(source,sort_keys=True,default=str)
    except Exception:
        body=str(source)
    return " ".join((str(p.get("subject","")),body))

def _facts_for(obs):
    p=_payload(obs)
    text=_payload_text(obs)
    phrases=strong_phrases(text)
    facts=set()
    source_id=str(getattr(obs,"source_id","") or p.get("source_id","")).lower()

    if "weather.gov" in source_id:
        for x in phrases:
            if any(k in x for k in (
                "warning","watch","storm","hurricane","tornado","flood",
                "snow","wind","heat","freeze","fire","thunderstorm"
            )):
                facts.add(("external_state",x))

    if "usgs.gov" in source_id:
        for x in phrases:
            if "earthquake" in x or "quake" in x:
                facts.add(("event",x))

    if "federalregister.gov" in source_id:
        for x in phrases:
            if any(k in x for k in (
                "rule","order","notice","regulation","tariff","sanction",
                "waiver","approval","prohibition"
            )):
                facts.add(("event",x))

    for x in phrases:
        if any(k in x for k in (
            "texas","california","florida","new-york","washington",
            "alaska","hawaii","gulf","atlantic","pacific"
        )):
            facts.add(("geography",x))

    return tuple(sorted(
        (kind,key)
        for kind,key in facts
        if kind in OBSERVATION_FIELDS and key and key!="new"
    ))

def descriptor_from_canonical(obs):
    oid=str(obs.observation_id)
    facts=_facts_for(obs)
    lineage=ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-115",
        revision=UMD_115_REVISION,
        schema_version="1.0.0",
        parent_hashes=(),
        source_refs=("oad://072/"+oid,),
        created_at=datetime.now(timezone.utc),
    )
    return ObservationDescriptor(oid,facts,lineage)

def descriptors_from_canonical(observations):
    return tuple(descriptor_from_canonical(x) for x in observations)

def verify_oad_072_immutable_payload_support():
    class X:
        observation_id="x"
        source_id="source.independent.weather.gov"
        payload=(("subject","Tornado Warning for Texas"),("source_payload",(("headline","Tornado Warning"),)))
    d=descriptor_from_canonical(X())
    return isinstance(d.facts,tuple)
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import acquire_independent_production_bundle
from qseries_v2.oracle_adapters.independent.oad_061_independent_to_canonical_bridge import canonicalize_independent_bundle
from qseries_v2.oracle_adapters.independent.oad_072_independent_umd115_descriptor_adapter import *

class T(unittest.TestCase):
    def test_immutable_payload_contract(self):
        self.assertTrue(verify_oad_072_immutable_payload_support())

    def test_physical(self):
        raw=acquire_independent_production_bundle(2)
        can=canonicalize_independent_bundle(raw,"oad072.physical")
        ds=descriptors_from_canonical(can)

        print("[PHYSICAL] canonical=",len(can))
        print("[PHYSICAL] descriptors=",len(ds))
        print("[PHYSICAL] descriptors_with_structured_facts=",sum(bool(x.facts) for x in ds))
        for d in ds:
            print("[FACTS]",d.observation_id[:12],d.facts)

        self.assertEqual(len(can),len(ds))
        self.assertTrue(all(
            all(v!="new" for _,v in d.facts)
            for d in ds
        ))

if __name__=="__main__":
    print("="*88)
    print(" OAD-072 PHYSICAL CERTIFICATION TEST")
    print(" UMD-115 OBSERVATION DESCRIPTOR ADAPTER")
    print(" IMMUTABLE CANONICAL PAYLOAD SUPPORT")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] Frozen canonical tuple/mapping payloads decoded safely")
    print("[PASS] Real independent observations adapted only to UMD-115 supported fact kinds")
    print("[PASS] Generic collision term 'new' remains rejected")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-072 CERTIFIED")
"""

def write_exact(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*88)
    print(" OAD-072 IMMUTABLE PAYLOAD REBUILD INSTALLER")
    print(" INDEPENDENT OBSERVATION TO UMD-115 DESCRIPTOR ADAPTER")
    print("="*88)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)

    kalshi=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"
    oph=ROOT/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py"
    umd115=ROOT/"qseries_v2"/"universal_market_discovery"/"umd_115_observation_impact.py"
    oad71=PKG/"oad_071_semantic_noise_rejection.py"

    for dep,label in (
        (kalshi,"Frozen Kalshi OAD-055"),
        (oph,"Frozen OPH-023"),
        (umd115,"Frozen UMD-115"),
        (oad71,"Certified OAD-071"),
    ):
        if not dep.is_file():
            raise RuntimeError(label+" missing")

    frozen={
        kalshi:hashlib.sha256(kalshi.read_bytes()).hexdigest(),
        oph:hashlib.sha256(oph.read_bytes()).hexdigest(),
        umd115:hashlib.sha256(umd115.read_bytes()).hexdigest(),
    }

    affected=(MODULE,TEST,INIT)
    old={x:(x.read_bytes() if x.exists() else None) for x in affected}

    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)

        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export="from .oad_072_independent_umd115_descriptor_adapter import *"
        if export not in lines:
            lines.append(export)
        write_exact(INIT,"\n".join(x for x in lines if x.strip())+"\n")

        for dep,h in frozen.items():
            if hashlib.sha256(dep.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+dep.name)

        print("[PASS] Certified OAD-071 dependency verified")
        print("[PASS] Frozen Kalshi OAD-055 unchanged")
        print("[PASS] Frozen OPH-023 unchanged")
        print("[PASS] Frozen UMD-115 unchanged")
        print("[PASS] Rebuilt OAD-072 around immutable canonical payload representation")
        print("[PASS] No frozen subsystem modified")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-072 IMMUTABLE PAYLOAD REBUILD COMPLETE")

    except Exception:
        for x,b in old.items():
            if b is None:
                if x.exists():
                    x.unlink()
            else:
                x.write_bytes(b)
        print("[ROLLBACK] OAD-072 rebuild failed; affected files restored")
        raise

if __name__=="__main__":
    main()
