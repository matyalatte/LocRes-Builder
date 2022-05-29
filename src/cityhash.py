#cityhash is used for generating hash of keys in .locres files

#Converted UE4's codes (CityHash.cpp, etc.) to python.
#https://github.com/EpicGames/UnrealEngine

#Bit mask to use uint64 and uint32 on python
MASK_64 = 0xFFFFFFFFFFFFFFFF
MASK_32 = 0xFFFFFFFF

#Some primes between 2^63 and 2^64 for various uses.
k0 = 0xc3a5c85c97cb3127
k1 = 0xb492b66fbe98f273
k2 = 0x9ae16a3b2f90404f

def to_uint(bytes):
    return int.from_bytes(bytes, "little")

#use char* as uint64 pointer
def fetch64(bytes):
    return to_uint(bytes[:8])

#use char* as uint32 pointer
def fetch32(bytes):
    return to_uint(bytes[:4])

def bswap_64(i):
    i &= MASK_64
    b = i.to_bytes(8, byteorder="little")
    return int.from_bytes(b, "big")

def rotate(val, shift):
    val &= MASK_64
    return val if shift == 0 else ((val >> shift) | (val << (64 - shift))) & MASK_64

def shift_mix(val):
    val &= MASK_64
    return (val ^ (val >> 47)) & MASK_64

def hash_len_16(u, v, mul):
    a = ((u ^ v) * mul) & MASK_64
    a ^= (a >> 47)
    b = ((v ^ a) * mul) & MASK_64
    b ^= (b >> 47)
    b *= mul
    return b & MASK_64

def hash_len_16_2(u, v):
    kMul = 0x9ddfea08eb382d69
    return hash_len_16(u, v, kMul)

def hash_len_0to16(bytes):
    length = len(bytes)
    if length >= 8:
        mul = k2 + length * 2
        a = fetch64(bytes) + k2
        b = fetch64(bytes[-8:])
        c = rotate(b, 37) * mul + a
        d = (rotate(a, 25) + b) * mul
        return hash_len_16(c, d, mul)
    if length >= 4:
        mul = k2 + length * 2
        a = fetch32(bytes)
        return hash_len_16(length + (a << 3), fetch32(bytes[-4:]), mul)
    if length > 0:
        a = bytes[0]
        b = bytes[length >> 1]
        c = bytes[:-1]
        y = (a + (b << 8)) & MASK_32
        z = (length + (c << 2)) & MASK_32
        return (shift_mix(y * k2 ^ z * k0) * k2) & MASK_64
    return k2

def hash_len_17to32(bytes):
    length = len(bytes)
    mul = k2 + length * 2
    a = fetch64(bytes) * k1
    b = fetch64(bytes[8:])
    c = fetch64(bytes[-8:]) * mul
    d = fetch64(bytes[-16:]) * k2
    return (hash_len_16(
            rotate(a + b, 43) + rotate(c, 30) + d,
		    a + rotate(b + k2, 18) + c,
            mul)
            ) & MASK_64
    
def hash_len_33to64(bytes):
    length = len(bytes)
    mul = k2 + length * 2
    a = fetch64(bytes) * k2
    b = fetch64(bytes[8:])
    c = fetch64(bytes[-24:])
    d = fetch64(bytes[-32:])
    e = fetch64(bytes[16:]) * k2
    f = fetch64(bytes[24:]) * 9
    g = fetch64(bytes[-8:])
    h = fetch64(bytes[-16:]) * mul
    u = rotate(a + g, 43) + (rotate(b, 30) + c) * 9
    v = ((a + g) ^ d) + f + 1
    w = bswap_64((u + v) * mul) + h
    x = rotate(e + f, 42) + c
    y = (bswap_64((v + w) * mul) + g) * mul
    z = e + f + c
    a = (bswap_64((x + z) * mul + y) + b)
    b = shift_mix((z + a) * mul + d + h) * mul
    return (b + x)  & MASK_64

def weak_hash_len32_with_seeds(bytes, a, b):
	return weak_hash_len32_with_seeds2(
        fetch64(bytes),
		fetch64(bytes[8:]),
		fetch64(bytes[16:]),
		fetch64(bytes[24:]),
		a,
		b)

def weak_hash_len32_with_seeds2(w, x, y, z, a, b):
    a += w
    b = rotate(b + a + z, 21)
    c = a
    a += x
    a += y
    b += rotate(a, 44)
    return (a + z) & MASK_64, (b + c) & MASK_64

def cityhash64(bytes):
    length = len(bytes)
    if length <= 32:
        if length <= 16:
            return hash_len_0to16(bytes)
        else:
            return hash_len_17to32(bytes)
    elif length <= 64:
        return hash_len_33to64(bytes)

    x = fetch64(bytes[-40:])
    y = fetch64(bytes[-16:]) + fetch64(bytes[-56:])
    z = hash_len_16_2(fetch64(bytes[-48:]) + length, fetch64(bytes[-24:]))
    v_lo, v_hi = weak_hash_len32_with_seeds(bytes[-64:], length, z)
    w_lo, w_hi = weak_hash_len32_with_seeds(bytes[-32:], y + k1, x)
    x = x * k1 + fetch64(bytes)
    length = (length - 1) & (~63)
    bytes = bytes[:length]

    while(len(bytes)>0):
        x = rotate(x + y + v_lo + fetch64(bytes[8:]), 37) * k1
        y = rotate(y + v_hi + fetch64(bytes[48:]), 42) * k1
        x ^= w_hi
        y += v_lo + fetch64(bytes[40:])
        z = rotate(z + w_lo, 33) * k1
        v_lo, v_hi = weak_hash_len32_with_seeds(bytes, v_hi * k1, x + w_lo)
        w_lo, w_hi = weak_hash_len32_with_seeds(bytes[32:], z + w_hi, y + fetch64(bytes[16:]))
        z, x = x, z
        bytes = bytes[64:]
    return hash_len_16_2(hash_len_16_2(v_lo, w_lo) + shift_mix(y) * k1 + z,
		hash_len_16_2(v_hi, w_hi) + x)

#cityhash for strings
def string_cityhash(string):
    raw_hash = cityhash64(string.encode('utf-16-le'))
    hash = (raw_hash & MASK_32) + (((raw_hash >>32) & MASK_32) * 23)
    return hash & MASK_32
