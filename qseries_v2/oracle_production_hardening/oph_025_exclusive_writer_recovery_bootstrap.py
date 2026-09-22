from __future__ import annotations
from pathlib import Path
OPH_025_BUILD_ID="OPH-025"
OPH_025_REVISION="OPH_025_EXCLUSIVE_WRITER_RECOVERY_BOOTSTRAP_V1"

def install_writer_recovery_bootstrap(root=None):
    from . import oph_021_exclusive_postgresql_canonical_writer as writer
    from .oph_024_postgresql_stale_claim_recovery import recover_stale_claims
    root=Path(root or Path.cwd()).resolve()
    if getattr(writer,"_oph025_recovery_bootstrap",False):return False
    original=writer.run_exclusive_writer_forever
    def recovered(root_arg=None,progress=None,idle_sleep_seconds=0.002):
        actual=Path(root_arg or root).resolve()
        recovered_ids=recover_stale_claims(actual)
        if progress:progress(f"[OPH-025 RECOVERY] stale_claims_recovered={len(recovered_ids)}")
        return original(actual,progress,idle_sleep_seconds)
    writer.run_exclusive_writer_forever=recovered
    writer._oph025_recovery_bootstrap=True
    return True

def verify_oph_025_exclusive_writer_recovery_bootstrap(root=None):
    from .oph_024_postgresql_stale_claim_recovery import verify_oph_024_postgresql_stale_claim_recovery
    return verify_oph_024_postgresql_stale_claim_recovery(root) and OPH_025_BUILD_ID=="OPH-025"
