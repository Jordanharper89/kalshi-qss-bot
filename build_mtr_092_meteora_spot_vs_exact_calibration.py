from pathlib import Path

p=Path("mtr_092_meteora_spot_vs_exact_calibration.cjs")
p.write_text(r'''const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js");
const D=require("@meteora-ag/dlmm");
const DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const c=new Connection(RPC,"confirmed");

const KNOWN=new PublicKey("4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4");
const ABSURD=new PublicKey("9nnt4FN7s5Gh2ZZmnvPC76XXNr7LL8ss8mPMoYf8mD3R");
const INPUT=new BN("1000000");

function n(v){return Number(v?.toString?.()??v)}

async function probe(label,pair){
 const m=await DLMM.create(c,pair);
 const X=m.tokenX.mint.address,Y=m.tokenY.mint.address;
 const xd=m.tokenX.decimal??m.tokenX.decimals;
 const yd=m.tokenY.decimal??m.tokenY.decimals;

 const active=n(m.lbPair.activeId);
 const step=n(m.lbPair.binStep);
 const raw=Math.pow(1+step/10000,active);

 console.log(`\n[${label}] pair=${pair}`);
 console.log(`[${label}] X=${X} Y=${Y}`);
 console.log(`[${label}] X_DEC=${xd} Y_DEC=${yd}`);
 console.log(`[${label}] ACTIVE_ID=${active} BIN_STEP=${step}`);
 console.log(`[${label}] POW_RAW=${raw}`);

 for(const swapForY of [true,false]){
  try{
   const bins=await m.getBinArrayForSwap(swapForY);
   const q=m.swapQuote(INPUT,swapForY,new BN(0),bins);
   console.log(`[${label}] DIR swapForY=${swapForY} out=${q.outAmount} fee=${q.fee}`);
   const implied=n(q.outAmount)/n(INPUT);
   console.log(`[${label}] DIR swapForY=${swapForY} IMPLIED_RAW_RATIO=${implied}`);
  }catch(e){
   console.log(`[${label}] DIR swapForY=${swapForY} HOLD=${String(e.message||e).slice(0,120)}`);
  }
 }
}

(async()=>{
 console.log("[MTR-092] START");
 console.log("[SCOPE] Meteora spot-vs-exact calibration; read-only");

 await probe("KNOWN",KNOWN);
 await probe("ABSURD",ABSURD);

 console.log("[RESULT] SPOT_VS_EXACT_CALIBRATION_CAPTURED");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-092] COMPLETE");
})().catch(e=>{
 console.error("[MTR-092] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] Meteora spot-vs-exact calibration")
print("[SCOPE] two-pool read-only diagnostic; no signing; no sending")