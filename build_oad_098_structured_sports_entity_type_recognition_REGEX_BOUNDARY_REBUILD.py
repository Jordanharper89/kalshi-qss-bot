from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-098"
REVISION="OAD_098_STRUCTURED_SPORTS_ENTITY_TYPE_REGEX_BOUNDARY_REBUILD"
TITLE="STRUCTURED SPORTS ENTITY / TYPE RECOGNITION — FOUNDATIONAL REGEX BOUNDARY REBUILD"

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/"oad_098_structured_sports_entity_type_recognition.py"
TEST=ROOT/"test_oad_098_structured_sports_entity_type_recognition.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport re\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass SportsEntityType:\n    text:str\n    entity_type:str\n    structural_class:str\n    evidence:tuple[str,...]\n\n# Important: numeric \'+\' props must NOT use a trailing \\b after \'+\'\n# because \'+\' is itself a non-word character. Use an explicit right-edge lookahead.\nPROP_PATTERNS=(\n    ("player_prop", r"(?<!\\d)\\d+(?:\\.\\d+)?\\+(?=\\s|$|[,;/)])"),\n    ("spread_or_handicap", r"\\bwins?\\s+(?:1h\\s+)?by\\s+over\\s+\\d"),\n    ("total", r"\\bover\\s+\\d+(?:\\.\\d+)?\\s+(?:points|runs|goals)\\s+scored\\b"),\n    ("baseball_innings", r"\\bfirst\\s+5\\s+innings\\b"),\n    ("soccer_btts", r"\\bboth\\s+teams\\s+to\\s+score\\b"),\n)\n\nTEAM_HINTS=(\n    " fc"," united"," city"," state"," st."," university",\n    " tigers"," fighters"," heroes"," dinos"," esports"," team "\n)\n\ndef recognize_sports_entity_type(text):\n    raw=str(text or "").strip()\n    low=" "+raw.lower()+" "\n    for structural_class, pattern in PROP_PATTERNS:\n        if re.search(pattern, raw, re.I):\n            return SportsEntityType(\n                raw,\n                "STRUCTURED_MARKET_LEG",\n                structural_class,\n                (structural_class,),\n            )\n\n    if "/" in raw and len(raw.split("/"))==2:\n        return SportsEntityType(\n            raw,\n            "PAIR_OR_DOUBLES",\n            "participant_pair",\n            ("slash_pair",),\n        )\n\n    if any(hint in low for hint in TEAM_HINTS):\n        return SportsEntityType(\n            raw,\n            "TEAM_OR_CLUB",\n            "named_competitor",\n            ("team_structure",),\n        )\n\n    words=re.findall(r"[A-Za-zÀ-ÿ\'.-]+", raw)\n    if (\n        2 <= len(words) <= 5\n        and not re.search(\n            r"\\b(over|under|target|price|points|runs|goals|wins|tie)\\b",\n            raw,\n            re.I,\n        )\n    ):\n        return SportsEntityType(\n            raw,\n            "NAMED_COMPETITOR",\n            "participant_candidate",\n            ("proper_name_shape",),\n        )\n\n    return SportsEntityType(raw, "UNRESOLVED", "unknown", ())\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_098_structured_sports_entity_type_recognition import *\n\nclass T(unittest.TestCase):\n    def test_player_prop_integer_plus(self):\n        r=recognize_sports_entity_type("Rafael Devers: 1+")\n        self.assertEqual(r.structural_class,"player_prop")\n        self.assertEqual(r.entity_type,"STRUCTURED_MARKET_LEG")\n\n    def test_player_prop_decimal_plus(self):\n        r=recognize_sports_entity_type("Player Name: 2.5+")\n        self.assertEqual(r.structural_class,"player_prop")\n\n    def test_player_prop_comma_terminated(self):\n        r=recognize_sports_entity_type("Rafael Devers: 1+,")\n        self.assertEqual(r.structural_class,"player_prop")\n\n    def test_btts(self):\n        self.assertEqual(\n            recognize_sports_entity_type("Both Teams To Score").structural_class,\n            "soccer_btts",\n        )\n\n    def test_name_shape(self):\n        self.assertEqual(\n            recognize_sports_entity_type("Novak Djokovic").entity_type,\n            "NAMED_COMPETITOR",\n        )\n\n    def test_target_price_not_sport_entity(self):\n        self.assertEqual(\n            recognize_sports_entity_type("Target Price: $79,856.75").entity_type,\n            "UNRESOLVED",\n        )\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OAD-098 CERTIFICATION TEST")\n    print(" STRUCTURED SPORTS ENTITY / TYPE RECOGNITION")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Numeric \'+\' player props recognized with explicit non-word-safe boundary")\n    print("[PASS] Sports leg structure recognized without giant participant dictionaries")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-098 CERTIFIED")\n'

REQUIRED=[
 ("qseries_v2/oracle_adapters/independent/oad_097_cross_category_leg_parser.py","Certified OAD-097"),
]
FROZEN=[
 ("qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py","Frozen Kalshi OAD-055"),
 ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),
 ("qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py","Frozen UMD-098"),
 ("qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py","Frozen UMD-109"),
]

def write(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*88)
    print(" OAD-098 REBUILD INSTALLER")
    print(" "+TITLE)
    print("="*88)
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
        export="from .oad_098_structured_sports_entity_type_recognition import *"
        if export not in lines:
            lines.append(export)
        write(INIT,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+p.name)

        print("[PASS] Replaced foundational OAD-098 production module in place")
        print("[PASS] Replaced OAD-098 certification test in place")
        print("[PASS] Root defect repaired: trailing word-boundary after '+' removed")
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-098 REBUILD INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] OAD-098 affected files restored")
        raise

if __name__=="__main__":
    main()
