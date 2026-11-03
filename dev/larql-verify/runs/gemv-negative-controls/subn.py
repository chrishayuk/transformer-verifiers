import json,os,sys,numpy as np
sys.path.insert(0,os.getcwd())
from refcheck import gemv
N=os.environ['TMPDIR']+'/gemvneg'; W=os.path.expanduser('~/chris-models/gemv-7ac8c9e3/witness'); F=N+'/w-flush_subnormal_scale'
m=json.load(open(W+'/witness.json')); mf=json.load(open(F+'/witness.json'))
tot=ops_sub=rows_sub=rows_v=ops_v=outside=0; pass_with=[]; quiet_rows=0; xdiff=0
for r,rf in zip(m['records'],mf['records']):
    assert r['tensor']==rf['tensor'] and r['blocks']['sha256']==rf['blocks']['sha256']
    xdiff+= r['x']['sha256']!=rf['x']['sha256']
    n,k=r['rows'],r['columns']; raw=open(f"{F}/{rf['blocks']['file']}",'rb').read(); b=np.frombuffer(raw,dtype=np.uint8).reshape(n,k//32,34)
    h=b[:,:,0].astype(np.uint16)|(b[:,:,1].astype(np.uint16)<<8)
    sub=((h&0x7c00)==0)&((h&0x3ff)!=0); srow=sub.any(axis=1)
    x=np.fromfile(f"{F}/{rf['x']['file']}",dtype='<u4'); y=np.fromfile(f"{F}/{rf['y']['file']}",dtype='<u4')
    want=gemv.seq_bits(raw,x,n,k); v=(want!=y)
    tot+=int(sub.sum()); rows_sub+=int(srow.sum()); rows_v+=int(v.sum()); outside+=int((v&~srow).sum()); quiet_rows+=int((srow&~v).sum())
    ops_sub+=int(sub.any()); ops_v+=int(v.any())
    if sub.any() and not v.any(): pass_with.append(r['tensor'])
print(f"blocks with subnormal scale {tot}; operations containing one {ops_sub}/196; rows containing one {rows_sub}")
print(f"operations SEQ flagged {ops_v}; rows SEQ flagged {rows_v}; flagged rows with NO subnormal scale {outside}")
print(f"rows with a subnormal scale SEQ did not flag {quiet_rows}; operations with one that SEQ passed {pass_with[:6]} ({len(pass_with)})")
print(f"operations whose x differed from the clean run {xdiff}/196")
