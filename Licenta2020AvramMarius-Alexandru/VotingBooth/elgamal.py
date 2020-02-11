import sys
import zlib
from utils import *
import hashlib


class PrivateKey(object):
    def __init__(self, p: int = None, g: int = None, x=None):
        self.p = p
        self.g = g
        self.x = x
        self.bit_len = p.bit_length()


class PublicKey(object):
    def __init__(self, p: int = None, g: int = None, h=None):
        self.p = p
        self.g = g
        self.h = h
        self.bit_len = p.bit_length()


def encode(m):
    m_b = bytes(m, "utf-8")
    m_c = zlib.compress(m_b, level=6)
    m_e = int.from_bytes(m_c, byteorder="big")
    return m_e


def decode(m_p):
    m_c = m_p.to_bytes((m_p.bit_length() // 8) + 1, byteorder="big")
    m = zlib.decompress(m_c)
    m_s = m.decode("utf-8", "replace")
    return m_s


def generate_keys(bit_len=256, iConfidence=32):
    p = find_prime(bit_len, iConfidence)
    g = find_primitive_root(p)
    g = pow(g, 2, p)
    x = random.randint(2, (p - 1) // 2)
    h = pow(g, x, p)

    public_key = PublicKey(p, g, h)
    private_key = PrivateKey(p, g, x)

    return {'privateKey': private_key, 'publicKey': public_key}


def get_keys(p, g):
    if MR(p, 32) is False:
        raise AssertionError("Number not prime.")
    x = random.randint(2, (p - 1) // 2)
    h = pow(g, x, p)

    public_key = PublicKey(p, g, h)
    private_key = PrivateKey(p, g, x)

    return {'privateKey': private_key, 'publicKey': public_key}

from math import sqrt
def encrypt(key, sPlaintext):
    z = encode(sPlaintext)
    if z > key.p:
        raise ArithmeticError("Message too long")
    y = random.randint(2, (key.p - 1) // 2)
    c = pow(key.g, y, key.p)
    d = z * pow(key.h, y, key.p) % key.p
    return c, d

def decrypt(key, c1, c2):
    s = pow(c1, key.x, key.p)
    s_inv = mod_inv(s, key.p)
    m_enc = c2 * s_inv % key.p
    # m_enc = tonelli_shanks(m_enc, key.p)
    # m_enc = key.p - pow(m_enc, (key.p + 1) // 4, key.p)
    try:
        m = decode(m_enc)
    except:
        m_enc = key.p - m_enc
        m = decode(m_enc)
    return m


def get_hash_int(message):
    h = hashlib.new("sha256")
    h.update(message.encode())
    h = h.digest()
    h_int = int.from_bytes(h, byteorder="big")
    return h_int


def sign(priv_key, message):
    k = random.randint(2, priv_key.p - 2)
    while gcd(k, priv_key.p - 1) != 1:
        k = random.randint(2, priv_key.p - 2)
    r = pow(priv_key.g, k, priv_key.p)
    h_int = get_hash_int(message)
    k_inv = mod_inv(k, priv_key.p - 1)
    xr = mul_mod(priv_key.x, r, priv_key.p - 1)
    s = (h_int - xr) % (priv_key.p - 1)
    s = mul_mod(s, k_inv, priv_key.p - 1)
    if s == 0:
        r, s = sign(priv_key, message)
    return r, s


def get_rand_exponent(p):
    u = random.randint(2, (p - 1) // 2)
    return u


def reencrypt(key, c1, c2, u):
    c1 = c1 * pow(key.g, u, key.p) % key.p
    c2 = c2 * pow(key.h, u, key.p) % key.p
    return c1, c2


def test():
    assert (sys.version_info >= (3, 4))
    print("Generating keys...")
    keys = generate_keys()
    print("Done.")
    pv = keys['privateKey']
    pb = keys['publicKey']
    message = "Hello"
    print("Encrypting message...")
    c1, c2 = encrypt(pb, message)
    print("c1,c2:{c1},{c2}".format(c1=c1, c2=c2))
    print("Reencrypting message...")
    r = get_rand_exponent(pb.p)
    c1, c2 = reencrypt(pb, c1, c2, r)
    print("c1,c2:{c1},{c2}".format(c1=c1, c2=c2))
    print("Decrypting message...")
    plain = decrypt(pv, c1, c2)
    print("Plaintext:{s}".format(s=plain))
    print("Decrypted text:{s}".format(s=message))
    return message == plain
