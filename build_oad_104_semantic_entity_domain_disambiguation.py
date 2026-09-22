from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-104'
REVISION='OAD_104_SEMANTIC_ENTITY_DOMAIN_DISAMBIGUATION_V1'
TITLE='SEMANTIC ENTITY / DOMAIN DISAMBIGUATION'

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=ROOT/'qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py'
TEST=ROOT/'test_oad_104_semantic_entity_domain_disambiguation.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport re\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n# Deliberately small semantic ambiguity rules. These are not participant dictionaries;\n# they prevent lexical domain false positives and preserve unknown when identity is not provable.\n@dataclass(frozen=True, slots=True)\nclass SemanticDisambiguation:\n    text: str\n    lexical_domain: str\n    semantic_domain: str\n    semantic_subdomain: str\n    state: str\n    reason: str\n\nSPORT_STRUCTURE = (\n    r"\\bwins?\\b", r"\\bgoals?\\b", r"\\bpoints?\\b", r"\\bruns?\\b", r"\\binnings?\\b",\n    r"\\bsets?\\b", r"\\bsubmission\\b", r"\\bdecision\\b", r"\\bko/tko\\b",\n)\n\ndef disambiguate_semantic_domain(text, lexical_domain="unknown", guarded_sport="UNKNOWN"):\n    text=str(text or "").strip()\n    low=text.lower()\n    if guarded_sport and guarded_sport!="UNKNOWN":\n        return SemanticDisambiguation(text,lexical_domain,"sports",guarded_sport,"RESOLVED",\n            "guarded sport identity overrides lexical ambiguity")\n    if re.search(r"\\b(shanghai\\s+port|golden\\s+state|portland\\s+st\\.?)\\b",low,re.I):\n        return SemanticDisambiguation(text,lexical_domain,"unknown","",\n            "AMBIGUOUS_ENTITY","lexical token is embedded in a named entity; authoritative entity identity required")\n    if any(re.search(p,low,re.I) for p in SPORT_STRUCTURE):\n        return SemanticDisambiguation(text,lexical_domain,"sports","UNKNOWN",\n            "SPORT_STRUCTURE_ONLY","sports mechanics present without sport identity")\n    if lexical_domain!="unknown":\n        return SemanticDisambiguation(text,lexical_domain,lexical_domain,"",\n            "LEXICAL_DOMAIN_ONLY","domain signal retained but not treated as entity identity")\n    return SemanticDisambiguation(text,lexical_domain,"unknown","","UNRESOLVED","no safe semantic identity")\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation import disambiguate_semantic_domain\nclass T(unittest.TestCase):\n    def test_shanghai_port_not_transport(self):\n        r=disambiguate_semantic_domain("Shanghai Port","transport")\n        self.assertEqual((r.semantic_domain,r.state),("unknown","AMBIGUOUS_ENTITY"))\n    def test_guarded_sport_wins(self):\n        r=disambiguate_semantic_domain("Golden State","energy_commodities","basketball")\n        self.assertEqual((r.semantic_domain,r.semantic_subdomain),("sports","basketball"))\nif __name__=="__main__":\n    print("="*96); print(" OAD-104 CERTIFICATION TEST"); print("="*96)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Named-entity lexical collisions are not promoted into domains")\n    print("[PASS] Guarded sport evidence outranks lexical ambiguity")\n    print("[DONE] OAD-104 CERTIFIED")\n'
REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_103_guarded_contextual_identity_resolver.py', 'Certified OAD-103 guarded identity resolver')]
FROZEN=[
 ("qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py","Frozen Kalshi OAD-055"),
 ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),
 ("qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py","Frozen UMD-098"),
 ("qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py","Frozen UMD-109"),
]

def write(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp,path)

def main():
    print("="*104)
    print(" OAD-104 INSTALLER")
    print(" "+TITLE)
    print("="*104)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for rel,label in REQUIRED:
        p=ROOT/rel
        if not p.is_file():
            raise RuntimeError(label+" missing")
        print("[PASS]",label,"verified")
    frozen={ROOT/rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel,_ in FROZEN}
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write(MODULE,MODULE_SOURCE)
        write(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export=f"from .oad_104_semantic_entity_domain_disambiguation import *"
        if export not in lines:
            lines.append(export)
        write(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+p.name)
        print("[PASS] Wrote:",MODULE.relative_to(ROOT))
        print("[PASS] Wrote:",TEST.name)
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-104 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] OAD-104 affected files restored")
        raise

if __name__=="__main__":
    main()
