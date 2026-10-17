"""MTR-152: native Solana transaction envelope decoder, read-only.
Structural checks only. No claim of PumpSwap/Meteora protections or profit.
"""
import hashlib
from dataclasses import dataclass

B58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

class NativeFormatError(ValueError):
    pass

def _short(buf, pos):
    value = 0
    for shift in (0, 7, 14):
        if pos >= len(buf):
            raise NativeFormatError('SHORTVEC_TRUNCATED')
        b = buf[pos]; pos += 1
        value |= (b & 127) << shift
        if not b & 128:
            if value > 65535:
                raise NativeFormatError('SHORTVEC_OVERSIZED')
            return value, pos
    raise NativeFormatError('SHORTVEC_INVALID')

def _read(buf, pos, size):
    if size < 0 or pos + size > len(buf):
        raise NativeFormatError('TRUNCATED')
    return buf[pos:pos+size], pos+size

def _base58(raw):
    num = int.from_bytes(raw, 'big')
    out = ''
    while num:
        num, rem = divmod(num, 58)
        out = B58[rem] + out
    zeros = len(raw)-len(raw.lstrip(b'\0'))
    return '1' * zeros + (out or ('' if zeros else '1'))

def inspect_native(raw):
    """Parse legacy/v0 transaction, without importing Solana or reading secrets."""
    if type(raw) is not bytes or not raw or len(raw) > 1232:
        raise NativeFormatError('INVALID_RAW_OR_SIZE')
    pos = 0
    sigs, pos = _short(raw, pos)
    if not 1 <= sigs <= 64:
        raise NativeFormatError('SIGNATURE_COUNT_INVALID')
    _, pos = _read(raw, pos, 64*sigs)
    if pos >= len(raw):
        raise NativeFormatError('MISSING_MESSAGE')
    version = 'legacy'
    if raw[pos] & 128:
        v = raw[pos] & 127; pos += 1
        if v != 0:
            raise NativeFormatError('UNSUPPORTED_VERSION')
        version = 'v0'
    header, pos = _read(raw, pos, 3)
    required, readonly_signed, readonly_unsigned = header
    n, pos = _short(raw, pos)
    if n < required or required != sigs or readonly_signed > required or readonly_unsigned > n-required:
        raise NativeFormatError('INVALID_HEADER')
    keys = []
    for _ in range(n):
        key, pos = _read(raw, pos, 32)
        keys.append(_base58(key))
    _, pos = _read(raw, pos, 32)  # recent blockhash
    count, pos = _short(raw, pos)
    if count > 256:
        raise NativeFormatError('TOO_MANY_INSTRUCTIONS')
    instructions = []
    for _ in range(count):
        program_raw, pos = _read(raw, pos, 1)
        program_index = program_raw[0]
        ac, pos = _short(raw, pos)
        accounts, pos = _read(raw, pos, ac)
        size, pos = _short(raw, pos)
        data, pos = _read(raw, pos, size)
        instructions.append((program_index, list(accounts), data))
    lookup_count = 0
    loaded_count = 0
    if version == 'v0':
        lookup_count, pos = _short(raw, pos)
        for _ in range(lookup_count):
            _, pos = _read(raw, pos, 32)
            wc, pos = _short(raw, pos)
            _, pos = _read(raw, pos, wc)
            rc, pos = _short(raw, pos)
            _, pos = _read(raw, pos, rc)
            loaded_count += wc + rc
    if pos != len(raw):
        raise NativeFormatError('TRAILING_BYTES')
    if not instructions:
        raise NativeFormatError('NO_INSTRUCTIONS')
    programs = []
    for index, accounts, data in instructions:
        if index >= n:
            # ALT may hold program indices; requires independently verified resolution.
            raise NativeFormatError('UNRESOLVED_PROGRAM_ID')
        if any(a >= n+loaded_count for a in accounts):
            raise NativeFormatError('INVALID_ACCOUNT_INDEX')
        programs.append({'program_id': keys[index], 'account_count': len(accounts),
                         'data_len': len(data), 'data_sha256': hashlib.sha256(data).hexdigest()})
    return {'version': version, 'signatures': sigs, 'static_keys': n,
            'lookups': lookup_count, 'loaded_accounts_unresolved': loaded_count,
            'programs': tuple(programs), 'raw_sha256': hashlib.sha256(raw).hexdigest(),
            'structural_valid': True, 'native_protections_verified': False,
            'official_economics_verified': False, 'atomic_two_leg_proven': False,
            'signing_authorized': False, 'broadcast_authorized': False}

if __name__ == '__main__':
    print('[MTR152] NATIVE_TRANSACTION_STRUCTURE_DECODER_READY')
    print('[OFFICIAL_BOUNDS_VERIFIED] FALSE')
    print('[ATOMIC_TWO_LEG_PROOF] FALSE')
    print('[PRODUCTION_CUTOVER] FALSE')
    print('[PRIVATE_KEY] NOT_USED')
    print('[SIGNING] FALSE')
    print('[BROADCAST] FALSE')
