from pathlib import Path
import runpy
from qseries_v2.oracle_production_hardening.oph_020_universal_postgresql_producer_admission import install_universal_postgresql_ingress
UNDERLYING_RUNNER='run_ocr_013_continuous_reasoning_runtime.py'

if __name__=='__main__':
    print('='*88,flush=True)
    print(' OPH-022 UNIVERSAL POSTGRESQL INGRESS child=reasoning',flush=True)
    print('='*88,flush=True)
    install_universal_postgresql_ingress('oracle.reasoning',Path.cwd())
    print('[OPH-022] direct_canonical_postgresql_write_authority=FALSE',flush=True)
    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name='__main__')
