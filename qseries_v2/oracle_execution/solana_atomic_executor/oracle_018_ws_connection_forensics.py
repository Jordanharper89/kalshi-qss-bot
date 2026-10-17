
from pathlib import Path
import argparse, asyncio, getpass, json, os, shutil, socket, ssl, unittest

BASE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
NAME = 'oracle_018_ws_connection_forensics.py'
REPORT = Path('runtime_state/oracle/oracle_live_execution/ORACLE_018_WS_FORENSICS.json')
VERSION = 'ORACLE_018_WS_CONNECTION_FORENSICS'
ACCOUNT = 'J3SZrLFzgwDyGDLQCcGLpeuBA5bPGuuTKbhgmWKSsQK1'


def classify(exc):
    status = getattr(exc, 'status_code', None)
    if status is None:
        status = getattr(
            getattr(exc, 'response', None),
            'status_code',
            None
        )
    if status in (401, 403):
        return 'AUTHORIZATION_REJECTED', status
    if status == 429:
        return 'RATE_LIMIT', status
    if isinstance(status, int) and status >= 500:
        return 'PROVIDER_HTTP_ERROR', status
    if isinstance(status, int):
        return 'HANDSHAKE_REJECTED', status
    if isinstance(exc, socket.gaierror):
        return 'DNS_RESOLUTION_FAILURE', None
    if isinstance(exc, ssl.SSLError):
        return 'TLS_FAILURE', None
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return 'CONNECTION_TIMEOUT', None
    if isinstance(exc, ConnectionRefusedError):
        return 'CONNECTION_REFUSED', None
    if isinstance(exc, ConnectionResetError):
        return 'CONNECTION_RESET', None
    if isinstance(exc, OSError):
        return 'NETWORK_OS_ERROR', getattr(exc, 'errno', None)
    return 'UNCLASSIFIED', None


async def check_ws(url, seconds=10, connector=None):
    if connector is None:
        import websockets
        connector = websockets.connect

    info = {
        'connected': False,
        'acknowledged': False,
        'failure': 'NONE',
        'http_or_errno': None,
        'subscription_error_code': None,
        'http_rpc_calls': 0,
        'transaction_simulations': 0
    }

    try:
        async with asyncio.timeout(seconds):
            async with connector(
                url,
                open_timeout=seconds,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=1
            ) as ws:
                info['connected'] = True

                request = {
                    'jsonrpc': '2.0',
                    'id': 1,
                    'method': 'accountSubscribe',
                    'params': [
                        ACCOUNT,
                        {
                            'encoding': 'base64',
                            'commitment': 'processed'
                        }
                    ]
                }

                await ws.send(json.dumps(
                    request,
                    separators=(',', ':')
                ))

                while True:
                    message = json.loads(await ws.recv())
                    if message.get('id') != 1:
                        continue

                    if isinstance(message.get('result'), int):
                        info['acknowledged'] = True
                    else:
                        info['failure'] = 'SUBSCRIPTION_REJECTED'
                        error = message.get('error') or {}
                        code = (
                            error.get('code')
                            if isinstance(error, dict)
                            else None
                        )
                        info['subscription_error_code'] = (
                            code if isinstance(code, int) else None
                        )
                    break

    except Exception as exc:
        info['failure'], info['http_or_errno'] = classify(exc)

    return info


def write_report(record):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    tmp = REPORT.with_suffix('.tmp')
    tmp.write_text(
        json.dumps(record, indent=2, sort_keys=True) + '\n',
        encoding='utf-8'
    )
    tmp.replace(REPORT)


class Tests(unittest.TestCase):

    def test_auth(self):
        obj = type('E', (), {'status_code': 401})()
        self.assertEqual(
            classify(obj)[0],
            'AUTHORIZATION_REJECTED'
        )

    def test_rate(self):
        obj = type('E', (), {'status_code': 429})()
        self.assertEqual(classify(obj)[0], 'RATE_LIMIT')

    def test_timeout(self):
        self.assertEqual(
            classify(TimeoutError())[0],
            'CONNECTION_TIMEOUT'
        )

    def test_dns(self):
        self.assertEqual(
            classify(socket.gaierror(-2, 'secret'))[0],
            'DNS_RESOLUTION_FAILURE'
        )

    def test_no_secret_in_classification(self):
        self.assertNotIn(
            'secret',
            str(classify(RuntimeError('secret')))
        )

    def test_ack_and_single_subscription(self):
        class WS:
            sent = []

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def send(self, message):
                self.sent.append(json.loads(message))

            async def recv(self):
                return '{"id":1,"result":17}'

        result = asyncio.run(check_ws(
            'wss://test',
            connector=lambda *a, **kw: WS()
        ))

        self.assertTrue(result['acknowledged'])
        self.assertEqual(
            WS.sent[0]['method'],
            'accountSubscribe'
        )
        self.assertEqual(result['http_rpc_calls'], 0)

    def test_rejected_subscription(self):
        class WS:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def send(self, message):
                pass

            async def recv(self):
                return (
                    '{"id":1,"error":'
                    '{"code":-32602,"message":"secret"}}'
                )

        result = asyncio.run(check_ws(
            'wss://test',
            connector=lambda *a, **kw: WS()
        ))

        self.assertEqual(
            result['failure'],
            'SUBSCRIPTION_REJECTED'
        )
        self.assertNotIn('secret', str(result))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--seconds', type=int, default=10)
    args = parser.parse_args()

    if args.test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if result.wasSuccessful() else 1

    if args.check:
        if not 5 <= args.seconds <= 15:
            print('[HOLD] CHECK_DURATION_5_TO_15')
            return 2

        key = getpass.getpass(
            'Helius API key (hidden): '
        ).strip()

        if not key:
            print('[HOLD] MISSING_KEY')
            return 2

        override = os.environ.get(
            'SOLANA_WS_URL', ''
        ).strip()

        url = (
            override
            or 'wss://mainnet.helius-rpc.com/?api-key=' + key
        )

        source = (
            'EXPLICIT_WS_OVERRIDE'
            if override
            else 'HELIUS_STANDARD_WS'
        )

        if not url.startswith('wss://'):
            print('[HOLD] WSS_REQUIRED')
            return 2

        info = asyncio.run(
            check_ws(url, args.seconds)
        )

        record = {
            'build': VERSION,
            'endpoint_source': source,
            **info
        }

        write_report(record)

        print(
            '[WS_DIAGNOSTIC]',
            json.dumps(record, sort_keys=True)
        )
        print(
            '[SCANNER] UNCHANGED '
            '[HTTP_RPC] 0 '
            '[SIGNING] FALSE '
            '[BROADCAST] FALSE'
        )
        print('[REPORT]', REPORT)

        return 0 if info['acknowledged'] else 2

    dst = BASE / NAME

    if not dst.parent.is_dir():
        print('[FAIL] CANONICAL_EXECUTOR_DIRECTORY_MISSING')
        return 2

    if dst.resolve() != Path(__file__).resolve():
        shutil.copyfile(Path(__file__), dst)

    print('[PASS]', VERSION, dst)
    print(
        '[MODE] ONE_STANDARD_WEBSOCKET_CONNECTION; '
        'ONE_ACCOUNT_SUBSCRIPTION; ZERO_HTTP_RPC'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
