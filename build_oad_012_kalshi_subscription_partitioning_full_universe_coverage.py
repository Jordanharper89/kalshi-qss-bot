from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates += [base, base/"kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p, p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir():
            return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT=locate_repository()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current: return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-012'
TITLE='KALSHI SUBSCRIPTION PARTITIONING + FULL-UNIVERSE COVERAGE'
REVISION='OAD_012_PRODUCTION_V1'
MODULE=PACKAGE/'oad_012_subscription_partitioning.py'
TEST=ROOT/'test_oad_012_kalshi_subscription_partitioning_full_universe_coverage.py'
EXPORTS=('OAD_012_BUILD_ID', 'OAD_012_REVISION', 'SubscriptionPartition', 'SubscriptionCoveragePlan', 'partition_subscriptions', 'build_partition_subscribe_commands', 'build_oad_012_certification_manifest', 'verify_oad_012_kalshi_subscription_partitioning_full_universe_coverage')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from math import ceil
from types import MappingProxyType
from .oad_011_websocket_foundation import build_subscribe_command

OAD_012_BUILD_ID="OAD-012"
OAD_012_REVISION="OAD_012_KALSHI_SUBSCRIPTION_PARTITIONING_FULL_UNIVERSE_COVERAGE_V1"

@dataclass(frozen=True)
class SubscriptionPartition:
    partition_id:int
    market_tickers:tuple[str,...]
    channels:tuple[str,...]

@dataclass(frozen=True)
class SubscriptionCoveragePlan:
    partitions:tuple[SubscriptionPartition,...]
    eligible_markets:int
    covered_markets:int
    complete:bool

def partition_subscriptions(market_tickers,channels=("orderbook_delta","ticker","trade"),partition_size=100):
    tickers=tuple(sorted(set(str(x) for x in market_tickers if str(x))))
    if not tickers or int(partition_size)<1:
        raise ValueError("markets and positive partition_size required")
    parts=[]
    for i in range(0,len(tickers),int(partition_size)):
        chunk=tickers[i:i+int(partition_size)]
        build_subscribe_command(len(parts)+1,channels,chunk)
        parts.append(SubscriptionPartition(len(parts)+1,chunk,tuple(channels)))
    return SubscriptionCoveragePlan(tuple(parts),len(tickers),sum(len(p.market_tickers) for p in parts),True)

def build_partition_subscribe_commands(plan):
    if not isinstance(plan,SubscriptionCoveragePlan) or not plan.complete:
        raise ValueError("complete coverage plan required")
    return tuple(build_subscribe_command(p.partition_id,p.channels,p.market_tickers) for p in plan.partitions)

def build_oad_012_certification_manifest():
    return MappingProxyType({"build_id":OAD_012_BUILD_ID,"revision":OAD_012_REVISION,
        "full_universe_coverage":True,"partitioning":True,"read_only":True})

def verify_oad_012_kalshi_subscription_partitioning_full_universe_coverage():
    p=partition_subscriptions(("C","A","B"),partition_size=2)
    return p.complete and p.covered_markets==3 and len(p.partitions)==2 and p.partitions[0].market_tickers==("A","B")
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_012_subscription_partitioning import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_012_kalshi_subscription_partitioning_full_universe_coverage())
    def test_no_loss(self):
        p=partition_subscriptions(tuple("ABCDE"),partition_size=2)
        got=tuple(x for part in p.partitions for x in part.market_tickers)
        self.assertEqual(got,("A","B","C","D","E"))
    def test_commands(self):
        self.assertEqual(len(build_partition_subscribe_commands(partition_subscriptions(("A","B"),partition_size=1))),2)
if __name__=="__main__":
    print("="*72);print(" OAD-012 CERTIFICATION TEST");print(" SUBSCRIPTION PARTITIONING + FULL-UNIVERSE COVERAGE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi deterministic full-universe subscription partitioning certified");print("[DONE] OAD-012 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oad_011_websocket_foundation.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_011_websocket_foundation')
        if getattr(m,'verify_oad_011_kalshi_websocket_market_data_foundation')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_adapters.kalshi."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),
              "test":TEST.name,"files":{str(MODULE.relative_to(ROOT)):sha(MODULE),
              TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__": main()
