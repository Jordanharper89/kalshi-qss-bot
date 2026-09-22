from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-074"
REVISION="OAD_074_PRODUCTION_INSTALLER_V1"
TITLE='STRONG STRUCTURED MARKET ASSOCIATION'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_074_strong_structured_market_association.py'
TEST=ROOT/'test_oad_074_strong_structured_market_association.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import semantic_key\nREAD_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False\n@dataclass(frozen=True,slots=True)\nclass StrongAssociation:\n observation_id:str;market_id:str;matched_facts:tuple;association_strength:str;candidate_only:bool=True\ndef strong_associations(descriptor,dependency_index,max_candidates=10):\n    hits={}\n    for kind,key in descriptor.facts:\n        sk=semantic_key(key)\n        ids=tuple(dependency_index.get(kind+"="+sk,()))\n        for mid in ids:hits.setdefault(mid,set()).add((kind,sk))\n    out=[]\n    for mid,facts in hits.items():\n        # One structured exact UMD fact is materially stronger than generic token overlap.\n        if not facts: continue\n        strength="MULTI_FACT" if len(facts)>=2 else "STRUCTURED_EXACT"\n        out.append(StrongAssociation(descriptor.observation_id,mid,tuple(sorted(facts)),strength,True))\n    return tuple(sorted(out,key=lambda x:(-len(x.matched_facts),x.market_id))[:max_candidates])\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_115_observation_impact import ObservationDescriptor,UMD_115_REVISION\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_adapters.independent.oad_074_strong_structured_market_association import *\nclass T(unittest.TestCase):\n def test_no_generic_collision(self):\n  l=ImmutableLineage("UMD","UMD-115",UMD_115_REVISION,"1.0.0",(),("oad://074",),datetime.now(timezone.utc))\n  d=ObservationDescriptor("x",(("event","earthquake"),),l)\n  r=strong_associations(d,{"event=new":("K1",),"event=earthquake":("K2",)})\n  self.assertEqual(tuple(x.market_id for x in r),("K2",))\n def test_empty(self):\n  l=ImmutableLineage("UMD","UMD-115",UMD_115_REVISION,"1.0.0",(),("oad://074b",),datetime.now(timezone.utc))\n  self.assertEqual(strong_associations(ObservationDescriptor("x",(),l),{}),())\nif __name__=="__main__":\n print("="*88);print(" OAD-074 CERTIFICATION TEST");print(" STRONG STRUCTURED MARKET ASSOCIATION");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] Generic word overlap cannot create an association")\n print("[DONE] OAD-074 CERTIFIED")\n'

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
