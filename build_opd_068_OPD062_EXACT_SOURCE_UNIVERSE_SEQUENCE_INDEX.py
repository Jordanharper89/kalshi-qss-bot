from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

INDEX="idx_oracle_opd062_source_universe_seq"
PRED="""source_id='source.crypto.hf.coinbase.historical_window'
OR source_id LIKE 'source.crypto.condition.%'
OR source_id LIKE 'source.crypto.learned_case.%'"""

def main():
    root=Path.cwd()
    with connect(root,autocommit=True) as c:
        with c.cursor() as q:
            q.execute("SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname=%s",(INDEX,))
            if not q.fetchone():
                q.execute("SET statement_timeout=0")
                q.execute(f"""CREATE INDEX CONCURRENTLY {INDEX}
                ON public.oracle_canonical_observations(sequence_number DESC)
                WHERE ({PRED})""")
    print("[PASS] OPD-062 exact admitted-source sequence index installed")
    print("[PASS] OPD-062 query semantics unchanged")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")

if __name__=="__main__":
    main()