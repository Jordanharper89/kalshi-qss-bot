
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

SAMPLE_ROWS = 250000

def inventory(root=None, sample_rows=SAMPLE_ROWS):
    root = Path(root or Path.cwd())

    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")

            q.execute(
                "SELECT sequence_number, observed_at "
                "FROM public.oracle_canonical_observations "
                "ORDER BY sequence_number DESC LIMIT 1"
            )
            newest = q.fetchone()

            q.execute(
                "SELECT sequence_number, observed_at "
                "FROM public.oracle_canonical_observations "
                "ORDER BY sequence_number ASC LIMIT 1"
            )
            oldest = q.fetchone()

            q.execute(
                "WITH recent AS ("
                " SELECT sequence_number, observed_at, source_id, observation_type "
                " FROM public.oracle_canonical_observations "
                " ORDER BY sequence_number DESC LIMIT %s"
                ") "
                "SELECT source_id, observation_type, COUNT(*) AS n, "
                "MIN(observed_at), MAX(observed_at) "
                "FROM recent "
                "GROUP BY source_id, observation_type "
                "ORDER BY n DESC",
                (int(sample_rows),)
            )
            groups = q.fetchall() or []

        c.rollback()

    source_ids = {str(r[0]) for r in groups}
    obs_types = {str(r[1]) for r in groups}

    return {
        "schema_version": "OED-002",
        "inventory_mode": "BOUNDED_RECENT_PHYSICAL_CENSUS",
        "sample_rows_requested": int(sample_rows),
        "sample_rows_accounted": sum(int(r[2]) for r in groups),
        "oldest_sequence": int(oldest[0]) if oldest else None,
        "oldest_observed_at": oldest[1] if oldest else None,
        "newest_sequence": int(newest[0]) if newest else None,
        "newest_observed_at": newest[1] if newest else None,
        "sample_source_count": len(source_ids),
        "sample_observation_type_count": len(obs_types),
        "groups": [
            {
                "source_id": str(source_id),
                "observation_type": str(obs_type),
                "rows": int(n),
                "first_at": first_at,
                "last_at": last_at,
            }
            for source_id, obs_type, n, first_at, last_at in groups
        ],
        "exact_full_table_count_attempted": False,
        "read_only": True,
    }
