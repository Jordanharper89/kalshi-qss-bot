from pathlib import Path
import runpy
from qseries_v2.oracle_learning.olr_043_live_learning_evidence_adapter import adapt_learning_batch
UNDERLYING_RUNNER='run_olr_005_continuous_learning_runtime.py'

if __name__=='__main__':
    print('='*88,flush=True)
    print(' OLR-044 CONTINUOUS LEARNER EVIDENCE RUNTIME',flush=True)
    print('='*88,flush=True)
    print('[OLR-044] live_evidence_linkage=ENABLED execution_authority=FALSE',flush=True)
    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name='__main__')
