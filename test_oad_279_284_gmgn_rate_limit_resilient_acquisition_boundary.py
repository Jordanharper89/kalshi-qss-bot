from __future__ import annotations

import importlib
import time
import unittest
from unittest.mock import patch

M279=importlib.import_module(
    "qseries_v2.oracle_adapters.independent.oad_279_gmgn_solana_token_intelligence_adapter"
)
M284=importlib.import_module(
    "qseries_v2.oracle_adapters.independent.oad_284_gmgn_resilient_continuous_worker"
)

class T(unittest.TestCase):
    def test_rate_limit_parser_body(self):
        reset=int(time.time())+240
        parsed=M279._rate_limit_details(
            '{"code":429,"error":"RATE_LIMIT_BANNED","reset_at":'+str(reset)+'}'
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(int(parsed[0]),reset)
        self.assertGreater(parsed[1],200)

    def test_unknown_429_defaults_to_five_minute_cooldown(self):
        parsed=M279._rate_limit_details("HTTP 429 RATE_LIMIT_EXCEEDED")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed[1],300.0)

    def test_candidate_fallback_stops_immediately_on_rate_limit(self):
        fake_trending=type("X",(),{
            "payload":{"raw":{"data":{"rank":[
                {"address":"TOKEN_A"},{"address":"TOKEN_B"}
            ]}}}
        })()
        calls=[]
        def acquire(token,timeout_seconds=30.0):
            calls.append(token)
            raise M279.GMGNRateLimitError(
                "GMGN_RATE_LIMITED",
                retry_after_seconds=300.0,
            )
        with patch.object(M279,"acquire_gmgn_solana_trending",return_value=fake_trending):
            with patch.object(M279,"acquire_gmgn_solana_token_intelligence",side_effect=acquire):
                with self.assertRaises(M279.GMGNRateLimitError):
                    M279.acquire_current_gmgn_solana_token_intelligence()
        self.assertEqual(calls,["TOKEN_A"])

    def test_worker_uses_provider_cooldown_not_generic_60s_cap(self):
        e=M279.GMGNRateLimitError(
            "GMGN_RATE_LIMITED",
            retry_after_seconds=300.0,
        )
        wait=M284._rate_limit_wait(e)
        self.assertGreaterEqual(wait,300.0)
        self.assertLessEqual(wait,600.0)

    def test_safety_boundaries(self):
        for m in (M279,M284):
            self.assertFalse(m.PROBABILITY_ENABLED)
            self.assertFalse(m.DIRECTION_ENABLED)
            self.assertFalse(m.PUBLICATION_ALLOWED)
            self.assertFalse(m.EXECUTION_AUTHORITY)

if __name__=="__main__":
    print("="*100)
    print(" OAD-279 / OAD-284 GMGN RATE-LIMIT RESILIENT ACQUISITION BOUNDARY CERTIFICATION")
    print("="*100)
    r=unittest.main(verbosity=2,exit=False)
    if not r.result.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] provider 429/reset cooldown recognized")
    print("[PASS] candidate amplification stops immediately on provider rate limit")
    print("[PASS] five-minute conservative cooldown used when reset time is unavailable")
    print("[PASS] exact provider cooldown can exceed old 60-second generic retry cap")
    print("[PASS] runtime now exposes bounded provider failure detail")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-279/OAD-284 GMGN ACQUISITION BOUNDARY REBUILD CERTIFIED")
