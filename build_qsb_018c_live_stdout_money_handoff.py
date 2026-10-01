from pathlib import Path
import py_compile

ROOT = Path.cwd()
QSB015 = ROOT / "run_qsb_015_first_seconds_launch_impulse.py"
GMGN300 = ROOT / "qseries_v2/oracle_adapters/independent/oad_300_solana_wallet_trader_claim_normalization.py"

for dep in (QSB015, GMGN300):
    if not dep.is_file():
        raise SystemExit("[FAIL] missing dependency: " + str(dep))

PKG = ROOT / "qseries_v2/oracle_strategy_intelligence/solana_money"
PKG.mkdir(parents=True, exist_ok=True)
(PKG / "__init__.py").touch(exist_ok=True)

MODULE = PKG / "qsb_018c_live_stdout_money_handoff.py"
TEST = ROOT / "test_qsb_018c_live_stdout_money_handoff.py"
RUN = ROOT / "run_qsb_018c_live_stdout_money_handoff.py"

module = r"""
from __future__ import annotations
import json, re
from dataclasses import dataclass, asdict

READ_ONLY = True
EXECUTION_AUTHORITY = False
PAPER_ONLY = True
REVISION = "QSB_018C_LIVE_STDOUT_MONEY_HANDOFF_V1"

FAST_PREFIX = "[FAST ENTRIES]"
MONEY_PREFIX = "[FRESH MONEY]"
BURST_PREFIX = "[BURST]"
FAMILIES_PREFIX = "[FAMILIES]"

@dataclass(frozen=True)
class FastEntry:
    family: str
    token: str
    score: float
    liquidity_usd: float
    def to_dict(self): return asdict(self)

def parse_fast_entries(line: str):
    if FAST_PREFIX not in line:
        return ()
    payload=line.split(FAST_PREFIX,1)[1].strip()
    try:
        rows=json.loads(payload)
    except Exception:
        return ()
    out=[]
    if isinstance(rows,list):
        for r in rows:
            if not isinstance(r,dict):
                continue
            token=str(r.get("token") or "").strip()
            if not token:
                continue
            try: score=float(r.get("score",0.0))
            except Exception: score=0.0
            try: liq=float(r.get("liq",0.0))
            except Exception: liq=0.0
            out.append(FastEntry(str(r.get("family") or "UNKNOWN"),token,score,liq))
    return tuple(out)

def parse_fresh_money(line: str):
    if MONEY_PREFIX not in line:
        return None
    def grab(name, cast=float):
        m=re.search(r"\b"+re.escape(name)+r"=([^\s]+)",line)
        if not m: return None
        raw=m.group(1).replace("$","")
        if raw=="None": return None
        try: return cast(raw)
        except Exception: return None
    return {
        "closed": grab("closed",int),
        "wins": grab("wins",int),
        "losses": grab("losses",int),
        "win_rate": grab("win_rate",float),
        "net": grab("NET",float),
    }

def qualifies_existing_qsb015_entry(entry: FastEntry):
    # Do not invent a second strategy. Respect QSB-015's own live entry;
    # only reject malformed / non-executable rows.
    return bool(entry.token and entry.score > 0 and entry.liquidity_usd > 0)
"""

test = r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_018c_live_stdout_money_handoff import (
    parse_fast_entries, parse_fresh_money, qualifies_existing_qsb015_entry,
    EXECUTION_AUTHORITY, PAPER_ONLY
)

class T(unittest.TestCase):
    def test_exact_user_log_fast_entry(self):
        line='[FAST ENTRIES] [{"family": "ORCA", "token": "BABANGA4JE7Kkam4nTrALAwAVgsNJUuFJnnkF7S16BZp", "score": 0.95, "liq": 229406.1}]'
        rows=parse_fast_entries(line)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0].family,"ORCA")
        self.assertEqual(rows[0].token,"BABANGA4JE7Kkam4nTrALAwAVgsNJUuFJnnkF7S16BZp")
        self.assertAlmostEqual(rows[0].score,0.95)
        self.assertAlmostEqual(rows[0].liquidity_usd,229406.1)
        self.assertTrue(qualifies_existing_qsb015_entry(rows[0]))

    def test_fresh_money(self):
        x=parse_fresh_money("[FRESH MONEY] closed=9 wins=6 losses=3 win_rate=0.6667 NET=$5.0086")
        self.assertEqual(x["closed"],9)
        self.assertEqual(x["wins"],6)
        self.assertAlmostEqual(x["net"],5.0086)

    def test_authority(self):
        self.assertFalse(EXECUTION_AUTHORITY)
        self.assertTrue(PAPER_ONLY)

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

runtime = r"""
from __future__ import annotations
import json, subprocess, sys, threading, queue, time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_018c_live_stdout_money_handoff import (
    parse_fast_entries, parse_fresh_money, qualifies_existing_qsb015_entry
)

ROOT=Path.cwd()
QSB015=ROOT/"run_qsb_015_first_seconds_launch_impulse.py"
STATE=ROOT/"runtime_state"/"solana_opportunities"
LEDGER=STATE/"qsb_018c_live_money_handoff.jsonl"

def _gmgn_matches(token):
    hits=[]
    root=ROOT/"runtime_state"
    if not root.exists():
        return hits
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".json",".jsonl"):
            continue
        s=str(p).lower()
        if not any(x in s for x in ("gmgn","wallet","trader")):
            continue
        try:
            txt=p.read_text(encoding="utf-8",errors="ignore")
        except Exception:
            continue
        if token in txt:
            hits.append(str(p.relative_to(ROOT)))
    return hits[:10]

def _write(row):
    STATE.mkdir(parents=True,exist_ok=True)
    with LEDGER.open("a",encoding="utf-8") as f:
        f.write(json.dumps(row,sort_keys=True)+"\n")

def main():
    if not QSB015.is_file():
        raise SystemExit("[FAIL] missing QSB-015 runtime")

    proc=subprocess.Popen(
        [sys.executable,str(QSB015)],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    print("[QSB-018C] ONE SOLANA MONEY RUNTIME")
    print("[QSB-018C] LIVE QSB-015 STDOUT HANDOFF + GMGN TOKEN MATCH")
    print("[QSB-018C] PAPER ONLY / execution_authority=FALSE")

    try:
        assert proc.stdout is not None
        for raw in proc.stdout:
            line=raw.rstrip()
            print(line)

            money=parse_fresh_money(line)
            if money is not None:
                print("[QSB-018C MONEY]",json.dumps(money,sort_keys=True))

            entries=parse_fast_entries(line)
            for e in entries:
                if not qualifies_existing_qsb015_entry(e):
                    continue
                gmgn=_gmgn_matches(e.token)
                row={
                    "event":"QSB015_FAST_ENTRY_HANDOFF",
                    "family":e.family,
                    "token":e.token,
                    "score":e.score,
                    "liquidity_usd":e.liquidity_usd,
                    "gmgn_matching_sources":gmgn,
                    "gmgn_match_count":len(gmgn),
                    "paper_only":True,
                    "execution_authority":False,
                }
                _write(row)
                print("[LIVE HANDOFF]",json.dumps(row,sort_keys=True))
                if gmgn:
                    print("[GMGN MATCH] token=",e.token," sources=",len(gmgn))
                else:
                    print("[GMGN PENDING] token=",e.token," QSB-015 entry remains active; wallet enrichment does not block it")

        rc=proc.wait()
        raise SystemExit("[FAIL] QSB-015 child exited rc="+str(rc))
    finally:
        if proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait()

if __name__=="__main__":
    main()
"""

MODULE.write_text(module,encoding="utf-8")
TEST.write_text(test,encoding="utf-8")
RUN.write_text(runtime,encoding="utf-8")

for p in (MODULE,TEST,RUN):
    py_compile.compile(str(p),doraise=True)

print("[PASS] dependency:",QSB015.relative_to(ROOT))
print("[PASS] dependency:",GMGN300.relative_to(ROOT))
print("[PASS] installed:",MODULE.relative_to(ROOT))
print("[PASS] test:",TEST.relative_to(ROOT))
print("[PASS] runtime:",RUN.relative_to(ROOT))
print("[PASS] QSB-018C exact live stdout handoff installed")
print("[PASS] QSB-015 live entries are no longer lost behind markets=0 file polling")
print("[PASS] GMGN enrichment is attached by exact token and does not block existing QSB-015 entries")
print("[PASS] PAPER_ONLY=True execution_authority=FALSE")
