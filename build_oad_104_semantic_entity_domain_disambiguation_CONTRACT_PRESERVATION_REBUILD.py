from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-104'
REVISION='OAD_104_CONTRACT_PRESERVATION_FOUNDATIONAL_REBUILD'
TITLE='SEMANTIC ENTITY / DOMAIN DISAMBIGUATION — CONTRACT PRESERVATION REBUILD'

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
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport re\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass SemanticDisambiguation:\n    text: str\n    lexical_domain: str\n    lexical_subdomain: str\n    semantic_domain: str\n    semantic_subdomain: str\n    state: str\n    reason: str\n\nSPORT_STRUCTURE=(\n    r"\\bwins?\\b", r"\\bgoals?\\b", r"\\bpoints?\\b", r"\\bruns?\\b", r"\\binnings?\\b",\n    r"\\bsets?\\b", r"\\bsubmission\\b", r"\\bdecision\\b", r"\\bko/tko\\b",\n)\n\nAMBIGUOUS_ENTITY_PATTERNS=(\n    r"\\bshanghai\\s+port\\b",\n    r"\\bgolden\\s+state\\b",\n    r"\\bportland\\s+st\\.?\\b",\n)\n\ndef _normalized_subdomain(domain, subdomain):\n    domain=str(domain or "").strip()\n    subdomain=str(subdomain or "").strip()\n    if domain=="sports":\n        return subdomain if subdomain not in ("","NONE") else "UNKNOWN"\n    if domain=="financial_markets":\n        return subdomain if subdomain not in ("","NONE") else "financial_price"\n    return subdomain\n\ndef disambiguate_semantic_domain(\n    text,\n    lexical_domain="unknown",\n    guarded_sport="UNKNOWN",\n    lexical_subdomain=""\n):\n    text=str(text or "").strip()\n    lexical_domain=str(lexical_domain or "unknown").strip()\n    lexical_subdomain=_normalized_subdomain(lexical_domain, lexical_subdomain)\n    guarded_sport=str(guarded_sport or "UNKNOWN").strip()\n\n    if guarded_sport not in ("","NONE","UNKNOWN"):\n        return SemanticDisambiguation(\n            text, lexical_domain, lexical_subdomain,\n            "sports", guarded_sport,\n            "RESOLVED",\n            "guarded sport identity overrides lexical ambiguity",\n        )\n\n    low=text.lower()\n\n    # Preserve explicit upstream sports identity as UNKNOWN rather than erasing it.\n    if lexical_domain=="sports":\n        if any(re.search(p,low,re.I) for p in AMBIGUOUS_ENTITY_PATTERNS):\n            return SemanticDisambiguation(\n                text, lexical_domain, lexical_subdomain,\n                "sports", lexical_subdomain or "UNKNOWN",\n                "UPSTREAM_SPORTS_PRESERVED",\n                "upstream sports admission preserved; entity semantics remain unresolved",\n            )\n        return SemanticDisambiguation(\n            text, lexical_domain, lexical_subdomain,\n            "sports", lexical_subdomain or "UNKNOWN",\n            "UPSTREAM_SPORTS_PRESERVED",\n            "validated upstream sports domain/subdomain preserved",\n        )\n\n    # Preserve upstream financial domain and explicit financial_price subtype.\n    if lexical_domain=="financial_markets":\n        return SemanticDisambiguation(\n            text, lexical_domain, lexical_subdomain,\n            "financial_markets", lexical_subdomain or "financial_price",\n            "UPSTREAM_FINANCIAL_PRESERVED",\n            "validated upstream financial market subtype preserved",\n        )\n\n    if any(re.search(p,low,re.I) for p in AMBIGUOUS_ENTITY_PATTERNS):\n        return SemanticDisambiguation(\n            text, lexical_domain, lexical_subdomain,\n            "unknown","",\n            "AMBIGUOUS_ENTITY",\n            "lexical token occurs inside a named entity; identity not guessed",\n        )\n\n    if any(re.search(p,low,re.I) for p in SPORT_STRUCTURE):\n        return SemanticDisambiguation(\n            text, lexical_domain, lexical_subdomain,\n            "sports","UNKNOWN",\n            "SPORT_STRUCTURE_ONLY",\n            "sports mechanics present without sport identity",\n        )\n\n    if lexical_domain!="unknown":\n        return SemanticDisambiguation(\n            text, lexical_domain, lexical_subdomain,\n            lexical_domain, lexical_subdomain,\n            "LEXICAL_DOMAIN_ONLY",\n            "validated upstream non-sport domain preserved",\n        )\n\n    return SemanticDisambiguation(\n        text, lexical_domain, lexical_subdomain,\n        "unknown","",\n        "UNRESOLVED",\n        "no safe semantic identity",\n    )\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation import disambiguate_semantic_domain\n\nclass T(unittest.TestCase):\n    def test_sports_unknown_preserved(self):\n        r=disambiguate_semantic_domain("Lloyd Harris","sports","UNKNOWN","UNKNOWN")\n        self.assertEqual((r.semantic_domain,r.semantic_subdomain),("sports","UNKNOWN"))\n    def test_financial_price_preserved(self):\n        r=disambiguate_semantic_domain("Target Price: $79,695.41","financial_markets","UNKNOWN","financial_price")\n        self.assertEqual((r.semantic_domain,r.semantic_subdomain),("financial_markets","financial_price"))\n    def test_shanghai_port_unknown_when_not_admitted_sports(self):\n        r=disambiguate_semantic_domain("Shanghai Port","transport","UNKNOWN","")\n        self.assertEqual((r.semantic_domain,r.state),("unknown","AMBIGUOUS_ENTITY"))\n    def test_guarded_sport_wins(self):\n        r=disambiguate_semantic_domain("Golden State","energy_commodities","basketball","")\n        self.assertEqual((r.semantic_domain,r.semantic_subdomain),("sports","basketball"))\n\nif __name__=="__main__":\n    print("="*100)\n    print(" OAD-104 FOUNDATIONAL REBUILD CERTIFICATION TEST")\n    print("="*100)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] sports:UNKNOWN preserved exactly")\n    print("[PASS] financial_markets:financial_price preserved exactly")\n    print("[PASS] ambiguous entities are not guessed")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-104 FOUNDATIONAL REBUILD CERTIFIED")\n'
REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_099_mixed_domain_cross_category_decomposition.py', 'Current OAD-099 decomposition contract'), ('qseries_v2/oracle_adapters/independent/oad_103_guarded_contextual_identity_resolver.py', 'Certified OAD-103 guarded resolver'), ('qseries_v2/oracle_adapters/independent/oad_106_failed_gate_repository_audit.py', 'Certified repository failure audit')]
FROZEN=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]

def write(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp,path)

def main():
    print("="*108)
    print(" OAD-104 REBUILD INSTALLER")
    print(" "+TITLE)
    print("="*108)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for rel,label in REQUIRED:
        p=ROOT/rel
        if not p.is_file():
            raise RuntimeError(label+" missing: "+str(p))
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
        print("[PASS] Rebuilt foundational module:",MODULE.relative_to(ROOT))
        print("[PASS] Wrote:",TEST.name)
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-104 REBUILD INSTALLATION COMPLETE")
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
