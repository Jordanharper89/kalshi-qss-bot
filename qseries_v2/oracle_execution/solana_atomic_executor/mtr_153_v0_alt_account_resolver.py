"""MTR-153: offline v0 ALT expansion, no RPC, secrets or execution."""
import hashlib
from types import MappingProxyType
from .mtr_152_native_envelope_inspector import inspect_native, NativeFormatError, _short, _read, _base58

class ALTResolutionError(ValueError):
    pass

def _parse_v0(raw):
    # Re-parse the wire format independently; no trusted lookup claims from input.
    if not isinstance(raw, bytes) or len(raw)>1232:
        raise ALTResolutionError('INVALID_TRANSACTION')
    n,p=_short(raw,0)
    if not 1<=n<=64:
        raise ALTResolutionError('INVALID_SIGNATURE_COUNT')
    _,p=_read(raw,p,64*n)
    if p>=len(raw) or raw[p]!=128:
        raise ALTResolutionError('V0_REQUIRED')
    p+=1
    header,p=_read(raw,p,3)
    k,p=_short(raw,p)
    if k < n or header[0] != n or header[1] > n or header[2] > k-n:
        raise ALTResolutionError('INVALID_MESSAGE_HEADER')
    static=[]
    for _ in range(k):
        key,p=_read(raw,p,32); static.append(_base58(key))
    _,p=_read(raw,p,32)
    count,p=_short(raw,p)
    if not 1<=count<=256:
        raise ALTResolutionError('INVALID_INSTRUCTION_COUNT')
    instructions=[]
    for _ in range(count):
        pi,p=_read(raw,p,1)
        ac,p=_short(raw,p); ai,p=_read(raw,p,ac)
        dl,p=_short(raw,p); data,p=_read(raw,p,dl)
        instructions.append((pi[0],tuple(ai),data))
    count,p=_short(raw,p)
    lookups=[]
    for _ in range(count):
        table,p=_read(raw,p,32)
        wc,p=_short(raw,p); writable,p=_read(raw,p,wc)
        rc,p=_short(raw,p); readonly,p=_read(raw,p,rc)
        lookups.append((_base58(table),tuple(writable),tuple(readonly)))
    if p!=len(raw) or not instructions:
        raise ALTResolutionError('INVALID_MESSAGE_TERMINATION')
    return static,instructions,lookups

def resolve_v0(raw, tables):
    """tables: mapping table pubkey -> immutable 32-byte account address sequence.

    This requires the caller to supply independently validated on-chain ALT state;
    it DOES NOT attest that a supplied table is current or authentic.
    """
    # MTR-152 intentionally rejects program indexes referencing loaded keys.
    # Permit only that specific unresolved-index condition; independently
    # verify all bounds after authoritative lookup expansion below.
    try:
        structural=inspect_native(raw)
        if structural['version']!='v0':
            raise ALTResolutionError('V0_REQUIRED')
    except NativeFormatError as exc:
        if str(exc) != 'UNRESOLVED_PROGRAM_ID':
            raise ALTResolutionError('INVALID_NATIVE_ENVELOPE') from exc
    if not isinstance(tables,dict):
        raise ALTResolutionError('TABLE_PROOF_REQUIRED')
    static,ins,refs=_parse_v0(raw)
    writable=[]; readonly=[]; seen=set()
    for table, wi, ri in refs:
        if table in seen:
            raise ALTResolutionError('DUPLICATE_LOOKUP_TABLE')
        seen.add(table)
        seq=tables.get(table)
        if not isinstance(seq,(tuple,list)) or any(type(a)!=bytes or len(a)!=32 for a in seq):
            raise ALTResolutionError('UNVERIFIED_TABLE_CONTENTS')
        if len(seq)>256 or any(i>=len(seq) for i in wi+ri):
            raise ALTResolutionError('LOOKUP_INDEX_OUT_OF_RANGE')
        if len(set(wi+ri))!=len(wi+ri):
            raise ALTResolutionError('DUPLICATE_LOOKUP_INDEX')
        writable.extend(_base58(seq[i]) for i in wi)
        readonly.extend(_base58(seq[i]) for i in ri)
    keys=static+writable+readonly
    instructions=[]
    for pi,ai,data in ins:
        if pi>=len(keys) or any(i>=len(keys) for i in ai):
            raise ALTResolutionError('INVALID_RESOLVED_INDEX')
        # Program may not be a writable lookup account.
        if len(static)<=pi<len(static)+len(writable):
            raise ALTResolutionError('WRITABLE_PROGRAM_ID')
        instructions.append(MappingProxyType({
            'program_id':keys[pi], 'accounts':tuple(keys[i] for i in ai),
            'data_sha256':hashlib.sha256(data).hexdigest(), 'data_len':len(data)}))
    return MappingProxyType({
        'raw_sha256':hashlib.sha256(raw).hexdigest(),
        'static_keys':len(static),'writable_loaded':len(writable),
        'readonly_loaded':len(readonly), 'lookups':len(refs),
        'instructions':tuple(instructions),
        'alt_authenticity_verified':False,
        'bounds_verified':False,'atomic_two_leg_proven':False,
        'protected_profit_certified':False,'signing_authorized':False,
        'broadcast_authorized':False})

if __name__=='__main__':
    print('[MTR153] V0_ALT_INDEX_RESOLVER_READY')
    print('[ALT_AUTHENTICITY] REQUIRES_TRUSTED_ONCHAIN_PROOF')
    print('[ATOMIC_TWO_LEG_PROOF] FALSE')
    print('[PROTECTED_PROFIT] FALSE')
    print('[SCANNER] FROZEN')
    print('[PRIVATE_KEY] NOT_USED')
    print('[SIGNING] FALSE')
    print('[BROADCAST] FALSE')
