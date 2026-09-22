from pathlib import Path

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_canonical_market_history_access_index import MARKET_ID_EXPRESSION

root = Path.cwd()

sql = f"""
EXPLAIN (COSTS TRUE, FORMAT TEXT)
SELECT
    sequence_number,
    acquired_at,
    ({MARKET_ID_EXPRESSION}) AS market_id
FROM public.oracle_canonical_observations
WHERE observation_type='market_snapshot'
ORDER BY sequence_number DESC
LIMIT 500
"""

c = connect(root, autocommit=False)
q = c.cursor()

q.execute("SET TRANSACTION READ ONLY")

print("=== RECENT MARKET_SNAPSHOT PLAN ===")
q.execute(sql)
for row in q.fetchall():
    print(row[0])

print("=== CANONICAL INDEXES ===")
q.execute("""
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname='public'
  AND tablename='oracle_canonical_observations'
ORDER BY indexname
""")

for row in q.fetchall():
    print(row)

c.rollback()
c.close()