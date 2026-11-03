# Spike only, not a verifier: tests the proposed bound against exact rational arithmetic on the sequential f32 program.
import numpy as np, random, math
from fractions import Fraction as F
u=F(1,2**24); eta=F(1,2**150)
def gamma(n): return n*u/(1-n*u)
def f16(bits):
    s=-1.0 if bits&0x8000 else 1.0; e=(bits>>10)&31; m=bits&1023
    assert e!=31
    return s*(m*2.0**-24 if e==0 else (1024+m)*2.0**(e-25))
def row(rng,k,mode):
    ds=[];qs=[];xs=[]
    for b in range(k//32):
        if mode=='subnormal_d': bits=int(rng.choice([1,2,3,0x3ff,0x8001,0x83ff]))
        elif mode=='underflow': bits=int(rng.choice([1,3,7]))
        else: bits=int(rng.integers(0,0x7c00))|int(rng.choice([0,0x8000]))
        ds.append(bits)
        qs.append(rng.integers(-127,128,32))
        if mode=='normal': x=rng.normal(0,1,32)
        elif mode=='subnormal_d': x=rng.normal(0,1,32)
        elif mode=='underflow': x=rng.normal(0,1,32)*2.0**-120
        elif mode=='wide': x=rng.normal(0,1,32)*2.0**rng.integers(-40,40,32)
        elif mode=='cancel': x=rng.normal(0,1,32)
        xs.append(x.astype(np.float32))
    return ds,qs,xs
def run(ds,qs,xs,cancel=False):
    acc=np.float32(0); exact=F(0); mag=F(0); inexact_prod=0; nterm=0
    for b,(bits,q,x) in enumerate(zip(ds,qs,xs)):
        d=np.float32(f16(bits))
        for j in range(32):
            qd=np.float32(int(q[j]))*d
            assert F(float(qd))==F(int(q[j]))*F(float(d)), 'q*d inexact'
            acc=np.float32(acc+qd*x[j])
            t=F(int(q[j]))*F(float(d))*F(float(x[j])); exact+=t; mag+=abs(t); nterm+=1
    return float(acc),exact,mag,nterm
rng=np.random.default_rng(7); out={}
for k in (32,1024,3072):
  for mode in ('normal','subnormal_d','underflow','wide','cancel'):
    worst=0.0; n=4 if k==3072 else 12
    for _ in range(n):
        ds,qs,xs=row(rng,k,mode)
        if mode=='cancel':  # second half is exact negation of first: true answer 0
            h=len(ds)//2
            if h:
                ds[h:]=ds[:h]; qs[h:]=[-q for q in qs[:h]]; xs[h:]=xs[:h]
        y,ex,mag,nt=run(ds,qs,xs)
        if not math.isfinite(y): raise SystemExit('nonfinite')
        err=abs(F(y)-ex); bound=gamma(nt)*mag+nt*eta*(1+gamma(nt))
        assert err<=bound,(k,mode,float(err),float(bound))
        worst=max(worst,float(err/bound) if bound else 0)
    print(f"k={k:5d} {mode:12s} worst err/bound={worst:.2e}")
print('bound held on all')
