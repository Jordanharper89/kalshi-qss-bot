import {Connection,PublicKey,TransactionMessage,VersionedTransaction} from '@solana/web3.js';
import BN from 'bn.js';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const dlmmPackage=require('@meteora-ag/dlmm');
const DLMM=dlmmPackage.default??dlmmPackage.DLMM??dlmmPackage;
import {PUMP_AMM_SDK,OnlinePumpAmmSdk,sellBaseInput} from '@pump-fun/pump-swap-sdk';
import {createInterface} from 'node:readline';

const PUMP='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA';
const DLMM_PROGRAM='LBUZKhRxPF3XUpBCjp4YzTKgLccwBBzZYRSqNeZerDo';
const WSOL='So11111111111111111111111111111111111111112';
function hold(code){throw new Error(code)}
function pub(s){return new PublicKey(String(s))}
function str(v){return String(v?.toString?.()??'')}
function rawIxs(obj){if(Array.isArray(obj))return obj;
 if(obj?.instructions&&Array.isArray(obj.instructions))return obj.instructions;
 if(obj?.transaction?.instructions)return obj.transaction.instructions;
 if(obj?.instructions?.length)return [...obj.instructions];
 if(obj?.message?.instructions)hold('SDK_TRANSACTION_COMPILED_ALREADY');
 return obj?.instructions??null;}
const ALLOWED=new Set([PUMP,DLMM_PROGRAM,'11111111111111111111111111111111',
 'ComputeBudget111111111111111111111111111111',
 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb',
 'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL']);
async function construct(x){
 if(!process.env.SOLANA_RPC_URL?.startsWith('https://'))hold('HTTPS_RPC_REQUIRED');
 const connection=new Connection(process.env.SOLANA_RPC_URL,{commitment:'processed'});
 const wallet=pub(x.wallet), pumpPool=pub(x.pump_pool), poolKey=pub(x.meteora_pool), mint=pub(x.token);
 if(!Number.isSafeInteger(x.size_lamports)||x.size_lamports<=0)hold('REVERSE_SIZE_NOT_SAFE_POSITIVE');
 if(!Number.isInteger(x.expected_gross_token)||x.expected_gross_token<=0 ||
    !Number.isInteger(x.expected_net_token)||x.expected_net_token<=0)hold('REVERSE_TOKEN_AMOUNTS_INVALID');
 const slotBefore=await connection.getSlot('processed');
 const pool=await DLMM.create(connection,poolKey,{cluster:'mainnet-beta'});
 const xt=str(pool.tokenX?.publicKey??pool.tokenX?.mint?.address);
 const yt=str(pool.tokenY?.publicKey??pool.tokenY?.mint?.address);
 if(!((xt===WSOL && yt===str(mint))||(yt===WSOL && xt===str(mint))))hold('DLMM_MINT_BINDING_MISMATCH');
 const swapForY=xt===WSOL;
 const bins=await pool.getBinArrayForSwap(swapForY,6);
 const quote=pool.swapQuote(new BN(String(x.size_lamports)),swapForY,new BN(0),bins,false);
 const consumed=Number(str(quote.consumedInAmount));
 const quotedOut=Number(str(quote.outAmount));
 if(consumed!==x.size_lamports)hold('DLMM_PARTIAL_FILL_REJECT');
 if(quotedOut!==x.expected_gross_token)hold('DLMM_BANK_QUOTE_PARITY_FAIL');
 const dlmmTx=await pool.swap({inToken:pub(WSOL),outToken:mint,
     inAmount:quote.consumedInAmount,minOutAmount:quote.minOutAmount,
     lbPair:poolKey,user:wallet,binArraysPubkey:quote.binArraysPubkey});
 const dlmmIxs=rawIxs(dlmmTx);
 if(!Array.isArray(dlmmIxs)||!dlmmIxs.length)hold('DLMM_NATIVE_IX_MISSING');
 const online=new OnlinePumpAmmSdk(connection);
 const state=await online.swapSolanaState(pumpPool,wallet);
 if(!state?.pool)hold('PUMP_SDK_STATE_NOT_READY');
 if(str(state.pool.baseMint)!==str(mint) && str(state.baseMint)!==str(mint))hold('PUMP_TOKEN_MISMATCH');
 if(typeof state.pool.protocolFees?.add!=='function' || !BN.isBN(state.pool.creatorFees))
   hold('PUMP_V2_FEE_BUCKETS_UNAVAILABLE');
 const args={baseReserve:new BN(String(x.pump_base_reserve)),quoteReserve:new BN(String(x.pump_quote_reserve)),
 virtualQuoteReserves:state.pool.virtualQuoteReserves,
 feeBucketsTotal:state.pool.protocolFees.add(state.pool.creatorFees),globalConfig:state.globalConfig,
 feeConfig:state.feeConfig,baseMint:state.baseMint,baseMintAccount:state.baseMintAccount,
 coinCreator:state.pool.coinCreator,creator:state.pool.creator,quoteMint:state.pool.quoteMint,
 isMayhemMode:state.pool.isMayhemMode,creatorFeeBps:state.pool.creatorFeeBps};
 const sellQuote=sellBaseInput({...args,base:new BN(String(x.expected_net_token)),slippage:0});
 const expectedMin=Number(str(sellQuote.minQuote));
 if(!Number.isSafeInteger(expectedMin)||expectedMin<x.expected_min_sol_out)hold('PUMP_SDK_MIN_QUOTE_PARITY_FAIL');
 // SDK's user-fee and token program accounts are preserved verbatim.
 const pumpSdk=PUMP_AMM_SDK;
 if(typeof pumpSdk?.sellInstructions!=='function')hold('PUMP_SDK_SELL_METHOD_MISSING');
 const sell=await pumpSdk.sellInstructions(state,new BN(String(x.expected_net_token)),new BN(String(expectedMin)));
 const sellIxs=rawIxs(sell);
 if(!Array.isArray(sellIxs)||!sellIxs.length)hold('PUMP_SDK_SELL_IX_MISSING');
 const preIxs=[...dlmmIxs,...sellIxs];
 if(preIxs.some(ix=>!ALLOWED.has(str(ix.programId))))hold('UNAPPROVED_NATIVE_PROGRAM');
 if(preIxs.some(ix=>['11111111111111111111111111111111',
   'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'].includes(str(ix.programId))))
   hold('SDK_REQUIRES_ACCOUNT_SETUP_OR_SOL_MOVEMENT');

 const legs=preIxs.filter(ix=>str(ix.programId)===PUMP||str(ix.programId)===DLMM_PROGRAM);
 if(legs.length!==2||str(legs[0].programId)!==DLMM_PROGRAM||str(legs[1].programId)!==PUMP)
   hold('REVERSE_ATOMIC_LEG_ORDER_INVALID');
 if(legs.some(ix=>!Array.isArray(ix.keys)||ix.keys.length<12))hold('SDK_REQUIRED_ACCOUNTS_MISSING');
 const dk=new Set(legs[0].keys.map(k=>str(k.pubkey)));
 const pk=new Set(legs[1].keys.map(k=>str(k.pubkey)));
 if(!dk.has(str(poolKey)) || !pk.has(str(pumpPool)) || !dk.has(str(wallet)) || !pk.has(str(wallet)))
   hold('SDK_NATIVE_POOL_WALLET_BINDING_INVALID');
 if(!legs[1].keys.some(k=>k.isSigner && str(k.pubkey)===str(wallet)))
   hold('PUMP_SELL_SIGNER_META_MISSING');
 // Reject a cleanup that closes a transient account before the second leg.
 const nativeIds=preIxs.map(ix=>str(ix.programId));
 const dlmmIndex=nativeIds.indexOf(DLMM_PROGRAM),pumpIndex=nativeIds.indexOf(PUMP);
 if(preIxs.slice(dlmmIndex+1,pumpIndex).some(ix=>ix.programId?.toBase58()==='11111111111111111111111111111111'))
   hold('INTER_LEG_SYSTEM_MUTATION_UNVERIFIED');
 const blockhash=await connection.getLatestBlockhash('processed');
 const lookups=[];
 if(x.alt_address){
   const alt=await connection.getAddressLookupTable(pub(x.alt_address),{commitment:'processed'});
   if(!alt?.value)hold('CANONICAL_ALT_ONCHAIN_MISSING');
   if(alt.value.state.deactivationSlot!==BigInt('18446744073709551615'))hold('CANONICAL_ALT_DEACTIVATED');
   lookups.push(alt.value);
 }
 const message=new TransactionMessage({payerKey:wallet,recentBlockhash:blockhash.blockhash,instructions:preIxs})
   .compileToV0Message(lookups);
 const tx=new VersionedTransaction(message);
 const raw=Buffer.from(tx.serialize());
 if(raw.length>1232)hold('NATIVE_V0_PACKET_TOO_LARGE');
 const slotAfter=await connection.getSlot('processed');
 if(slotBefore!==x.bank_slot||slotAfter!==x.bank_slot)hold('SDK_READBACK_NOT_SINGLE_BANK');
 return {ok:true,version:0,serialized_bytes:raw.length,
   unsigned_transaction_b64:raw.toString('base64'),
   message_b64:Buffer.from(message.serialize()).toString('base64'),
   bank_slot:x.bank_slot,slot_before:slotBefore,slot_after:slotAfter,
   gross_token:quotedOut,net_token:x.expected_net_token,
   meteora_min_out:Number(str(quote.minOutAmount)),pump_min_out:expectedMin,
   legs:['DLMM_BUY','PUMP_SELL'],lookup_count:message.addressTableLookups.length,
   native_legs:2,actual_native_instruction_count:preIxs.length};
}
// Persistent unsigned JSON-lines worker; no wallet key material.
process.stdout.write(JSON.stringify({worker_ready:true})+'\n');
const rl=createInterface({input:process.stdin,crlfDelay:Infinity,terminal:false});
for await(const line of rl){
 try{
   const req=JSON.parse(line);
   const r=await construct(req);
   process.stdout.write(JSON.stringify(r)+'\n');
 }catch(e){
   const reason=String(e?.message||'').match(/^[A-Z][A-Z0-9_]{3,80}$/)?.[0]||'SDK_NATIVE_BUILDER_ERROR';
   process.stdout.write(JSON.stringify({ok:false,reason})+'\n');
 }
}
