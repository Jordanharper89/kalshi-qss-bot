from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-072"
REVISION="OAD_072_PRODUCTION_INSTALLER_V1"
TITLE='INDEPENDENT OBSERVATION TO UMD-115 DESCRIPTOR ADAPTER'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_072_independent_umd115_descriptor_adapter.py'
TEST=ROOT/'test_oad_072_independent_umd115_descriptor_adapter.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nimport json\nfrom datetime import datetime,timezone\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_115_observation_impact import UMD_115_REVISION,ObservationDescriptor,OBSERVATION_FIELDS\nfrom qseries_v2.oracle_adapters.independent.oad_071_semantic_noise_rejection import semantic_tokens,strong_phrases\nREAD_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False\ndef _payload_text(obs):\n    p=getattr(obs,"payload",{}) or {}\n    source=p.get("source_payload",{}) if isinstance(p,dict) else {}\n    return " ".join((str(p.get("subject","")),json.dumps(source,sort_keys=True,default=str)))\ndef _facts_for(obs):\n    p=getattr(obs,"payload",{}) or {}\n    src=str(p.get("source_id","") or getattr(obs,"source_id","")).lower()\n    text=_payload_text(obs)\n    toks=semantic_tokens(text); phrases=strong_phrases(text)\n    facts=set()\n    # UMD-115 supported fields only; conservative adapter-side extraction.\n    if "weather.gov" in str(getattr(obs,"source_id","")):\n        facts.update(("external_state",x) for x in phrases if any(k in x for k in ("warning","watch","storm","hurricane","tornado","flood","snow","wind","heat")))\n    if "usgs.gov" in str(getattr(obs,"source_id","")):\n        facts.update(("event",x) for x in phrases if "earthquake" in x or "quake" in x)\n    if "federalregister.gov" in str(getattr(obs,"source_id","")):\n        facts.update(("event",x) for x in phrases if any(k in x for k in ("rule","order","notice","regulation","tariff","sanction")))\n    # Geography/entity candidates need meaningful length and must survive OAD-071.\n    for x in phrases:\n        if len(x)>=8 and any(ch=="-" for ch in x):\n            if any(k in x for k in ("texas","california","florida","new-york","washington","alaska","hawaii","gulf","atlantic","pacific")):\n                facts.add(("geography",x))\n    return tuple(sorted((k,v) for k,v in facts if k in OBSERVATION_FIELDS and v))\ndef descriptor_from_canonical(obs):\n    oid=str(obs.observation_id)\n    facts=_facts_for(obs)\n    lineage=ImmutableLineage(subsystem_id="UMD",build_id="UMD-115",revision=UMD_115_REVISION,\n        schema_version="1.0.0",parent_hashes=(),source_refs=("oad://072/"+oid,),created_at=datetime.now(timezone.utc))\n    return ObservationDescriptor(oid,facts,lineage)\ndef descriptors_from_canonical(observations):\n    return tuple(descriptor_from_canonical(x) for x in observations)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import acquire_independent_production_bundle\nfrom qseries_v2.oracle_adapters.independent.oad_061_independent_to_canonical_bridge import canonicalize_independent_bundle\nfrom qseries_v2.oracle_adapters.independent.oad_072_independent_umd115_descriptor_adapter import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  raw=acquire_independent_production_bundle(2);can=canonicalize_independent_bundle(raw,"oad072.physical");ds=descriptors_from_canonical(can)\n  print("[PHYSICAL] canonical=",len(can));print("[PHYSICAL] descriptors=",len(ds));print("[PHYSICAL] descriptors_with_structured_facts=",sum(bool(x.facts) for x in ds))\n  for d in ds: print("[FACTS]",d.observation_id[:12],d.facts)\n  self.assertEqual(len(can),len(ds));self.assertTrue(all(all(v!="new" for _,v in d.facts) for d in ds))\nif __name__=="__main__":\n print("="*88);print(" OAD-072 PHYSICAL CERTIFICATION TEST");print(" UMD-115 OBSERVATION DESCRIPTOR ADAPTER");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] Real independent observations adapted only to UMD-115 supported fact kinds")\n print("[DONE] OAD-072 CERTIFIED")\n'

def write_exact(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*88);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*88)
    print("[BOOT] Revision:",REVISION);print("[ROOT]",ROOT)
    kalshi=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"
    oph=ROOT/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py"
    oad70=PKG/"oad_070_physical_current_market_independent_association_gate.py"
    umd115=ROOT/"qseries_v2"/"universal_market_discovery"/"umd_115_observation_impact.py"
    for p,label in ((kalshi,"Frozen Kalshi OAD-055"),(oph,"Frozen OPH-023"),(oad70,"Certified OAD-070"),(umd115,"Certified UMD-115")):
        if not p.is_file(): raise RuntimeError(label+" missing")
    frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (kalshi,oph,umd115)}
    affected=(MODULE,TEST,INIT); old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from ."+MODULE.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_exact(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("Frozen dependency changed: "+p.name)
        print("[PASS] Certified OAD-070 dependency verified")
        print("[PASS] Frozen Kalshi OAD-055 unchanged")
        print("[PASS] Frozen OPH-023 unchanged")
        print("[PASS] Frozen UMD-115 observation-impact contract unchanged")
        print("[PASS] Wrote:",MODULE.relative_to(ROOT));print("[PASS] Wrote:",TEST.name)
        print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored");raise

if __name__=="__main__": main()
