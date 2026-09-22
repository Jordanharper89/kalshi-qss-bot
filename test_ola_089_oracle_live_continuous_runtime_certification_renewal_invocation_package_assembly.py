from __future__ import annotations
from datetime import datetime,timedelta,timezone
import importlib.util,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODULE_PATH=ROOT/"qseries_v2"/"oracle_intelligence"/"live_acquisition"/"oracle_live_continuous_runtime_certification_renewal_invocation_package_assembly.py"
def load_module():
    name="ola089_test_target"; spec=importlib.util.spec_from_file_location(name,MODULE_PATH); assert spec and spec.loader
    module=importlib.util.module_from_spec(spec); sys.modules[name]=module
    try: spec.loader.exec_module(module)
    finally: sys.modules.pop(name,None)
    return module

def make_upstream(checked_at,ready=True,required=True):
    m=__import__("qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_certification_renewal_invocation_readiness_gate",fromlist=["OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessStatus"])
    cls=m.OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessStatus
    status=("renewal_required_invocation_ready" if required else "renewal_eligible_invocation_ready") if ready else "renewal_required_invocation_blocked"
    vals={
    "schema_version":"OLA-088","engine_id":"OLA-088","status":status,"renewal_invocation_ready":ready,"renewal_eligible":True,"renewal_required":required,"renewal_authorized":ready,"operator_authorization_id":"operator-test" if ready else "","authorized_at":checked_at-timedelta(seconds=1) if ready else None,"checked_at":checked_at,"certification_usable":not required,"certification_expired":required,"certification_published_at":checked_at-timedelta(seconds=101),"certification_age_seconds":101.0,"renewal_due_at_age_seconds":80.0,"expiration_age_seconds":100.0,"seconds_until_renewal_due":-21.0,"seconds_until_expiration":-1.0,"attestation_id":"attestation-test","attestation_hash":"a"*64,"upstream_authorization_status":"renewal_required_authorized" if ready else "renewal_required_awaiting_authorization","upstream_authorization_status_hash":"b"*64,"upstream_authorization_schema_version":"OLA-087","upstream_renewal_schema_version":"OLA-086","upstream_expiration_schema_version":"OLA-085","upstream_status_schema_version":"OLA-084","upstream_attestation_schema_version":"OLA-083","upstream_certification_schema_version":"OLA-082","upstream_advancement_schema_version":"OLA-081","upstream_monitor_schema_version":"OLA-068","upstream_runtime_schema_version":"OLA-074","current_file":"current.json","immutable_evidence_file":"evidence.json","lineage_verified":True,"safety_boundary_verified":True,"read_only":True,"execution_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"trade_authorization_allowed":False,"order_placement_allowed":False,"funds_moved":False,"portfolio_mutated":False,"postgresql_read_performed":False,"postgresql_write_performed":False,"runtime_started":False,"runtime_stopped":False,"runtime_restarted":False,"runtime_imported":False,"runtime_invoked":False,"runtime_lock_mutated":False,"files_written":False,"renewal_performed":False,"certification_evidence_mutated":False,"renewal_executor_imported":False,"renewal_executor_invoked":False}
    return cls(**vals,status_hash=m.stable_hash(vals))

def main():
    module=load_module(); now=datetime(2026,7,20,3,0,tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory() as td:
        for required,mode in ((False,"eligible"),(True,"required")):
            upstream=make_upstream(now,True,required)
            result=module.assemble_oracle_live_continuous_runtime_certification_renewal_invocation_package(repository_root=td,assembled_at=now,upstream_status=upstream)
            assert result.package_ready is True and result.renewal_mode==mode and result.verify_package_hash() is True
            assert result.renewal_performed is False and result.files_written is False and result.renewal_executor_invoked is False
        blocked=make_upstream(now,False,True)
        try: module.assemble_oracle_live_continuous_runtime_certification_renewal_invocation_package(repository_root=td,assembled_at=now,upstream_status=blocked)
        except module.OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageNotReady: pass
        else: raise AssertionError("blocked readiness assembled a package")
    print("[PASS] OLA-089 Oracle Live Continuous Runtime Certification Renewal Invocation Package Assembly")
if __name__=="__main__": main()
