from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-073"
REVISION="OAD_073_PRODUCTION_INSTALLER_V1"
TITLE='CURRENT MARKET UMD-NORMALIZED DEPENDENCY INDEX'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_073_current_market_umd_dependency_index.py'
TEST=ROOT/'test_oad_073_current_market_umd_dependency_index.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom types import MappingProxyType\nfrom qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import semantic_key\nfrom qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index import fetch_current_open_kalshi_market_index\nfrom qseries_v2.oracle_adapters.independent.oad_071_semantic_noise_rejection import strong_phrases\nREAD_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False\ndef market_dependency_facts(m):\n    text=" ".join(str(m.get(k,"") or "") for k in ("ticker","event_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary"))\n    phrases=strong_phrases(text)\n    facts=set()\n    for x in phrases:\n        if any(k in x for k in ("earthquake","hurricane","tornado","flood","storm","snow","rain","temperature","heat","wind")): facts.add(("event",x))\n        if any(k in x for k in ("bitcoin","ethereum","solana","btc","eth")): facts.add(("asset",x))\n        if any(k in x for k in ("cpi","inflation","unemployment","payroll","gdp","interest-rate","fed-rate")): facts.add(("metric",x))\n        if any(k in x for k in ("election","president","senate","governor","primary")): facts.add(("event",x))\n        if any(k in x for k in ("texas","california","florida","new-york","washington","alaska","hawaii","gulf","atlantic","pacific")): facts.add(("geography",x))\n    return tuple(sorted(facts))\ndef build_current_market_dependency_index(limit=1000):\n    markets,_=fetch_current_open_kalshi_market_index(limit=limit)\n    index={}\n    fact_counts=0\n    for m in markets:\n        ticker=str(m.get("ticker","")).strip()\n        if not ticker: continue\n        facts=market_dependency_facts(m);fact_counts+=len(facts)\n        for kind,key in facts:index.setdefault(kind+"="+semantic_key(key),[]).append(ticker)\n    frozen=MappingProxyType({k:tuple(sorted(set(v))) for k,v in sorted(index.items())})\n    return markets,frozen,fact_counts\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_073_current_market_umd_dependency_index import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  markets,index,count=build_current_market_dependency_index(1000)\n  print("[PHYSICAL] current_open_markets=",len(markets));print("[PHYSICAL] semantic_dependency_keys=",len(index));print("[PHYSICAL] market_fact_instances=",count)\n  print("[PHYSICAL] sample_keys=",tuple(index.keys())[:20])\n  self.assertGreater(len(markets),0);self.assertNotIn("event=new",index)\nif __name__=="__main__":\n print("="*88);print(" OAD-073 PHYSICAL CERTIFICATION TEST");print(" CURRENT MARKET UMD-NORMALIZED DEPENDENCY INDEX");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] Current-market dependency keys normalized with frozen UMD semantic_key")\n print("[DONE] OAD-073 CERTIFIED")\n'

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
