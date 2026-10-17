import argparse, sqlite3
from contextlib import closing
from datetime import datetime, timezone
from build_oracle_231 import DB, schema
from build_oracle_233 import analyze

def score(rows):
    return sorted([
        (
            mint,
            routes,
            obs,
            txs,
            min(100,
                10*routes
                + min(obs,50)
                + 5*min(txs,8))
        )
        for mint,routes,obs,txs in rows
    ],key=lambda v:(-v[4],v[0]))

def run(path=DB):
    entries=score(analyze(path))
    timestamp=datetime.now(timezone.utc).isoformat()

    with closing(sqlite3.connect(path,timeout=20)) as c:
        schema(c)

        for mint,routes,obs,txs,priority in entries:
            c.execute('''
                INSERT INTO oracle234_scores
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(mint) DO UPDATE SET
                route_count=excluded.route_count,
                observations=excluded.observations,
                mriya_txs=excluded.mriya_txs,
                priority=excluded.priority,
                updated_at=excluded.updated_at
            ''',(
                mint,routes,obs,txs,
                priority,timestamp
            ))

        c.commit()

    print('[ORACLE234_RESULT]',
          'scored=',len(entries),
          'priority_is_not_profit=TRUE')

def test():
    rows=[
        ('a',1,5,0),
        ('b',2,7,2)
    ]

    ranked=score(rows)

    assert ranked[0][0]=='b'
    assert ranked[0][4]>ranked[1][4]

    print('[ORACLE234_TEST_PASS] '
          'deterministic_priority=TRUE '
          'profitability_not_claimed=TRUE')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if a.test: test()
    if a.run: run()