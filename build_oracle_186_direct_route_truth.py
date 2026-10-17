
"""ORACLE186 complete standalone diagnostic replacement."""
import argparse
import ast
from pathlib import Path

from build_oracle_185_isolated_bootstrap_replacement import CODE as PREVIOUS

ROOT = Path("qseries_v2/oracle_execution/solana_atomic_executor")
DEST = ROOT / "oracle186_direct_route_truth.py"


def replacement():
    s = PREVIOUS

    def once(before, after):
        nonlocal s
        n = s.count(before)
        if n != 1:
            raise RuntimeError("HOLD_ORACLE186_SOURCE_DRIFT_COUNT_" + str(n))
        s = s.replace(before, after, 1)

    once("ORACLE185_DIRECT_RESULTS.json", "ORACLE186_DIRECT_RESULTS.json")
    once("'build':'ORACLE185'", "'build':'ORACLE186'")
    once(
        "print('[ORACLE185_ROUTE] direction=%s stage=%s bytes=%s reason=%s broadcast=FALSE' %",
        "print('[ORACLE186_ROUTE] direction=%s stage=%s bytes=%s reason=%s broadcast=FALSE' %"
    )
    once("print('[ORACLE185_RESULT]',status",
         "print('[ORACLE186_RESULT]',status")

    once(
        "row={'token':token[:10],'direction':direction,'diagnostic_only':True}",
        "row={'token':token[:10],'direction':direction,'diagnostic_only':True,'stage':'ADMISSION'}"
    )
    once(
        "route=r.same_snapshot_route(user,snap,opp)",
        "row['stage']='ROUTE_CONSTRUCTION'\n"
        "                    route=r.same_snapshot_route(user,snap,opp)"
    )
    once(
        "route,_,_=r._fast_010_profit_lock_route(route,direction,bound)",
        "row['stage']='PROFIT_LOCK'\n"
        "                    route,_,_=r._fast_010_profit_lock_route(route,direction,bound)"
    )
    once(
        "row.update(q181.inspect_route(route))",
        "row['stage']='SWAP2_ACCOUNT_LAYOUT'\n"
        "                    row.update(q181.inspect_route(route))"
    )
    once(
        "compiled=r.compile_current(user,route)",
        "row['stage']='NATIVE_COMPILE'\n"
        "                    compiled=r.compile_current(user,route)"
    )
    once(
        "row['stage']='COMPILE_HOLD'",
        "row['stage']='COMPILE_HOLD'\n"
        "                        row['reason_code']='NO_LEGAL_PACKET_OR_ALT_UNAVAILABLE'\n"
        "                        row['compile_reason']=str(compiled.get('reason','UNKNOWN'))[:60]"
    )
    once(
        "sim=r.simulate_current(compiled,user)",
        "row['stage']='SIGNED_SIMULATION'\n"
        "                        sim=r.simulate_current(compiled,user)"
    )

    once(
        "row.update(stage='HOLD',reason=type(exc).__name__)\n"
        "                    message=str(exc)\n"
        "                    if message.isascii() and message.isupper() and len(message)<100:\n"
        "                        row['code']=message",
        """failed_at=row['stage']
                    row.update(stage='HOLD',failed_at=failed_at,reason=type(exc).__name__)
                    import re
                    message=str(exc)
                    m=re.fullmatch(r'[A-Z][A-Z0-9_]{3,95}',message)
                    row['code']=message if m else 'ERROR_DETAIL_REDACTED'
                    print('[ORACLE186_HOLD] direction=%s at=%s code=%s type=%s' %
                          (direction,failed_at,row['code'],type(exc).__name__),flush=True)"""
    )

    once(
        "print('[ORACLE185_BOOTSTRAP_HOLD]',reason,flush=True)",
        "print('[ORACLE186_BOOTSTRAP_HOLD]',reason,flush=True)"
    )
    once(
        "p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')",
        "p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true');"
        "p.add_argument('--max-pairs',type=int,default=4)"
    )
    once(
        "test() if a.test else run() if a.run else p.error('choose --test or --run')",
        "test() if a.test else run(max_pairs=max(1,min(a.max_pairs,8))) "
        "if a.run else p.error('choose --test or --run')"
    )

    ast.parse(s)
    return s


def test():
    s = replacement()
    assert "original(method,*args,**kwargs)" in s
    assert "r.run(" not in s and "r.serve_canonical(" not in s
    assert "ORACLE185_BROADCAST_FORBIDDEN" in s
    assert "ORACLE186_HOLD" in s and "failed_at" in s
    assert "ERROR_DETAIL_REDACTED" in s
    print("[TEST PASS] ORACLE186 complete replacement, stage evidence, no send")


def install():
    if not (ROOT / "runtime.py").is_file():
        raise RuntimeError("HOLD_ORACLE186_RUNTIME_MISSING")
    if not (ROOT / "oracle185_isolated_bootstrap_replacement.py").is_file():
        raise RuntimeError("HOLD_ORACLE186_MISSING_PREVIOUS_MODULE")

    content = replacement()
    if DEST.exists() and DEST.read_text(encoding="utf-8") != content:
        raise RuntimeError("HOLD_ORACLE186_EXISTING_MODULE_DIFFERS")

    DEST.write_text(content, encoding="utf-8")
    print("[INSTALL PASS] ORACLE186 direct-route diagnostics; scanner unchanged")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    args = p.parse_args()
    test() if args.test else install()
