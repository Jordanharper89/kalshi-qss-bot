const fs=require("fs"),{Connection,PublicKey}=require("@solana/web3.js");
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const c=new Connection(RPC,"confirmed");
const PUMP=new PublicKey("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
const POOL=new PublicKey("12x41vhkRjSzL85qyAez3FrGxgUfJQqwv9FtVksgUb9");
const BASE=new PublicKey("7i7DCiJytzEnbThvCD85gYJsmoBG5XUfqUEAkb3C7XXz");
const QUOTE=new PublicKey("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v");
function all(b,x){let a=[],p=0;while((p=b.indexOf(x,p))>=0){a.push(p);p++}return a}
function pk(b,o){try{return new PublicKey(b.subarray(o,o+32)).toBase58()}catch{return null}}
async function main(){
 console.log("[MTR-042] START");
 console.log("[SCOPE] physical PumpSwap mint-offset resolution; no signing; no sending");
 const a=await c.getAccountInfo(POOL,"confirmed");if(!a)throw Error("ANCHOR_POOL_MISSING");
 if(!a.owner.equals(PUMP))throw Error(`WRONG_OWNER ${a.owner.toBase58()}`);
 const b=Buffer.from(a.data),bo=all(b,BASE.toBuffer()),qo=all(b,QUOTE.toBuffer());
 console.log(`[POOL] ${POOL.toBase58()}`);
 console.log(`[SIZE] ${b.length}`);
 console.log(`[DISCRIMINATOR] ${b.subarray(0,8).toString("hex")}`);
 console.log(`[EXPECTED_BASE] ${BASE.toBase58()}`);
 console.log(`[EXPECTED_QUOTE] ${QUOTE.toBase58()}`);
 console.log(`[BASE_OFFSETS] ${bo.length?bo.join(","):"NONE"}`);
 console.log(`[QUOTE_OFFSETS] ${qo.length?qo.join(","):"NONE"}`);
 if(bo.length!==1||qo.length!==1)throw Error("UNIQUE_PHYSICAL_MINT_OFFSETS_NOT_FOUND");
 const baseOffset=bo[0],quoteOffset=qo[0];
 console.log(`[BASE_OFFSET] ${baseOffset}`);
 console.log(`[QUOTE_OFFSET] ${quoteOffset}`);
 console.log(`[BASE_READBACK] ${pk(b,baseOffset)}`);
 console.log(`[QUOTE_READBACK] ${pk(b,quoteOffset)}`);
 const ok=pk(b,baseOffset)===BASE.toBase58()&&pk(b,quoteOffset)===QUOTE.toBase58();
 const out={schema:"MTR-042",execution_authority:false,signing:false,sending:false,
  pool:POOL.toBase58(),size:b.length,discriminator:b.subarray(0,8).toString("hex"),
  expected_base:BASE.toBase58(),expected_quote:QUOTE.toBase58(),
  base_offset:baseOffset,quote_offset:quoteOffset,physical_readback_verified:ok};
 fs.writeFileSync("mtr_042_mint_offsets.json",JSON.stringify(out,null,2));
 if(!ok)throw Error("PHYSICAL_READBACK_MISMATCH");
 console.log("[RESULT] PUMPSWAP_MINT_OFFSETS_PHYSICALLY_VERIFIED");
 console.log("[NEXT_GATE] FILTERED_REAL_POOL_CROSS_VENUE_INTERSECTION");
 console.log("[OUTPUT] mtr_042_mint_offsets.json");console.log("[MTR-042] COMPLETE");
}
main().catch(e=>{console.error("[MTR-042] FAIL");console.error(e?.stack||e);process.exit(1)});