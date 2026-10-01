# Verification suite for QSB-005
from qseries_v2.solana_money_runner_v5 import SolanaMoneyEngineV5

def run_tests():
    engine = SolanaMoneyEngineV5()
    
    # 1. Unverified Decimal Guard Check
    res1 = engine.evaluate_live_market({"is_live_feed": True, "decimals_verified": False})
    assert res1["reason"] == "PRICE_ORIENTATION_UNPROVEN"
    
    # 2. No Quote Guard Check
    res2 = engine.evaluate_live_market({"is_live_feed": True, "decimals_verified": True, "executable_quote": None})
    assert res2["reason"] == "NO_EXECUTABLE_QUOTE"
    
    # 3. Dynamic Friction Check
    f = engine.calculate_venue_friction("PUMP_SWAP", 100.0)
    assert f["total_friction"] > 2.0  # Fees + Slippage + Gas

    print("ALL PHYSICAL MECHANICS CHECKS PASSED FOR QSB-005.")

if __name__ == "__main__":
    run_tests()
