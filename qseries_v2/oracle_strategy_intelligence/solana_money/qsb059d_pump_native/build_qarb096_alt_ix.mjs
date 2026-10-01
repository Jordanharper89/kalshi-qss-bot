import fs from "node:fs";
import {
    PublicKey,
    AddressLookupTableProgram
} from "@solana/web3.js";

const req=JSON.parse(
    fs.readFileSync(0,"utf8")
);

const authority=
    new PublicKey(req.user);

const recentSlot=
    Number(req.recentSlot);

const addresses=
    (req.addresses ?? [])
    .map(x=>new PublicKey(x));

function enc(ix){
    return {
        programId:
            ix.programId.toBase58(),

        accounts:
            ix.keys.map(k=>({
                pubkey:
                    k.pubkey.toBase58(),

                isSigner:
                    !!k.isSigner,

                isWritable:
                    !!k.isWritable
            })),

        data:
            Buffer.from(
                ix.data
            ).toString("base64")
    };
}

try{
    if(
        addresses.length<4
        || addresses.length>8
    ){
        throw new Error(
            "ALT_ADDRESS_COUNT:"
            +addresses.length
        );
    }

    const [
        createIx,
        lookupTable
    ]=
        AddressLookupTableProgram
        .createLookupTable({
            authority,
            payer:authority,
            recentSlot
        });

    const extendIx=
        AddressLookupTableProgram
        .extendLookupTable({
            payer:authority,
            authority,
            lookupTable,
            addresses
        });

    console.log(
        JSON.stringify({
            ok:true,

            lookupTable:
                lookupTable.toBase58(),

            recentSlot,

            addresses:
                addresses.map(
                    x=>x.toBase58()
                ),

            instructions:[
                enc(createIx),
                enc(extendIx)
            ]
        })
    );

}catch(e){
    console.log(
        JSON.stringify({
            ok:false,
            reason:
                e?.stack
                ??e?.message
                ??String(e)
        })
    );
}
