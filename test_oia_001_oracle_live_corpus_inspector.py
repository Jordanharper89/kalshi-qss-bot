from datetime import datetime, timezone
from qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector import (
    ENGINE_ID, SCHEMA_VERSION, OracleLiveCorpusInspector, format_report, stable_hash,
)

NOW=datetime(2026,7,20,2,0,0,tzinfo=timezone.utc)
class Cursor:
    def __init__(self): self.mode=None; self.closed=False
    def execute(self,sql,params=None):
        assert "INSERT" not in sql.upper() and "UPDATE" not in sql.upper() and "DELETE" not in sql.upper()
        self.mode="summary" if "oia001:corpus_summary" in sql else "markets"
        if self.mode=="markets": assert params==(25,)
    def fetchone(self):
        return (120,1,24,datetime(2026,7,20,0,0,tzinfo=timezone.utc),datetime(2026,7,20,1,59,tzinfo=timezone.utc),datetime(2026,7,20,1,59,30,tzinfo=timezone.utc))
    def fetchall(self):
        return [
          ("KXTEST-A",80,datetime(2026,7,20,0,0,tzinfo=timezone.utc),datetime(2026,7,20,1,59,tzinfo=timezone.utc),datetime(2026,7,20,1,59,30,tzinfo=timezone.utc),"0.41","0.43","0.42","1250.00","5400.00","2026-07-21T00:00:00Z"),
          ("KXTEST-B",40,datetime(2026,7,20,0,10,tzinfo=timezone.utc),datetime(2026,7,20,1,45,tzinfo=timezone.utc),datetime(2026,7,20,1,45,tzinfo=timezone.utc),"0.60","0.64","0.62","800.00","900.00","2026-07-21T00:00:00Z"),
        ]
    def close(self): self.closed=True
class Connection:
    def __init__(self): self.cursor_value=Cursor(); self.closed=False
    def cursor(self): return self.cursor_value
    def close(self): self.closed=True

def run_test():
    connections=[]
    def factory():
        connection=Connection(); connections.append(connection); return connection
    inspector=OracleLiveCorpusInspector(connection_factory=factory,stale_after_seconds=600,market_limit=25)
    report=inspector.inspect(inspected_at=NOW)
    assert report.schema_version==SCHEMA_VERSION=="OIA-001"
    assert report.engine_id==ENGINE_ID=="OIA-001"
    assert report.observation_count==120 and report.market_count==2
    assert report.source_count==1 and report.acquisition_batch_count==24
    assert round(report.corpus_duration_seconds)==7140
    assert round(report.observations_per_hour,4)==round(120/(7140/3600),4)
    assert report.active_market_count==1 and report.stale_market_count==1
    assert report.markets[0].market_id=="KXTEST-A" and report.markets[0].stale is False
    assert report.markets[1].market_id=="KXTEST-B" and report.markets[1].stale is True
    assert report.read_only is True and report.execution_allowed is False
    assert report.alerts_allowed is False and report.qseries_handoff_allowed is False
    payload=dict(report.to_dict()); expected_hash=payload.pop("report_hash")
    assert expected_hash==stable_hash(payload)
    rendered=format_report(report)
    assert "KXTEST-A" in rendered and "Observations:           120" in rendered
    assert connections[0].closed is True and connections[0].cursor_value.closed is True
    print("[PASS] OIA-001 Oracle Live Corpus Inspector")
if __name__=="__main__": run_test()
