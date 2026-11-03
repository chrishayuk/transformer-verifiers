import json,os,sys,collections
sys.path.insert(0,os.getcwd())
import numpy as np
from refcheck import gemv
N=os.environ['TMPDIR']+'/gemvneg'
for f in sys.argv[1:]:
    W=f'{N}/w-{f}'; m=json.load(open(W+'/witness.json')); rd=lambda s:open(os.path.join(W,s['file']),'rb').read()
    c=collections.Counter(); rows=viol=0; worst=0.0; wt=None
    for r in m['records']:
        n,k=r['rows'],r['columns']; b=rd(r['blocks']); x=np.frombuffer(rd(r['x']),dtype='<u4'); y=np.frombuffer(rd(r['y']),dtype='<u4')
        o=gemv.check_b1(b,x,y,n,k); c[o.status]+=1; rows+=o.rows_checked; viol+=o.rows_violating
        v=float(o.worst_ratio)
        if v>worst: worst,wt=v,r['tensor']
    out=dict(fault=f,b1_all=dict(c),rows=rows,rows_violating=viol,worst=worst,worst_tensor=wt); print(json.dumps(out),flush=True)
    open(N+'/full_b1.jsonl','a').write(json.dumps(out)+'\n')
