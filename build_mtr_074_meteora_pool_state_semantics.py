from pathlib import Path

target=Path("mtr_074_meteora_pool_state_semantics.cjs")
target.write_text(r'''const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm");
const DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const MET=new PublicKey("4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const INPUT=new BN("10000000");
const PHYSICAL=new BN("8106656");
const c=new Connection(RPC,"confirmed");

function show(v){
 if(v===null||v===undefined)return String(v);
 if(BN.isBN(v))return v.toString();
 if(v instanceof PublicKey)return v.toBase58();
 if(typeof v==="bigint")return v.toString();
 if(Buffer.isBuffer(v))return v.toString("hex");
 if(Array.isArray(v))return "["+v.map(show).join(",")+"]";
 if(typeof v==="object"){
  const o={};
  for(const [k,x] of Object.entries(v)){
   if(typeof x!=="function")o[k]=show(x);
  }
  return JSON.stringify(o);
 }
 return String(v);
}

(async()=>{
 console.log("[MTR-074] START");
 console.log("[SCOPE] decoded Meteora state/fee semantics; read-only");

 const m=await DLMM.create(c,MET);
 const x=m.tokenX.mint.address,y=m.tokenY.mint.address;
 const y2x=W.equals(y);
 const bins=await m.getBinArrayForSwap(y2x);
 const q=m.swapQuote(INPUT,y2x,new BN(100),bins);

 console.log(`[PAIR] ${MET.toBase58()}`);
 console.log(`[TOKEN_X] ${x.toBase58()}`);
 console.log(`[TOKEN_Y] ${y.toBase58()}`);
 console.log(`[ACTIVE_ID] ${m.lbPair.activeId}`);
 console.log(`[BIN_STEP] ${m.lbPair.binStep}`);

 for(const [k,v] of Object.entries(m.lbPair)){
  if(typeof v!=="function")
   console.log(`[POOL_STATE] ${k}=${show(v)}`);
 }

 console.log(`[QUOTE_KEYS] ${Object.keys(q).join(",")}`);
 for(const [k,v] of Object.entries(q)){
  if(typeof v!=="function")
   console.log(`[QUOTE_FIELD] ${k}=${show(v)}`);
 }

 const quoted=new BN(q.outAmount.toString());
 const shortfall=quoted.sub(PHYSICAL);
 const ppm=PHYSICAL.mul(new BN(1000000)).div(quoted);
 const lossPpm=shortfall.mul(new BN(1000000)).div(quoted);

 console.log(`[INPUT_RAW] ${INPUT}`);
 console.log(`[QUOTED_RAW] ${quoted}`);
 console.log(`[REFERENCE_PHYSICAL_RAW] ${PHYSICAL}`);
 console.log(`[SHORTFALL_RAW] ${shortfall}`);
 console.log(`[PHYSICAL_PPM] ${ppm}`);
 console.log(`[SHORTFALL_PPM] ${lossPpm}`);

 if(q.fee)console.log(`[QUOTE_FEE_RAW] ${show(q.fee)}`);
 if(q.protocolFee)console.log(`[PROTOCOL_FEE_RAW] ${show(q.protocolFee)}`);

 console.log("[RESULT] METEORA_POOL_AND_QUOTE_SEMANTICS_CAPTURED");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-074] COMPLETE");
})().catch(e=>{
 console.error("[MTR-074] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
''',encoding="utf-8")

print(f"[BUILD] wrote {target}")
print("[BUILD] Meteora pool-state and quote-semantics diagnostic")
print("[SCOPE] read-only; no private key; no signing; no sending")