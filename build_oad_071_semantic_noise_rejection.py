from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-071"
REVISION="OAD_071_PRODUCTION_INSTALLER_V1"
TITLE='SEMANTIC NOISE REJECTION'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_071_semantic_noise_rejection.py'
TEST=ROOT/'test_oad_071_semantic_noise_rejection.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nimport re\nfrom qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import semantic_key\nREAD_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False\nWEAK_TERMS=frozenset({\n "new","latest","update","updated","active","open","closed","market","markets","will","would","could","should",\n "today","tomorrow","yesterday","week","month","year","event","events","document","documents","alert","alerts",\n "state","states","federal","register","weather","earthquake","earthquakes","united","official","current",\n})\ndef semantic_tokens(value):\n    toks=[semantic_key(x) for x in re.findall(r"[A-Za-z][A-Za-z0-9.-]{2,}",str(value or ""))]\n    return tuple(sorted({x for x in toks if x and x not in WEAK_TERMS and len(x)>=3}))\ndef strong_phrases(value):\n    words=semantic_tokens(value)\n    out=set(words)\n    for n in (2,3):\n        for i in range(max(0,len(words)-n+1)):\n            phrase="-".join(words[i:i+n])\n            if phrase and not any(x in WEAK_TERMS for x in words[i:i+n]): out.add(phrase)\n    return tuple(sorted(out))\ndef verify_oad_071():\n    return "new" not in semantic_tokens("new federal update") and "bitcoin" in semantic_tokens("Bitcoin price")\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_071_semantic_noise_rejection import *\nclass T(unittest.TestCase):\n def test_generic_new_rejected(self): self.assertNotIn("new",semantic_tokens("new new latest update"))\n def test_domain_term_retained(self): self.assertIn("bitcoin",semantic_tokens("Bitcoin price threshold"))\n def test_phrase(self): self.assertIn("bitcoin-price",strong_phrases("Bitcoin price threshold"))\n def test_verify(self): self.assertTrue(verify_oad_071())\nif __name__=="__main__":\n print("="*88);print(" OAD-071 CERTIFICATION TEST");print(" SEMANTIC NOISE REJECTION");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] Generic collision terms including \'new\' rejected")\n print("[DONE] OAD-071 CERTIFIED")\n'

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
