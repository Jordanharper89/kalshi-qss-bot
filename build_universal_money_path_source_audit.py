from pathlib import Path
import re, hashlib

ROOT=Path.cwd()
FILES=[
"qseries_v2/oracle_execution/solana_atomic_executor/live_money_runtime.py",
"qseries_v2/oracle_execution/solana_atomic_executor/checkpoint25_expanded_live_universe_cutover.py",
"qseries_v2/oracle_execution/solana_atomic_executor/live_money_supervisor.py",
"qseries_v2/oracle_execution/solana_atomic_executor/live_money_driver.py",
"qseries_v2/oracle_execution/solana_atomic_executor/runtime.py",
]
PAT=re.compile(r"HOT_BOOK|INVENTORY|CAPACITY|REGISTRY|selected|active|mriya|pair|token|318|320|\b28\b",re.I)
out=[]
for rel in FILES:
    p=ROOT/rel
    out.append("="*120)
    out.append("FILE "+rel)
    if not p.is_file():
        out.append("MISSING")
        continue
    s=p.read_text(encoding="utf-8")
    lines=s.splitlines()
    out.append("SHA256 "+hashlib.sha256(s.encode()).hexdigest())
    out.append("LINES "+str(len(lines)))
    hits=[i for i,x in enumerate(lines) if PAT.search(x)]
    ranges=[]
    for i in hits:
        a=max(0,i-3); b=min(len(lines),i+4)
        if ranges and a<=ranges[-1][1]:
            ranges[-1]=(ranges[-1][0],max(ranges[-1][1],b))
        else:
            ranges.append((a,b))
    for a,b in ranges:
        out.append("--- L%d-L%d ---"%(a+1,b))
        out.extend("%04d %s"%(j+1,lines[j]) for j in range(a,b))
report="\n".join(out)+"\n"
path=ROOT/"UNIVERSAL_MONEY_PATH_AUDIT.txt"
path.write_text(report,encoding="utf-8")
print("[PASS] universal money-path source audit")
print("[FILES]",len(FILES))
print("[REPORT]",path)
print("[KEY] untouched")
print("[WALLET] untouched")
print("[BROADCAST] untouched")