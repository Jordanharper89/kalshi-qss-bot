const {Connection,PublicKey,TransactionMessage,
VersionedTransaction}=require("@solana/web3.js");
const {AccountLayout}=require("@solana/spl-token");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm");
const DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const MET=new PublicKey("4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const INPUT=new BN("10000000"),SLIP=new BN("100");
const c=new Connection(RPC,"confirmed");

function ixs(x){
 if(!x)return[];
 if(Array.isArray(x))return x.flatMap(ixs);
 if(x.instructions)return x.instructions;
 if(x.transaction?.instructions)return x.transaction.instructions;
 if(x.programId&&x.keys)return[x];
 return[];
}
function amt(acct){
 if(!acct)return null;
 const raw=Buffer.from(acct.data[0],"base64");
 return BigInt(AccountLayout.decode(raw.subarray(0,165)).amount.toString());
}

(async()=>{
 console.log("[MTR-080] START");
 console.log("[SCOPE] corrected Meteora Y->X quote + protected simulation");

 const m=await DLMM.create(c,MET);
 const X=m.tokenX.mint.address,Y=m.tokenY.mint.address;

 console.log(`[TOKEN_X] ${X.toBase58()}`);
 console.log(`[TOKEN_Y] ${Y.toBase58()}`);
 console.log(`[INPUT_MINT] ${W.toBase58()}`);

 if(!W.equals(Y))throw Error("EXPECTED_WSOL_AS_TOKEN_Y");

 const WRONG=true;
 const CORRECT=false;

 const wrongBins=await m.getBinArrayForSwap(WRONG);
 const rightBins=await m.getBinArrayForSwap(CORRECT);

 const qWrong=m.swapQuote(INPUT,WRONG,SLIP,wrongBins);
 const qRight=m.swapQuote(INPUT,CORRECT,SLIP,rightBins);

 console.log(`[WRONG_X_TO_Y] out=${qWrong.outAmount} min=${qWrong.minOutAmount}`);
 console.log(`[CORRECT_Y_TO_X] out=${qRight.outAmount} min=${qRight.minOutAmount}`);
 console.log(`[CORRECT_FEE] ${qRight.fee}`);
 console.log(`[CORRECT_PROTOCOL_FEE] ${qRight.protocolFee}`);
 console.log(`[CORRECT_ARRAYS] ${qRight.binArraysPubkey.map(x=>x.toBase58()).join(",")}`);

 const built=await m.swap({
  inToken:Y,
  outToken:X,
  inAmount:INPUT,
  minOutAmount:qRight.minOutAmount,
  lbPair:MET,
  user:USER,
  binArraysPubkey:qRight.binArraysPubkey
 });

 const all=ixs(built);
 console.log(`[INSTRUCTIONS] ${all.length}`);

 const bh=await c.getLatestBlockhash("confirmed");
 const msg=new TransactionMessage({
  payerKey:USER,
  recentBlockhash:bh.blockhash,
  instructions:all
 }).compileToV0Message();

 const tx=new VersionedTransaction(msg);
 const reserveX=m.lbPair.reserveX;

 const pre=BigInt((await c.getTokenAccountBalance(reserveX)).value.amount);

 const sim=await c.simulateTransaction(tx,{
  sigVerify:false,
  replaceRecentBlockhash:true,
  commitment:"confirmed",
  accounts:{encoding:"base64",addresses:[reserveX.toBase58()]}
 });

 console.log(`[SIM_ERR] ${JSON.stringify(sim.value.err)}`);
 console.log(`[SIM_UNITS] ${sim.value.unitsConsumed??"null"}`);

 const post=amt(sim.value.accounts?.[0]);
 console.log(`[RESERVE_X_PRE] ${pre}`);
 console.log(`[RESERVE_X_POST] ${post}`);
 if(post!==null){
  const delta=pre-post;
  console.log(`[PHYSICAL_X_OUT] ${delta}`);
  console.log(`[QUOTE_MINUS_PHYSICAL] ${BigInt(qRight.outAmount.toString())-delta}`);
  console.log(`[MIN_MET] ${delta>=BigInt(qRight.minOutAmount.toString())}`);
 }

 if(sim.value.err)
  console.log("[RESULT] CORRECT_DIRECTION_PROTECTED_SIMULATION_FAIL");
 else
  console.log("[RESULT] CORRECT_DIRECTION_PROTECTED_SIMULATION_PASS");

 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-080] COMPLETE");
})().catch(e=>{
 console.error("[MTR-080] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
