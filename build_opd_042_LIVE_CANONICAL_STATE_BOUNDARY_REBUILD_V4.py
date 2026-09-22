from pathlib import Path
import py_compile
R=Path.cwd(); P=R/"qseries_v2"/"oracle_predictive_discovery"/"opd_042_live_state_to_prospective_intake_bridge.py"
T=R/"test_opd_042_live_state_to_prospective_intake_bridge.py"; P.parent.mkdir(parents=True,exist_ok=True)
P.write_text("""from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_041_exact_live_token_materializer import materialize_exact_live_tokens
from qseries_v2.oracle_predictive_data.opd_032_prospective_state_intake_ledger import observe
SOURCES=('source.crypto.condition.btc.bitcoin.fastest_fee_rate','source.crypto.condition.btc.bitcoin.half_hour_fee_rate')
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
def production_snapshot(root=None):
    root=Path(root or Path.cwd()).resolve()
    sql=\"\"\"SELECT DISTINCT ON (source_id) sequence_number,observed_at,source_id,canonical_observation_json
    FROM public.oracle_canonical_observations
    WHERE observation_type='crypto_condition_snapshot' AND source_id=ANY(%s)
    ORDER BY source_id,sequence_number DESC\"\"\"
    with connect(root,autocommit=False) as c:
        with c.cursor() as q:
            q.execute('SET TRANSACTION READ ONLY');q.execute(\"SET LOCAL statement_timeout='5000ms'\")
            q.execute(sql,(list(SOURCES),)); rows=q.fetchall() or []
        c.rollback()
    if len(rows)!=len(SOURCES): raise RuntimeError('OPD-042 requires current rows for both frozen OPD-030 condition sources')
    obs=[{'sequence_number':int(a),'observed_at':b.isoformat(),'source_id':c,'canonical_observation_json':d} for a,b,c,d in rows]
    return {'schema_version':'OPD-042-LIVE','state_at_t_sequence':max(x['sequence_number'] for x in obs),'state_at_t_observed_at':max(x['observed_at'] for x in obs),'observations':obs,'read_only':True,'execution_authority':False}
def bridge_snapshot(snapshot,root=None):
    root=Path(root or Path.cwd()).resolve()
    tokens=materialize_exact_live_tokens(root,snapshot)
    enriched=dict(snapshot); enriched['feature_tokens']=list(tokens)
    return observe(enriched,root)
def cycle(root=None): return bridge_snapshot(production_snapshot(root),root)
""",encoding="utf-8")
T.write_text("""from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_042_live_state_to_prospective_intake_bridge import production_snapshot,bridge_snapshot
x=production_snapshot(Path.cwd()); assert isinstance(x,dict) and len(x['observations'])==2
r=bridge_snapshot(x,Path.cwd()); print('[STATE_SEQ]',x['state_at_t_sequence']); print('[OBSERVE_RETURN]',repr(r)[:1000])
print('[PASS] OPD-042 V4 exact live canonical state boundary certified')
""",encoding="utf-8")
py_compile.compile(str(P),doraise=True);py_compile.compile(str(T),doraise=True)
print("[PASS] OPD-042 V4 foundational rebuild installed")