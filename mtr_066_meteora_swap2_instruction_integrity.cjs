const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm");
const DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const MET=new PublicKey("4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const INPUT=new BN("10000000");
const c=new Connection(RPC,"confirmed");

function ixs(x){
 if(!x)return[];
 if(Array.isArray(x))return x.flatMap(ixs);
 if(x.instructions)return x.instructions;
 if(x.transaction&&x.transaction.instructions)return x.transaction.instructions;
 if(x.programId&&x.keys)return[x];
 return[];
}
function u64(buf,off){
 if(buf.length<off+8)return null;
 return new BN(buf.subarray(off,off+8),"le");
}

(async()=>{
 console.log("[MTR-066] START");
 console.log("[SCOPE] Meteora Swap2 instruction integrity; no signing; no sending");

 const m=await DLMM.create(c,MET);
 const x=m.tokenX.mint.address,y=m.tokenY.mint.address;
 if(!W.equals(x)&&!W.equals(y))throw Error("WSOL_NOT_IN_PAIR");

 const y2x=W.equals(y);
 const bins=await m.getBinArrayForSwap(y2x);
 const q=m.swapQuote(INPUT,y2x,new BN(100),bins);

 console.log(`[PAIR] x=${x.toBase58()} y=${y.toBase58()} wsol_is=${W.equals(x)?"X":"Y"}`);
 console.log(`[QUOTE] input=${INPUT} out=${q.outAmount} min=${q.minOutAmount} fee=${q.fee}`);
 console.log(`[QUOTE_DIRECTION] swapYtoX=${y2x}`);

 const tx=await m.swap({
  inToken:W,outToken:W.equals(x)?y:x,inAmount:INPUT,
  minOutAmount:q.minOutAmount,lbPair:MET,user:USER,
  binArraysPubkey:q.binArraysPubkey
 });

 const all=ixs(tx);
 const swap=all.find(z=>z.programId.toBase58()==="LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo");
 if(!swap)throw Error("SWAP2_INSTRUCTION_NOT_FOUND");

 const data=Buffer.from(swap.data);
 console.log(`[SWAP2_DATA_LEN] ${data.length}`);
 console.log(`[SWAP2_DISCRIMINATOR] ${data.subarray(0,8).toString("hex")}`);
 console.log(`[SWAP2_DATA_HEX] ${data.toString("hex")}`);

 /* Anchor Swap2 begins discriminator + amountIn + minAmountOut. */
 const encodedIn=u64(data,8);
 const encodedMin=u64(data,16);
 console.log(`[DECODE] amount_in=${encodedIn} min_out=${encodedMin}`);
 console.log(`[EXPECT] amount_in=${INPUT} min_out=${q.minOutAmount}`);

 if(!encodedIn||!encodedMin)throw Error("SWAP2_DATA_TOO_SHORT");
 if(!encodedIn.eq(INPUT))throw Error("SWAP2_INPUT_AMOUNT_MISMATCH");
 if(!encodedMin.eq(q.minOutAmount))throw Error("SWAP2_MIN_OUT_MISMATCH");

 console.log(`[INSTRUCTION_KEYS] ${swap.keys.length}`);
 swap.keys.forEach((k,i)=>console.log(
  `[KEY ${i}] ${k.pubkey.toBase58()} signer=${k.isSigner} writable=${k.isWritable}`));

 console.log("[RESULT] SWAP2_ENCODED_AMOUNTS_MATCH_FRESH_QUOTE");
 console.log("[NEXT_GATE] METEORA_FRESHNESS_OR_ACCOUNT_STATE_DIAGNOSIS");
 console.log("[MTR-066] COMPLETE");
})().catch(e=>{
 console.error("[MTR-066] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
