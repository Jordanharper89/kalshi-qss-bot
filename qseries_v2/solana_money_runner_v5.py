# QSB-005 Standalone Solana Live Money Runner Engine
import os, sys, json, time, math

class SolanaMoneyEngineV5:
    def __init__(self, state_dir="runtime_state/qseries/solana_money_runner_v5"):
        self.state_dir = state_dir
        os.makedirs(self.state_dir, exist_ok=True)
        self.ledger_file = os.path.join(self.state_dir, "ledger.json")
        self.status_file = os.path.join(self.state_dir, "status.json")
        self.positions_file = os.path.join(self.state_dir, "positions.json")
        self.ledger = self._load_json(self.ledger_file, {
            "trades": [],
            "summary": {
                "count": 0, "wins": 0, "losses": 0, "win_rate": 0.0,
                "gross_pnl_usdc": 0.0, "total_fees_usdc": 0.0,
                "total_slippage_usdc": 0.0, "total_friction_usdc": 0.0,
                "net_pnl_usdc": 0.0, "profitability_proven": False
            }
        })
        self.positions = self._load_json(self.positions_file, {})

    def _load_json(self, path, default):
        if os.path.exists(path):
            try:
                with open(path, "r") as f: return json.load(f)
            except Exception: return default
        return default

    def _save_json(self, path, data):
        with open(path, "w") as f: json.dump(data, f, indent=2)

    def calculate_venue_friction(self, venue, amount_usdc, price_impact=0.005):
        venue_fees = {
            "PUMP_SWAP": 0.010,
            "PUMP_FUN": 0.010,
            "RAYDIUM_V4": 0.0025,
            "RAYDIUM_CPMM": 0.0025,
            "METEORA_DLMM": 0.0030,
            "ORCA": 0.0030
        }
        protocol_fee_rate = venue_fees.get(venue.upper(), 0.005)
        network_gas_fee = 0.005
        protocol_fee = amount_usdc * protocol_fee_rate * 2.0
        slippage_cost = amount_usdc * price_impact * 2.0
        total_friction = protocol_fee + slippage_cost + (network_gas_fee * 2.0)
        return {
            "protocol_fee": round(protocol_fee, 6),
            "slippage": round(slippage_cost, 6),
            "network_fee": round(network_gas_fee * 2.0, 6),
            "total_friction": round(total_friction, 6)
        }

    def evaluate_live_market(self, tick_data):
        if not tick_data.get("is_live_feed", False):
            return {"action": "ABSTAIN", "reason": "NO_REAL_DATA"}

        if not tick_data.get("decimals_verified", False):
            return {"action": "ABSTAIN", "reason": "PRICE_ORIENTATION_UNPROVEN"}

        if not tick_data.get("executable_quote"):
            return {"action": "ABSTAIN", "reason": "NO_EXECUTABLE_QUOTE"}

        return {"action": "EVALUATE_SETUP", "data": tick_data}

if __name__ == "__main__":
    engine = SolanaMoneyEngineV5()
    print("QSB-005 Standalone Engine Loaded.")
