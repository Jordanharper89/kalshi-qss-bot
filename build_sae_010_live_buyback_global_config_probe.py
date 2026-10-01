from pathlib import Path
import subprocess

ROOT=Path.cwd()
B=(
    ROOT/"qseries_v2"/"oracle_strategy_intelligence"/
    "solana_money"/"qsb059d_pump_native"
)

MJS=B/"sae010_live_buyback_global_config_probe.mjs"
TEST=ROOT/"test_sae_010_live_buyback_global_config_probe.py"

MJS.write_text(r'''
import {Connection} from "@solana/web3.js";
import {
  OnlinePumpAmmSdk,
  GLOBAL_CONFIG_PDA
} from "@pump-fun/pump-swap-sdk";

const rpc=process.env.SOLANA_RPC_URL ||
  "https://api.mainnet-beta.solana.com";

const sdk=new OnlinePumpAmmSdk(
  new Connection(rpc,"confirmed")
);

if (
  !sdk.program ||
  !sdk.program.account ||
  !sdk.program.account.globalConfig ||
  !sdk.program.account.globalConfig.fetch
) {
  throw new Error("GLOBAL_CONFIG_FETCH_INTERFACE_MISSING");
}

const gc=await sdk.program.account.globalConfig.fetch(
  GLOBAL_CONFIG_PDA
);

const raw=
  gc.buybackFeeRecipients ||
  gc.buyback_fee_recipients ||
  [];

const recipients=raw.map(
  x=>x?.toBase58 ? x.toBase58() : String(x)
);

console.log(
  "[SAE010_GLOBAL_CONFIG]",
  GLOBAL_CONFIG_PDA.toBase58()
);

console.log(
  "[SAE010_BUYBACK_COUNT]",
  recipients.length
);

recipients.forEach((x,i)=>{
  console.log(
    `[SAE010_BUYBACK] index=${i} pubkey=${x}`
  );
});

if (recipients.length!==8) {
  throw new Error(
    "EXPECTED_8_BUYBACK_RECIPIENTS_GOT_"+recipients.length
  );
}

console.log("[PASS] SAE-010 live buyback GlobalConfig truth");
'''.lstrip(),encoding="utf-8")

TEST.write_text(r'''
from pathlib import Path
import unittest

class T(unittest.TestCase):

    def test_probe_installed(self):
        p=Path(
            "qseries_v2/oracle_strategy_intelligence/"
            "solana_money/qsb059d_pump_native/"
            "sae010_live_buyback_global_config_probe.mjs"
        )
        self.assertTrue(p.is_file())
        s=p.read_text(encoding="utf-8")
        self.assertIn("GLOBAL_CONFIG_PDA",s)
        self.assertIn("SAE010_BUYBACK",s)
        self.assertIn("EXPECTED_8_BUYBACK_RECIPIENTS",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
'''.lstrip(),encoding="utf-8")

print("[PASS] SAE-010 live Pump GlobalConfig probe installed")
print("[TARGET] current on-chain buybackFeeRecipients[8]")
print("[RUNTIME] unchanged")
print("[BROADCAST] disabled")