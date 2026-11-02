"""A representation contract, measured independently of LARQL (development only, decision revision D15).

Called by LQL's VERIFY REPRESENTATION, or directly. Protocol `larql-verify-contract/1`: one JSON object on stdout, nothing
else there. Exit 0 whenever the contract was judged or could not be evaluated; a non-zero exit means the verifier itself
failed. The measurement is refcheck.e1, the checker's audited E1, against a checkpoint verified by its pinned hashes. Nothing
here imports or runs LARQL. It reads and writes no file other than what it reads to measure.

  larql-verifier contract --contract Q8_0_T2 --container <dir> --source <checkpoint dir>

A result is a numerical measurement of one container, not a proof about the encoder that produced it.
"""

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import larql_verify as L  # noqa: E402  (also puts the vendored refcheck on sys.path)
from refcheck import container as C  # noqa: E402
from refcheck import e1 as E1  # noqa: E402
from refcheck import harness as H  # noqa: E402

SCHEMA = "larql-verify-contract/1"
STATEMENTS = {
    "Q8_0_T2": "every element of every Q8_0 tensor is within the T2 reconstruction bound of its source value",
}


def verifier_identity():
    pin = json.load(open(os.path.join(L.VENDOR, "PIN.json")))
    return {"name": "transformer-verifiers refcheck.e1", "refcheck_commit": pin["checker_commit"],
            "refcheck_tree": pin["refcheck_tree"], "script_sha256": L.sha256_file(os.path.abspath(__file__))}


def could_not(out, *reasons):
    out.update(status="could_not_evaluate", reasons=list(reasons))
    return out


def q8_0_t2(out, container, source):
    try:
        files = H.verify_snapshot(source)
    except Exception as e:  # noqa: BLE001
        return could_not(out, f"the source checkpoint is not one whose hashes are pinned here: {e}")
    out["source"]["identity"] = f"{len(files)} files match refcheck's pinned SHA-256 hashes"
    try:
        c = C.open_container(container)
    except Exception as e:  # noqa: BLE001
        return could_not(out, f"the validating reader refused the container: {e}")
    Wu = H.load_upstream(source)
    rep = E1.e1_report(c, lambda k: Wu[k], {k: tuple(v.shape) for k, v in Wu.items()})
    tot = rep["total"]
    problems = []
    if not rep["coverage"]["ok"]:
        problems.append(f"the container's tensors do not match the source checkpoint: {rep['coverage']}")
    if not tot["n_q8_tensors"]:
        problems.append("the container has no Q8_0 tensors, so the contract would hold vacuously")
    outside = sum(v["blocks"] for v in tot["outside_t2_domain"].values())
    if outside:
        problems.append(f"{outside} blocks have a stored scale outside T2's domain, about which T2 says nothing")
    if tot["n_upstream_nonfinite"]:
        problems.append(f"{tot['n_upstream_nonfinite']} source elements are not finite")
    if problems:
        return could_not(out, *problems)

    q = {k: t for k, t in rep["tensors"].items() if t["dtype"] == "Q8_0"}
    offending = sorted(((k, t) for k, t in q.items() if t["n_exceed_t2"]),
                       key=lambda kv: (-kv[1]["n_exceed_t2"], kv[0]))
    n_blocks = sum(t["n_blocks"] for t in q.values()) if all("n_blocks" in t for t in q.values()) else None
    out.update(
        status="violated" if tot["n_exceed_t2"] else "satisfied",
        violations=tot["n_exceed_t2"],
        measurements=[
            {"name": "Q8_0 tensors", "value": str(tot["n_q8_tensors"])},
            {"name": "elements over T2", "value": str(tot["n_exceed_t2"])},
            {"name": "blocks over T2", "value": str(tot["n_blocks_exceed_t2"])},
            {"name": "zero-scale blocks", "value": str(tot["zero_scale_blocks"])},
            {"name": "worst error / T2 bound", "value": f"{tot['worst_ratio']:.6g}"},
            {"name": "max |source - decoded|", "value": f"{tot['max_abs_error']:.6g}"},
            {"name": "decode matches gguf-py", "value": str(tot["gguf_all_bit_identical"]).lower()},
        ],
        offending=[{"name": k, "violations": t["n_exceed_t2"],
                    "detail": f"{t['n_blocks_exceed_t2']} blocks, worst error / bound {t['worst_ratio']:.6g}"}
                   for k, t in offending],
        report_sha256=hashlib.sha256(E1.canonical_json(rep).encode()).hexdigest(),
    )
    return out


def main():
    ap = argparse.ArgumentParser(prog="larql-verifier")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("contract")
    p.add_argument("--contract", required=True)
    p.add_argument("--container", required=True)
    p.add_argument("--source", required=True)
    a = ap.parse_args()
    container, source = os.path.abspath(a.container), os.path.abspath(a.source)
    out = {"schema": SCHEMA, "contract": a.contract, "contract_statement": STATEMENTS.get(a.contract, ""),
           "evidence_kind": "numerical_measurement", "status": None, "violations": 0,
           "container": {"path": a.container, "sha256": None}, "source": {"path": a.source, "identity": None},
           "measurements": [], "offending": [], "reasons": [], "verifier": verifier_identity()}
    if a.contract not in STATEMENTS:
        could_not(out, f"unknown contract {a.contract!r}; this verifier knows {sorted(STATEMENTS)}")
    elif not os.path.isdir(container):
        could_not(out, "the container is not a directory")
    else:
        out["container"]["sha256"] = H.container_sha256(container)
        q8_0_t2(out, container, source)
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
