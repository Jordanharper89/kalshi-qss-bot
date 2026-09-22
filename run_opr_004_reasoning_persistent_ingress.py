from pathlib import Path
import runpy
from qseries_v2.oracle_postgresql_reliability.opr_002_persistent_producer_ingress import install_persistent_postgresql_ingress
UNDERLYING_RUNNER='run_ocr_013_continuous_reasoning_runtime.py'

if __name__=='__main__':
    print('='*88,flush=True)
    print(' OPR-004 PERSISTENT POSTGRESQL INGRESS child=reasoning',flush=True)
    print('='*88,flush=True)
    install_persistent_postgresql_ingress('oracle.reasoning',Path.cwd())
    print('[OPR-004] persistent_queue_session=TRUE direct_canonical_postgresql_write_authority=FALSE',flush=True)
    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name='__main__')
