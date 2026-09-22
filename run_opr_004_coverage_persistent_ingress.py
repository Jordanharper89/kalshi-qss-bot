from pathlib import Path
import runpy,time
from qseries_v2.oracle_postgresql_reliability.opr_002_persistent_producer_ingress import install_persistent_postgresql_ingress
ORH_005_BUILD_ID="ORH-005"
UNDERLYING_RUNNER='run_opc_030_high_throughput_coverage_child.py'
PRODUCER='oracle.coverage'
BACKOFF_SECONDS=(1.0,2.0,5.0,10.0,30.0)

if __name__=='__main__':
    print('='*88,flush=True)
    print(' OPR-004 PERSISTENT POSTGRESQL INGRESS child=coverage — ORH-005 RESILIENT',flush=True)
    print('='*88,flush=True)
    failures=0
    while True:
        try:
            install_persistent_postgresql_ingress(PRODUCER,Path.cwd())
            print('[ORH-005] persistent_queue_session=TRUE direct_canonical_postgresql_write_authority=FALSE',flush=True)
            runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name='__main__')
            raise RuntimeError('underlying runner returned unexpectedly')
        except KeyboardInterrupt:
            raise
        except SystemExit as exc:
            code=exc.code if isinstance(exc.code,int) else 0
            if code in (0,None): raise
            failures+=1
            delay=BACKOFF_SECONDS[min(failures-1,len(BACKOFF_SECONDS)-1)]
            print(f'[ORH-005 INGRESS RECOVERY] child=coverage status=DEGRADED exit_code={code} retry_in={delay:.1f}s execution_authority=FALSE',flush=True)
            time.sleep(delay)
        except Exception as exc:
            failures+=1
            delay=BACKOFF_SECONDS[min(failures-1,len(BACKOFF_SECONDS)-1)]
            print(f'[ORH-005 INGRESS RECOVERY] child=coverage status=DEGRADED failure={failures} type={type(exc).__name__} retry_in={delay:.1f}s execution_authority=FALSE',flush=True)
            time.sleep(delay)
