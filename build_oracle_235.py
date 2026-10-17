import argparse, json, sqlite3
from contextlib import closing
from pathlib import Path
from build_oracle_231 import DB

REPORT=Path(
    'runtime_state/oracle/oracle_live_execution/'
    'ORACLE235_DISCOVERY_ACCEPTANCE.json'
)

def run(path=DB,report=REPORT):
    result={
        'build':'ORACLE235',
        'signing':False,
        'broadcast':False,
        'profit_certified':False,
        'dual_zone_certified':False,
        'status':'HOLD'
    }

    if not path.is_file():
        result['reason']='NO_REGISTRY'
    else:
        uri=path.resolve().as_uri()+'?mode=ro'

        with closing(sqlite3.connect(uri,uri=True)) as c:
            names={
                row[0] for row in c.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table'"
                )
            }

            required={
                'universal_routes',
                'oracle231_route_history',
                'oracle232_evidence',
                'oracle234_scores'
            }

            if not required.issubset(names):
                result['reason']='MISSING_DISCOVERY_COMPONENTS'
            else:
                result['registered_routes']=c.execute(
                    'SELECT COUNT(*) FROM universal_routes'
                ).fetchone()[0]

                result['historical_routes']=c.execute(
                    'SELECT COUNT(*) FROM oracle231_route_history'
                ).fetchone()[0]

                result['mriya_evidence']=c.execute(
                    'SELECT COUNT(*) FROM oracle232_evidence'
                ).fetchone()[0]

                result['scored_mints']=c.execute(
                    'SELECT COUNT(*) FROM oracle234_scores'
                ).fetchone()[0]

                result['universal_persistent']=(
                    result['historical_routes'] >=
                    result['registered_routes'] > 0
                )

                result['dual_zone_certified']=(
                    result['universal_persistent']
                    and result['mriya_evidence']>0
                )

                result['status']=(
                    'PASS_DISCOVERY_ONLY'
                    if result['dual_zone_certified']
                    else 'HOLD'
                )

                result['reason']=(
                    'VERIFIED_MRIYA_EVIDENCE_REQUIRED'
                    if result['mriya_evidence']==0
                    else 'DISCOVERY_ONLY_EXECUTION_GATED'
                )

    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(
        json.dumps(result,indent=2),
        encoding='utf-8'
    )

    print('[ORACLE235_RESULT]',
          json.dumps(result,sort_keys=True))
    print('[REPORT]',report)
    return result

def test():
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        x=run(
            Path(td)/'absent.db',
            Path(td)/'report.json'
        )

        assert not x['dual_zone_certified']
        assert not x['signing']
        assert not x['broadcast']

    print('[ORACLE235_TEST_PASS] '
          'no_false_certification=TRUE')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if a.test: test()
    if a.run: run()