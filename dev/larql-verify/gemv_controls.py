import json,os,sys,hashlib
from fractions import Fraction as F
sys.path.insert(0,os.getcwd())
import numpy as np
from refcheck import gemv
W=os.environ['TMPDIR']+'/gemvw/w'; m=json.load(open(W+'/witness.json')); R={r['tensor']:r for r in m['records']}
rd=lambda s:open(os.path.join(W,s['file']),'rb').read()
def load(t):
    r=R[t]; return r['rows'],r['columns'],bytearray(rd(r['blocks'])),np.frombuffer(rd(r['x']),dtype='<u4').copy(),np.frombuffer(rd(r['y']),dtype='<u4').copy()
def show(name,b,x,y,n,k):
    s=gemv.check_seq(bytes(b),x,y,n,k); o=gemv.check_b1(bytes(b),x,y,n,k)
    print(f"{name:44s} SEQ {s.status:10s} viol {s.rows_violating:5d} | B1 {o.status:10s} viol {o.rows_violating:5d} worst {float(o.worst_ratio):.3e}",flush=True)
T='0.self_attn.q_proj.weight'
n,k,b,x,y=load(T); print(T,n,k)
show('unchanged',b,x,y,n,k)
y2=y.copy(); y2[5]^=1; show('lowest bit of one y',b,x,y2,n,k)
y2=y.copy(); y2[5]^=0x80000000; show('sign of one y',b,x,y2,n,k)
b2=bytearray(b); blk=34*(k//32)*7+34*3; b2[blk+2+9]=(b2[blk+2+9]+40)&255; show('one code changed, in the blocks',b2,x,y,n,k)
b2=bytearray(b); b2[34*(k//32)*7+1]^=0x04; show('one scale exponent bit changed',b2,x,y,n,k)
# one swapped pair of adjacent rows in y
y2=y.copy(); y2[[10,11]]=y2[[11,10]]; show('two rows of y swapped',b,x,y2,n,k)
# wrong tensor's output
n2,k2,b3,x3,y3=load('0.self_attn.k_proj.weight'); show("another operator's y",b,x,y3,n,k) if (n2,k2)==(n,k) else None
# different programs on real data, computed here
w=gemv.q8_0.dequantize_q8_0_rows(bytes(b),n,k); xs=x.view(np.float32)
acc=np.zeros(n,dtype=np.float32)
for j in reversed(range(k)): acc=acc+(w[:,j]*xs[j])
show('reverse-order sum of the same inputs',b,x,acc.view(np.uint32),n,k)
acc=(w.astype(np.float64)@xs.astype(np.float64)).astype(np.float32); show('binary64 accumulate, rounded at the end',b,x,acc.view(np.uint32),n,k)
# independent recomputation of worst row, not using refcheck
def f16(h):
    s=-1 if h&0x8000 else 1; e=(h>>10)&31; f=h&1023; assert e!=31
    return s*(F(f,2**24) if e==0 else F(1024+f,1024)*F(2)**(e-15))
def f32(u):
    s=-1 if u>>31 else 1; e=(u>>23)&255; f=u&0x7fffff; assert e!=255
    return s*(F(f)*F(2)**-149 if e==0 else F(0x800000+f)*F(2)**(e-150))
res=json.load(open('results.json'))['results']
for t in sorted(res,key=lambda r:-float(r['worst_ratio']))[:2]:
    n,k,b,x,y=load(t['tensor']); i=t['worst_row']; base=i*(k//32)*34; ex=S=F(0)
    X=[f32(int(v)) for v in x]
    for bl in range(k//32):
        o=base+bl*34; d=f16(b[o]|b[o+1]<<8)
        for j in range(32):
            q=b[o+2+j]; q=q-256 if q>127 else q; p=q*d*X[bl*32+j]; ex+=p; S+=abs(p)
    g=F(k,2**24-k); B=g*S+k*F(1,2**150)*(1+g); ratio=abs(f32(int(y[i]))-ex)/B
    print(t['tensor'],'row',i,'recomputed',f"{float(ratio):.14f}",'reference',t['worst_ratio'][:16], 'y*',f"{float(ex):.6g}",'S',f"{float(S):.6g}")
