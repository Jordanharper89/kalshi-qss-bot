import argparse, sqlite3
from contextlib import closing
from pathlib import Path
from build_oracle_231 import DB, schema

def analyze(path=DB):
    if not path.is_file():
        raise RuntimeError('HOLD_REGISTRY_MISSING')

    with closing(sqlite3.connect(path,timeout=20)) as c:
        schema(c)
        rows = c.execute('''
            SELECT h.mint,
                   COUNT(*) AS routes,
                   SUM(h.observations) AS observations,
                   (SELECT COUNT(*)
                    FROM oracle232_evidence e
                    WHERE e.mint=h.mint) AS mriya_txs
            FROM oracle231_route_history h
            GROUP BY h.mint
            ORDER BY observations DESC
        ''').fetchall()

    print('[ORACLE233_RESULT]',
          'watched_mints=',len(rows),
          'mriya_verified_mints=',sum(x[3]>0 for x in rows),
          'repeated_observation_mints=',sum(x[2]>1 for x in rows))

    return rows

def test():
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        path=Path(td)/'test.db'

        with closing(sqlite3.connect(path)) as c:
            schema(c)
            c.execute(
                "INSERT INTO oracle231_route_history "
                "VALUES('mint','pump','dlmm','t','t',3)"
            )
            c.commit()

        assert analyze(path)[0][2] == 3

    print('[ORACLE233_TEST_PASS] historical_counts=TRUE')

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if a.test: test()
    if a.run: analyze()