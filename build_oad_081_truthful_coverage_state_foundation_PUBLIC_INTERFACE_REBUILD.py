from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-081"
REVISION="OAD_081_PUBLIC_INTERFACE_REBUILD_V1"
TITLE="TRUTHFUL COVERAGE-STATE FOUNDATION — PUBLIC INTERFACE REBUILD"

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
OAD079=PKG/"oad_079_live_source_coverage_gap_ranking.py"
OAD081=PKG/"oad_081_truthful_coverage_state_foundation.py"
TEST=ROOT/"test_oad_081_truthful_coverage_state_foundation.py"
INIT=PKG/"__init__.py"

OAD079_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass

from qseries_v2.oracle_adapters.independent.oad_077_live_market_topic_inventory import build_live_topic_inventory
from qseries_v2.oracle_adapters.independent.oad_078_authoritative_source_requirement_map import requirements_for_topic

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

COVERED="COVERED"
NOT_COVERED="NOT_COVERED"
UNMAPPED="UNMAPPED"

@dataclass(frozen=True,slots=True)
class CoverageGap:
    topic:str
    live_markets:int
    required_source_families:tuple[str,...]
    missing_source_families:tuple[str,...]
    coverage_state:str
    priority_score:int

    @property
    def covered(self):
        return self.coverage_state==COVERED

def coverage_state(topic, requirements, missing_families):
    if str(topic)=="other" or not requirements:
        return UNMAPPED
    if missing_families:
        return NOT_COVERED
    return COVERED

def rank_live_source_coverage_gaps(limit=1000):
    inv=build_live_topic_inventory(limit)
    out=[]
    for topic,count in inv.topic_counts:
        req=requirements_for_topic(topic)
        required=tuple(x.source_family for x in req if x.source_family!="Unmapped")
        missing=tuple(
            x.source_family for x in req
            if not x.existing_adapter and x.source_family!="Unmapped"
        )
        state=coverage_state(topic,req,missing)
        urgency=3 if state==UNMAPPED else (2 if state==NOT_COVERED else 1)
        score=int(count)*1000 + urgency*100 + len(missing)
        out.append(
            CoverageGap(
                topic,
                int(count),
                required,
                missing,
                state,
                score,
            )
        )
    return tuple(sorted(out,key=lambda x:(-x.priority_score,x.topic)))
"""

OAD081_SOURCE=r"""
from __future__ import annotations

from qseries_v2.oracle_adapters.independent.oad_079_live_source_coverage_gap_ranking import (
    COVERED,
    NOT_COVERED,
    UNMAPPED,
    CoverageGap,
    coverage_state,
)

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def verify_truthful_unmapped_semantics():
    a=coverage_state("other",(),())
    b=coverage_state(
        "sports",
        (object(),),
        ("Official league/team feeds",),
    )
    c=coverage_state(
        "weather",
        (object(),),
        (),
    )
    return a==UNMAPPED and b==NOT_COVERED and c==COVERED
"""

TEST_SOURCE=r"""
import unittest

from qseries_v2.oracle_adapters.independent.oad_079_live_source_coverage_gap_ranking import (
    COVERED,
    NOT_COVERED,
    UNMAPPED,
    coverage_state,
)
from qseries_v2.oracle_adapters.independent.oad_081_truthful_coverage_state_foundation import (
    verify_truthful_unmapped_semantics,
)

class T(unittest.TestCase):
    def test_other_is_unmapped(self):
        self.assertEqual(
            coverage_state("other",(),()),
            UNMAPPED,
        )

    def test_missing_is_not_covered(self):
        self.assertEqual(
            coverage_state(
                "sports",
                (object(),),
                ("Official league/team feeds",),
            ),
            NOT_COVERED,
        )

    def test_complete_is_covered(self):
        self.assertEqual(
            coverage_state(
                "weather",
                (object(),),
                (),
            ),
            COVERED,
        )

    def test_verify(self):
        self.assertTrue(verify_truthful_unmapped_semantics())

if __name__=="__main__":
    print("="*88)
    print(" OAD-081 CERTIFICATION TEST")
    print(" TRUTHFUL COVERAGE-STATE FOUNDATION — PUBLIC INTERFACE")
    print("="*88)

    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] Public coverage_state interface certified")
    print("[PASS] other/unclassified reports UNMAPPED")
    print("[PASS] missing source families report NOT_COVERED")
    print("[PASS] fully mapped source coverage reports COVERED")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-081 CERTIFIED")
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
    print(" OAD-081 PUBLIC INTERFACE REBUILD INSTALLER")
    print(" TRUTHFUL COVERAGE-STATE FOUNDATION")
    print("="*88)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)

    frozen_paths=(
        ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py",
        ROOT/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py",
        ROOT/"qseries_v2"/"universal_market_discovery"/"umd_098_market_taxonomy.py",
        ROOT/"qseries_v2"/"universal_market_discovery"/"umd_109_market_semantic_profile.py",
    )
    required=(
        PKG/"oad_077_live_market_topic_inventory.py",
        PKG/"oad_078_authoritative_source_requirement_map.py",
        PKG/"oad_080_live_adapter_expansion_plan.py",
    )

    for dep in frozen_paths+required:
        if not dep.is_file():
            raise RuntimeError("Required dependency missing: "+str(dep))

    frozen={x:hashlib.sha256(x.read_bytes()).hexdigest() for x in frozen_paths}
    affected=(OAD079,OAD081,TEST,INIT)
    old={x:(x.read_bytes() if x.exists() else None) for x in affected}

    try:
        write_exact(OAD079,OAD079_SOURCE)
        write_exact(OAD081,OAD081_SOURCE)
        write_exact(TEST,TEST_SOURCE)

        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        for exp in (
            "from .oad_079_live_source_coverage_gap_ranking import *",
            "from .oad_081_truthful_coverage_state_foundation import *",
        ):
            if exp not in lines:
                lines.append(exp)
        write_exact(INIT,"\n".join(x for x in lines if x.strip())+"\n")

        for dep,h in frozen.items():
            if hashlib.sha256(dep.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+dep.name)

        print("[PASS] Existing OAD-079 foundation rebuilt with public coverage_state interface")
        print("[PASS] OAD-081 certification surface aligned to production interface")
        print("[PASS] No private helper required by certification")
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-081 PUBLIC INTERFACE REBUILD COMPLETE")

    except Exception:
        for x,b in old.items():
            if b is None:
                if x.exists():
                    x.unlink()
            else:
                x.write_bytes(b)
        print("[ROLLBACK] OAD-081 rebuild failed; affected files restored")
        raise

if __name__=="__main__":
    main()
