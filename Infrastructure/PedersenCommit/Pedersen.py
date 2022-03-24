#From https://github.com/lorenzogentile404/pedersen-commitment

from modules.Crypto.Util import number
from modules.Crypto.Random import random
from modules.Crypto import Random
import sys

class Pedersen:
    def __init__(self, security):
        self.v = verifier()
        self.p = prover()
        
        self.security = security
        
        self.param = self.v.setup(self.security)

class verifier:
    def setup(self, security):
        # Pick p, q primes such that p | q - 1, that is equvalent to
        # say that q = r*p + 1 for some r
        p = number.getPrime(security, Random.new().read)
        # print("p = ",p)
        
        r = 1
        while True:
            q = r*p + 1
            if number.isPrime(q):
                # print("q = ",q)
                break
            r += 1
        
        # Compute elements of G = {i^r mod q | i in Z_q*}
        G = [] 
        for i in range(1, q): # Z_q*
            G.append(i**r % q)

        G = list(set(G))
        # print("Order of G = {i^r mod q | i in Z_q*} is " + str(len(G)) + " (must be equal to p).")
        
        # Since the order of G is prime, any element of G except 1 is a generator
        g = random.choice(list(filter(lambda e: e != 1, G)))
        # print("g = ",g)
                
        h = random.choice(list(filter(lambda e: e != 1 and e != g, G)))
        # print("h = ",h)
        
        # g and h are elements of G such that nobody knows math.log(h, g) (log of h base g)
           
        return q,g,h

    def open(self, param, c, m, *r):
        q, g, h = param

        rSum = 0
        for rEl in r:
            rSum += rEl
       
        return c == (pow(g,m,q) * pow(h,rSum,q)) % q  

    def add(self, param, *c):
        q = param[0]
        
        cSum = 1
        for cEl in c:
            cSum *= cEl
        return cSum % q
        
class prover: 
    def commit(self, param, m):
        q, g, h = param
        
        r = number.getRandomRange(1, q-1)
        c = (pow(g,m,q) * pow(h,r,q)) % q
        return c, r