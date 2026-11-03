import sys
fault,p=sys.argv[1:3]; s=open(p).read()
loop_old="""        for (j, &c) in codes.iter().enumerate() {
            // `d * q` first, then the activation — the decoder's
            // association, element by element. See the module note on
            // why this is exact and why hoisting `d` would not be.
            acc += ((c as i8 as f32) * d) * xs[j];
        }
"""
assert s.count(loop_old)==1
def rep(a,b):
    global s
    assert s.count(a)==1,a
    s=s.replace(a,b)
if fault=='reverse_blocks': rep("for b in 0..per_row {","for b in (0..per_row).rev() {")
elif fault=='hoist_scale': rep(loop_old,"""        let mut sum = 0.0f32;
        for (j, &c) in codes.iter().enumerate() { sum += (c as i8 as f32) * xs[j]; }
        acc += d * sum;
""")
elif fault=='binary64_acc':
    rep("let mut acc = 0.0f32;","let mut acc = 0.0f64;"); rep(loop_old,"""        for (j, &c) in codes.iter().enumerate() { acc += ((c as i8 as f64) * d as f64) * xs[j] as f64; }
"""); rep("    acc\n}","    acc as f32\n}")
elif fault=='unsigned_codes': rep(loop_old,loop_old.replace("(c as i8 as f32)","(c as f32)"))
elif fault=='wrong_last_element': rep(loop_old,loop_old.replace("* xs[j];","* xs[if j == 31 { 30 } else { j }];"))
elif fault=='flush_subnormal_scale': rep("let d = f16_to_f32(u16::from_le_bytes([blocks[base], blocks[base + 1]]));","let d = { let h = u16::from_le_bytes([blocks[base], blocks[base + 1]]); if h & 0x7c00 == 0 { 0.0 } else { f16_to_f32(h) } };")
else: sys.exit('unknown')
open(p,'w').write(s)
