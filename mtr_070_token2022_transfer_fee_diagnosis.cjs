const {Connection,PublicKey}=require("@solana/web3.js");

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const MINT=new PublicKey("9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump");
const TOKEN2022="TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb";
const QUOTED=12286248n;
const PHYSICAL=8122902n;
const c=new Connection(RPC,"confirmed");

(async()=>{
 console.log("[MTR-070] START");
 console.log("[SCOPE] Token-2022 mint extension diagnosis; read-only");

 const ai=await c.getAccountInfo(MINT,"confirmed");
 if(!ai)throw Error("MINT_NOT_FOUND");

 console.log(`[MINT] ${MINT.toBase58()}`);
 console.log(`[OWNER] ${ai.owner.toBase58()}`);
 console.log(`[DATA_LEN] ${ai.data.length}`);
 console.log(`[TOKEN2022] ${ai.owner.toBase58()===TOKEN2022}`);

 const r=await c._rpcRequest("getAccountInfo",[
  MINT.toBase58(),
  {encoding:"jsonParsed",commitment:"confirmed"}
 ]);
 if(r.error)throw Error(JSON.stringify(r.error));

 const parsed=r.result?.value?.data?.parsed;
 if(!parsed)throw Error("NO_JSON_PARSED_MINT");

 const info=parsed.info||{};
 console.log(`[DECIMALS] ${info.decimals}`);
 console.log(`[SUPPLY] ${info.supply}`);
 console.log(`[MINT_AUTHORITY] ${info.mintAuthority}`);
 console.log(`[FREEZE_AUTHORITY] ${info.freezeAuthority}`);

 const exts=info.extensions||[];
 console.log(`[EXTENSION_COUNT] ${exts.length}`);

 for(let i=0;i<exts.length;i++){
  const e=exts[i];
  console.log(`[EXTENSION_${i}] ${JSON.stringify(e)}`);
 }

 console.log(`[SDK_QUOTED_RAW] ${QUOTED}`);
 console.log(`[PHYSICAL_RECEIVED_RAW] ${PHYSICAL}`);

 const loss=QUOTED-PHYSICAL;
 const lossBps=loss*10000n/QUOTED;
 console.log(`[OBSERVED_LOSS_RAW] ${loss}`);
 console.log(`[OBSERVED_LOSS_BPS] ${lossBps}`);

 const feeExt=exts.find(e=>
  String(e.extension||e.type||"").toLowerCase().includes("transferfee"));

 if(feeExt){
  console.log(`[TRANSFER_FEE_EXTENSION] ${JSON.stringify(feeExt)}`);
  console.log("[RESULT] TOKEN2022_TRANSFER_FEE_EXTENSION_FOUND");
  console.log("[NEXT_GATE] EXACT_NET_TRANSFERABLE_AMOUNT_REPRICING");
 }else{
  console.log("[TRANSFER_FEE_EXTENSION] NONE");
  console.log("[RESULT] TOKEN2022_TRANSFER_FEE_DOES_NOT_EXPLAIN_OUTPUT_GAP");
  console.log("[NEXT_GATE] METEORA_SWAP2_OUTPUT_SEMANTICS_DIAGNOSIS");
 }

 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-070] COMPLETE");
})().catch(e=>{
 console.error("[MTR-070] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
