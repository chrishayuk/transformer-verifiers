import json,os,sys,collections
sys.path.insert(0,os.getcwd())
import numpy as np
from refcheck import gemv
W,f=sys.argv[1:3]; m=json.load(open(W+'/witness.json')); rd=lambda s:open(os.path.join(W,s['file']),'rb').read()
seq=collections.Counter(); bad=[]; rows=viol=0; recs=[]
for r in m['records']:
    n,k=r['rows'],r['columns']; b=rd(r['blocks']); x=np.frombuffer(rd(r['x']),dtype='<u4'); y=np.frombuffer(rd(r['y']),dtype='<u4')
    s=gemv.check_seq(b,x,y,n,k); seq[s.status]+=1; rows+=s.rows_checked; viol+=s.rows_violating
    recs.append((s.status!='satisfied',r))
# B1 on up to 12 operations, those SEQ flagged first
pick=[r for v,r in recs if v][:12] or [r for _,r in recs][:12]; b1=collections.Counter(); worst=0.0
for r in pick:
    n,k=r['rows'],r['columns']; b=rd(r['blocks']); x=np.frombuffer(rd(r['x']),dtype='<u4'); y=np.frombuffer(rd(r['y']),dtype='<u4')
    o=gemv.check_b1(b,x,y,n,k); b1[o.status]+=1; worst=max(worst,float(o.worst_ratio))
out=dict(fault=f,seq=dict(seq),seq_rows_checked=rows,seq_rows_violating=viol,b1_sampled=dict(b1),b1_worst=worst,commit=m['build_commit'],calls=m['calls_observed'])
print(json.dumps(out),flush=True); open(os.environ['TMPDIR']+'/gemvneg/results.jsonl','a').write(json.dumps(out)+'\n')
