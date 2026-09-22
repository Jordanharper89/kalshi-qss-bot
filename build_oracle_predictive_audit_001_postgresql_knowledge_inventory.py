from pathlib import Path
ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_001_postgresql_knowledge_inventory.py'
BODY=r"""
from pathlib import Path
from collections import Counter,defaultdict
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

root=Path.cwd()
with connect(root,autocommit=False) as c:
    with c.cursor() as q:
        q.execute("SET TRANSACTION READ ONLY")
        q.execute("SET LOCAL statement_timeout='10000ms'")
        q.execute("SELECT n_live_tup FROM pg_stat_user_tables WHERE schemaname='public' AND relname='oracle_canonical_observations'")
        estimate=(q.fetchone() or (0,))[0]
        q.execute("SELECT sequence_number,observed_at,observation_type,source_id FROM public.oracle_canonical_observations ORDER BY sequence_number DESC LIMIT 5000")
        rows=tuple(q.fetchall() or ())
    c.rollback()

types=Counter(str(r[2]) for r in rows)
sources=Counter(str(r[3]) for r in rows)
latest={}
for seq,ts,otype,source in rows:
    source=str(source)
    if source not in latest:
        latest[source]=(int(seq),str(ts),str(otype))
families=defaultdict(int)
for source,n in sources.items():
    if source.startswith("source.crypto."): families["crypto"]+=n
    elif source.startswith("source.osn.") or "sports" in source: families["sports"]+=n
    elif source.startswith("source.kalshi") or "kalshi" in source: families["kalshi"]+=n
    elif source.startswith("source.solana") or "solana" in source: families["solana"]+=n
    else: families["other"]+=n

print("[TABLE_ESTIMATE]",int(estimate or 0))
print("[LATEST_SAMPLE_ROWS]",len(rows))
print("[FAMILIES]",dict(sorted(families.items())))
print("[TOP_TYPES]",types.most_common(20))
print("[TOP_SOURCES]",sources.most_common(30))
for s in sorted(x for x in latest if x.startswith("source.crypto."))[:50]:
    print("[CRYPTO_SOURCE]",s,latest[s],sources[s])
assert rows,"canonical PostgreSQL latest-window is empty"
print("[PASS] OPA-001 read-only PostgreSQL knowledge inventory complete")
"""

def main():
    print("="*120)
    print(' ORACLE PREDICTIVE AUDIT 001 POSTGRESQL KNOWLEDGE INVENTORY INSTALLER')
    print("="*120)
    TEST.write_text(BODY.lstrip(),encoding="utf-8")
    print("[PASS] wrote",TEST.name)
    print("[PASS] read-only audit; no production mutation")

if __name__=="__main__":
    main()