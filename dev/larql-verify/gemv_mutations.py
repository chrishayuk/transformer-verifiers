import subprocess,sys,shutil,os,tempfile
PY=sys.argv[1]; root=os.getcwd(); src=open('refcheck/gemv.py').read()
M=[('reverse sum order','for j in range(k):','for j in reversed(range(k)):'),
('drop eta term','rhs = k * S[i] + k * _ETA_U * _TWO24','rhs = k * S[i] + 1'),
('halve gamma term','rhs = k * S[i] +','rhs = (k // 2) * S[i] +'),
('halve eta','_ETA_U = 1 << 23','_ETA_U = 1 << 22'),
('double eta','_ETA_U = 1 << 23','_ETA_U = 1 << 24'),
('double gamma term','rhs = k * S[i] +','rhs = (2 * k) * S[i] +'),
('Omega too large','_OMEGA_U = ((1 << 128) - (1 << 103)) << 173','_OMEGA_U = ((1 << 129) - (1 << 103)) << 173'),
('domain third always true','return _TWO24 * (S + k * _ETA_U) < _OMEGA_U * (_TWO24 - k)','return True'),
('domain without k*eta','return _TWO24 * (S + k * _ETA_U) < _OMEGA_U * (_TWO24 - k)','return _TWO24 * S < _OMEGA_U * (_TWO24 - k)'),
('signed difference','dif = abs(yi * (1 << 24) - ystar[i])','dif = (yi * (1 << 24) - ystar[i])'),
('non-strict compare','if lhs > rhs:','if lhs >= rhs:'),
]
for name,a,b in M:
    assert src.count(a)>=1,name
    d=tempfile.mkdtemp(); shutil.copytree('refcheck',d+'/refcheck'); shutil.copytree('tests',d+'/tests')
    open(d+'/refcheck/gemv.py','w').write(src.replace(a,b))
    r=subprocess.run([PY,'-I','-m','unittest','discover','-s','tests','-p','test_gemv*'],cwd=d,capture_output=True,text=True)
    last=[l for l in r.stderr.splitlines() if l.startswith(('OK','FAILED'))]
    print(f"{name:32s} {'CAUGHT' if r.returncode else 'SURVIVED':9s} {last[-1] if last else ''}",flush=True)
    shutil.rmtree(d)
