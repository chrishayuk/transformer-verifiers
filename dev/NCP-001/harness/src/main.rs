//! NCP-001's frozen benchmark and conformance runner. It calls the production `q8_0_gemv` and does nothing else
//! in the timed region. It lives outside the candidate workspace, and the agent can't read or change it.
//!
//!   ncp001-harness bench <cases.tsv> <reps> <out.tsv>   per case: warm median and minimum, first-touch time, output digest
//!   ncp001-harness conform <cases.tsv> <outdir>         per case: the output's raw bits
//!   ncp001-harness refuse                               exit 0 only if bad geometry is refused
//!
//! cases.tsv columns: id, rows, columns, blocks file, x file.
use larql_compute::cpu::kquant_gemv::q8_0_gemv;
use std::hint::black_box;
use std::time::Instant;

struct Case {
    id: String,
    n: usize,
    k: usize,
    blocks: Vec<u8>,
    x: Vec<f32>,
}

fn load(path: &str) -> Vec<Case> {
    std::fs::read_to_string(path)
        .unwrap()
        .lines()
        .filter(|l| !l.is_empty())
        .map(|l| {
            let f: Vec<&str> = l.split('\t').collect();
            let x = std::fs::read(f[4]).unwrap();
            Case {
                id: f[0].to_owned(),
                n: f[1].parse().unwrap(),
                k: f[2].parse().unwrap(),
                blocks: std::fs::read(f[3]).unwrap(),
                x: x.chunks_exact(4)
                    .map(|b| f32::from_bits(u32::from_le_bytes([b[0], b[1], b[2], b[3]])))
                    .collect(),
            }
        })
        .collect()
}

fn run(c: &Case) -> Vec<f32> {
    q8_0_gemv(black_box(&c.blocks), black_box(&c.x), c.n, c.k).expect("the kernel refused valid geometry")
}

fn fnv(y: &[f32]) -> u64 {
    let mut h = 0xcbf29ce484222325u64;
    for v in y {
        for b in v.to_bits().to_le_bytes() {
            h = (h ^ b as u64).wrapping_mul(0x100000001b3);
        }
    }
    h
}

fn bench(cases: &str, reps: usize, out: &str) {
    let cases = load(cases);
    let mut text = String::new();
    for c in &cases {
        let t = Instant::now();
        let first = run(c);
        let first_ns = t.elapsed().as_nanos() as u64;
        let mut ns = Vec::with_capacity(reps);
        for _ in 0..reps {
            let t = Instant::now();
            black_box(run(c));
            ns.push(t.elapsed().as_nanos() as u64);
        }
        ns.sort_unstable();
        text += &format!("{}\t{}\t{}\t{}\t{:016x}\n", c.id, ns[ns.len() / 2], ns[0], first_ns, fnv(&first));
    }
    std::fs::write(out, text).unwrap();
}

fn conform(cases: &str, dir: &str) {
    for c in load(cases) {
        let y: Vec<u8> = run(&c).iter().flat_map(|v| v.to_bits().to_le_bytes()).collect();
        std::fs::write(format!("{dir}/{}.y", c.id), y).unwrap();
    }
}

fn refuse() {
    let x = vec![0.0f32; 32];
    let b = vec![0u8; 34];
    let bad = [
        q8_0_gemv(&b, &x, 1, 0),
        q8_0_gemv(&b, &x, 1, 31),
        q8_0_gemv(&b, &x[..31], 1, 32),
        q8_0_gemv(&b[..33], &x, 1, 32),
        q8_0_gemv(&b, &x, 2, 32),
    ];
    assert!(bad.iter().all(Option::is_none), "bad geometry was accepted");
    assert_eq!(q8_0_gemv(&[], &x, 0, 32), Some(vec![]));
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    match a[1].as_str() {
        "bench" => bench(&a[2], a[3].parse().unwrap(), &a[4]),
        "conform" => conform(&a[2], &a[3]),
        "refuse" => refuse(),
        other => panic!("unknown mode {other}"),
    }
}
