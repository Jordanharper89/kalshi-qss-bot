import argparse, sqlite3
from contextlib import closing
from pathlib import Path

DB = Path(
    'runtime_state/oracle/oracle_live_execution/'
    'ORACLE218_DISCOVERY.sqlite3'
)

def schema(c):
    c.execute('''CREATE TABLE IF NOT EXISTS oracle231_route_history(
        mint TEXT NOT NULL,
        pump_pool TEXT NOT NULL,
        meteora_pool TEXT NOT NULL,
        first_seen TEXT NOT NULL,
        last_seen TEXT NOT NULL,
        observations INTEGER NOT NULL,
        PRIMARY KEY(mint,pump_pool,meteora_pool))''')
    c.execute('''CREATE TABLE IF NOT EXISTS oracle232_evidence(
        signature TEXT PRIMARY KEY,
        slot INTEGER NOT NULL,
        actor TEXT NOT NULL,
        mint TEXT NOT NULL,
        programs TEXT NOT NULL,
        verified_at TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS oracle234_scores(
        mint TEXT PRIMARY KEY,
        route_count INTEGER NOT NULL,
        observations INTEGER NOT NULL,
        mriya_txs INTEGER NOT NULL,
        priority INTEGER NOT NULL,
        updated_at TEXT NOT NULL)''')

def run(path=DB):
    if not path.is_file():
        raise RuntimeError('HOLD_ORACLE218_DB_MISSING')

    with closing(sqlite3.connect(path, timeout=20)) as c:
        c.execute('PRAGMA busy_timeout=20000')
        rows = c.execute(
            'SELECT mint,pump_pool,meteora_pool,last_seen '
            'FROM universal_routes'
        ).fetchall()

        if not rows:
            raise RuntimeError('HOLD_NO_DISCOVERED_ROUTES')

        schema(c)

        for mint, pump, dlmm, last_seen in rows:
            if not all((mint, pump, dlmm, last_seen)):
                continue
            if pump == dlmm:
                continue

            c.execute('''INSERT INTO oracle231_route_history
                VALUES(?,?,?,?,?,1)
                ON CONFLICT(mint,pump_pool,meteora_pool)
                DO UPDATE SET
                last_seen=excluded.last_seen,
                observations=oracle231_route_history.observations+1
                WHERE excluded.last_seen >
                oracle231_route_history.last_seen''',
                (mint,pump,dlmm,str(last_seen),str(last_seen)))

        count = c.execute(
            'SELECT COUNT(*) FROM oracle231_route_history'
        ).fetchone()[0]
        c.commit()

    print('[ORACLE231_PASS] persistent_routes=',count,
          'execution=FALSE')

def test():
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        p = Path(td) / 'test.db'

        with closing(sqlite3.connect(p)) as c:
            c.execute('CREATE TABLE universal_routes'
                      '(mint,pump_pool,meteora_pool,last_seen)')
            c.execute('INSERT INTO universal_routes VALUES(?,?,?,?)',
                ('mint','pump','dlmm','2026-10-10T10:00:00+00:00'))
            c.commit()

        run(p)
        run(p)

        with closing(sqlite3.connect(p)) as c:
            value = c.execute(
                'SELECT observations FROM oracle231_route_history'
            ).fetchone()[0]
            assert value == 1

    print('[ORACLE231_TEST_PASS] retention=TRUE dedup=TRUE')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--run',action='store_true')
    a = p.parse_args()
    if a.test: test()
    if a.run: run()