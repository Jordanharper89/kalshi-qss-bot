from pathlib import Path
import ast,importlib,os,subprocess,sys
ROOT=Path.cwd().resolve()
TARGET=ROOT/'qseries_v2/oracle_pre_settlement_coverage/opc_043_live_freshness_distribution_physical_proof.py'
TEST=ROOT/'test_opc_043_live_freshness_distribution_physical_proof.py'
SOURCE='from pathlib import Path\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_023_rotating_full_universe_coverage_cycle import fetch_rotating_open_page\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_003_canonical_observation_coverage_read_model import read_recent_canonical_market_freshness\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_028_activity_tier_refresh_policy import classify_market_refresh_tier\nOPC_043_BUILD_ID="OPC-043"\ndef physical_probe(root=None):\n root=Path(root or Path.cwd()).resolve();now=datetime.now(timezone.utc);b=CoverageLoadBudget(page_limit=1000,max_snapshots_per_cycle=1000,cycle_sleep_seconds=0.0,lookback_hours=24.0,request_timeout_seconds=20.0)\n _,markets,_,raw=fetch_rotating_open_page(root,b);fresh=read_recent_canonical_market_freshness(root,24,250000);rows=[];due=current=0\n for market in markets:\n  t=str(market.get("ticker") or "");last=fresh.get(t);tier=classify_market_refresh_tier(market,now);age=None if last is None else max(0.0,(now-last).total_seconds());d=age is None or age>=tier.refresh_seconds;due+=int(d);current+=int(not d);rows.append((t,tier.tier,tier.refresh_seconds,None if age is None else round(age,1),d))\n return {"raw_page_markets":raw,"active_markets":len(markets),"with_recent_snapshot":sum(r[3] is not None for r in rows),"fresh_for_required_interval":current,"due_for_refresh":due,"sample":rows[:20],"read_only":True,"execution_authority":False}\ndef verify_opc_043():return OPC_043_BUILD_ID=="OPC-043"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage import opc_043_live_freshness_distribution_physical_proof as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  self.assertTrue(m.verify_opc_043());x=m.physical_probe();self.assertGreater(x["raw_page_markets"],0);self.assertTrue(x["read_only"]);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n'
def w(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+f".{os.getpid()}.tmp")
    t.write_text(s,encoding="utf-8",newline="\n")
    os.replace(t,p)
def rr(p,b):
    if b is None:
        if p.exists(): p.unlink()
    else:
        p.write_bytes(b)
def main():
    print("="*88);print(' OPC-043 INSTALLER — LIVE FRESHNESS DISTRIBUTION PHYSICAL PROOF');print("="*88);print("[ROOT]",ROOT)
    bm=TARGET.read_bytes() if TARGET.exists() else None
    bt=TEST.read_bytes() if TEST.exists() else None
    try:
        ast.parse(SOURCE);ast.parse(TEST_SOURCE);print("[PASS] payload syntax verified")
        w(TARGET,SOURCE);w(TEST,TEST_SOURCE);importlib.invalidate_caches()
        modname=TARGET.with_suffix("").relative_to(ROOT).as_posix().replace("/",".")
        if modname in sys.modules: del sys.modules[modname]
        m=importlib.import_module(modname)
        if hasattr(m,"physical_probe"):
            print("[PHYSICAL]",m.physical_probe(ROOT))
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=180)
    except Exception:
        rr(TARGET,bm);rr(TEST,bt);print("[ROLLBACK] failed; affected files restored");raise
    print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":
    main()
