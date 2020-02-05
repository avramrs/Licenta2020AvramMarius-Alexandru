import random
import hashlib
import time


def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a


def mul_mod(a, b, p):
    return (a * b) % p


def mod_inv(a, m):
    m0 = m
    y = 0
    x = 1
    if m == 1:
        return 0
    while a > 1:
        q = a // m
        t = m
        m = a % m
        a = t
        t = y
        y = x - q * y
        x = t
    if x < 0:
        x = x + m0
    return x


def SS(p, confidence):
    '''Solovay-Strassen'''
    for i in range(confidence):
        a = random.randint(2, p - 1)
        if gcd(a, p) > 1:
            return False
        if not jacobi(a, p) % p == pow(a, (p - 1) // 2, p):
            return False
    return True


def MR(p, confidence):
    """Miller Rabin"""
    d = p - 1
    r = 0
    while d % 2 == 0:
        r += 1
        d //= 2
    for _ in range(confidence):
        a = random.randint(2, p - 2)
        x = pow(a, d, p)
        if x == 1 or x == p - 1:
            continue
        for i in range(r - 1):
            x = pow(x, 2, p)
            if x == p - 1:
                continue
        return False
    return True


def jacobi(k, n):
    if k < 0 or k % 2 == 1:
        return 0
    n = n % k
    t = 1
    while n != 0:
        while n % 2 == 0:
            n //= 2
            r = k % 8
            if r == 3 or r == 8:
                t = -t
        n, k = k, n
        if n % 4 == 3 and n % 4 == 3:
            t = -t
        n = n % k
    if k == 1:
        return t
    else:
        return 0


def tonelli_shanks(a, p):
    q = p - 1
    s = 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = random.randint(1, p - 1)
    while jacobi(z, p) == 1:
        z = random.randint(1, p - 1)
    m = s
    c = pow(z, q, p)
    t = pow(a, q, p)
    r = pow(a, (q + 1) // 2, p)
    while 1:
        if t == 0:
            return 0
        if t == 1:
            return r
        i = 0
        while t != 1:
            t = pow(t, 2, p)
            i += 1
        b = pow(c, pow(2, m - i - 1, (p - 1) // 2))
        m = i
        c = pow(b, 2, p)
        t = t * c % p
        r = r * b


def find_primitive_root(p):
    p1 = 2
    p2 = (p - 1) // 2
    while 1:
        g = random.randint(2, p - 1)
        if not pow(g, p1, p) == 1:
            if not pow(g, p2, p) == 1:
                return g


def find_prime(bit_len, iConfidence):
    """Germaine Prime"""
    found = False
    while found is False:
        q = random.randint(2 ** (bit_len - 2), 2 ** (bit_len - 1))
        if q % 2 == 0:
            q += 1
        while MR(q, iConfidence) is False:
            q = random.randint(2 ** (bit_len - 2), 2 ** (bit_len - 1))
            if q % 2 == 0:
                q += 1
        p = q * 2 + 1
        if MR(p, iConfidence):
            found = True
    return p


def gen_polynomial(degree, p):
    return [random.randint(0, p - 1) for _ in range(degree + 1)]


def calc_poly(pol, x, p):
    power = 0
    res = 0
    for coef in pol:
        xi = pow(x, power, p)
        res += mul_mod(coef, xi, p)
        power += 1
    return res % p


def get_sha256(bytes):
    h = hashlib.sha256()
    h.update(bytes)
    return h.digest()


def interpol(x_v, shares, p):
    s = 0
    for i in range(len(shares)):
        prod = 1
        prod2 = 1
        for j in range(len(x_v)):
            if i != j:
                prod *= x_v[j]
                prod2 = x_v[j] - x_v[i]
        fract = mul_mod(mod_inv(prod2, p), prod, p)
        s += mul_mod(shares[i], fract, p)
    return s


def timer(func, *params):
    start = time.time()
    for p in zip(*params):
        func(*p)
    stop = time.time()
    return stop - start


def get_timestamp():
    return time.asctime(time.gmtime())


def gen_rand_list(el_size, l_size):
    return [random.randint(2 ** el_size, 2 ** el_size) for i in range(l_size)]
