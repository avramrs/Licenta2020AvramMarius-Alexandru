import time
import random
from zlib import compress, decompress
from utils import *

P_LEN = 64
SECRET_LEN = 16
STORAGE_LEN = 10


class Vss(object):
    def __init__(self, germaine_prime=0, g=0):
        self.p = germaine_prime
        self.q = (self.p - 1) // 2
        if g == 0 and self.p != 0:
            self.g = find_primitive_root(self.p)
        else:
            self.g = g
        self.shares = []
        self.commits = []
        self.c = []

    def commit(self, a):
        return pow(self.g, a, self.p)

    def verify(self, commits, x, share):
        a = 1
        power = 0
        for c in commits:
            xi = pow(x, power, self.p)
            a = mul_mod(a, pow(c, xi, self.p), self.p)
            power += 1
        s_commit = self.commit(share)
        # print(s_commit)
        # print(a)
        return a == s_commit

    def split(self, x, share_nr):
        out = Vss()
        f = gen_polynomial((share_nr // 2) + 1, self.q)
        for i in range(share_nr):
            out.shares.append(calc_poly(f, i + 1, self.q))
        for i, coef in enumerate(f, 1):
            out.commits.append(self.commit(coef))
        c = f[0].to_bytes(f[0].bit_length() // 8 + 1, "big")
        h = get_sha256(c)
        c_data = x.to_bytes(x.bit_length() // 8 + 1, "big")
        c_data_32 = [int.from_bytes(c_data[i:i + 4], "big") for i in range(0, x.bit_length() // 8 + 1, 4)]
        for i in range(len(c_data_32)):
            out.c.append(pow(c_data_32[i], h[i], self.p))
        return out, c_data_32

    def recover(self, x_v, shares, c):
        """x_v = vector de indici a share-urilor"""
        c0 = interpol(x_v, shares, self.p)
        c_b = c0.to_bytes(c0.bit_length() // 8 + 1, "big")
        h = get_sha256(c_b)
        secret = []
        for i in range(len(c)):
            secret.append(pow(c[i], h[i], self.p))
        data_l = [s.to_bytes(s.bit_length() // 8 + 1, "big").lstrip(b"\x00") for s in secret]
        data = b"".join(data_l)
        plain = int.from_bytes(data, "big")
        return plain,data_l
