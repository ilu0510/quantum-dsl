import numpy as np
from dsl import *

ATOL = 1e-9
RTOL = 1e-7


def _as_np(x):
    if isinstance(x, tuple):
        return tuple(_as_np(t) for t in x)
    return np.asarray(x)


def allclose(a, b, atol=ATOL, rtol=RTOL):
    if isinstance(a, tuple) and isinstance(b, tuple):
        return len(a) == len(b) and all(
            allclose(x, y, atol=atol, rtol=rtol) for x, y in zip(a, b)
        )
    a = _as_np(a)
    b = _as_np(b)
    if a.shape == () and b.shape == ():
        return bool(np.isclose(a, b, atol=atol, rtol=rtol))
    return bool(np.allclose(a, b, atol=atol, rtol=rtol))


def max_abs_diff(a, b):
    if isinstance(a, tuple) and isinstance(b, tuple):
        if len(a) != len(b):
            raise ValueError("Tuple outputs have different lengths.")
        return max(max_abs_diff(x, y) for x, y in zip(a, b))

    a = np.asarray(a)
    b = np.asarray(b)

    if a.shape != b.shape:
        raise ValueError(f"Shape mismatch: {a.shape} vs {b.shape}")

    if a.shape == () and b.shape == ():
        return float(np.abs(a - b))

    return float(np.max(np.abs(a - b)))


def output_type_of(result):
    if isinstance(result, tuple):
        inner = ", ".join(output_type_of(x) for x in result)
        return f"tuple[{inner}]"

    arr = np.asarray(result)
    if arr.shape == ():
        return "expval"
    if arr.ndim == 1:
        if np.iscomplexobj(arr):
            return "statevector"
        return "probs"
    if arr.ndim == 2:
        return "density matrix"
    return f"array{arr.shape}"


def compare(label, program_builder, atol=ATOL, rtol=RTOL):
    p = program_builder()

    p.compile(backend="pennylane")
    out_pl = p()

    p._compiled = None
    p.compile(backend="qiskit")
    out_qk = p()

    ok = allclose(out_pl, out_qk, atol=atol, rtol=rtol)
    mad = max_abs_diff(out_pl, out_qk)
    out_type = output_type_of(out_pl)

    print("\n" + "=" * 80)
    print(f"{label} => {'PASS' if ok else 'FAIL'}")
    print(f"Output type  : {out_type}")
    print(f"Max abs diff : {mad:.3e}")
    print(f"Tolerance    : atol={atol:.1e}, rtol={rtol:.1e}")
    print("PennyLane    :", out_pl)
    print("Qiskit       :", out_qk)

    return {
        "label": label,
        "output_type": out_type,
        "pass": ok,
        "max_abs_diff": mad,
        "atol": atol,
        "rtol": rtol,
    }


# Bell State Probs
def t_bell_probs():
    with PREPARE(2) as p:
        SUPERPOSE(0)
        ENTANGLE(0, 1)
        MEASURE("probs", 0, 1)
    return p


# Wire Subset Probs (catching bit-ordering)
def t_probs_subset():
    with PREPARE(3) as p:
        gate.X(0)  # |100> in wire-indexing sense
        SUPERPOSE(1)
        ENTANGLE(1, 2)
        # probs on wires (2,1) intentionally reversed to test ordering
        MEASURE("probs", 2, 1)
    return p


# Controlled gate
def t_ctrl_Z():
    with PREPARE(3) as p:
        SUPERPOSE(0, 1)
        # Apply multi-control Z onto wire 2 (controls 0 and 1, target 2)
        gate.CTRL("Z", [0, 1], 2)
        MEASURE("state")
    return p


# Controlled Rotation Gate
def t_crz():
    with PREPARE(2) as p:
        SUPERPOSE(0)
        gate.CRZ(np.pi / 3, 0, 1)
        MEASURE("state")
    return p


# State Prep
def t_stateprep_1q():
    state = np.array([1 / np.sqrt(2), 1j / np.sqrt(2)], dtype=complex)
    with PREPARE(1) as p:
        STATE_PREP(state, 0)
        MEASURE("state")
    return p


# Basis State (bitstring mapping)
def t_basisstate():
    with PREPARE(3) as p:
        BASIS_STATE([1, 0, 1])  # expects X on wires 0 and 2 in qiskit path
        MEASURE("state")
    return p


# Expvals
def t_expval_X():
    with PREPARE(1) as p:
        gate.RY(0.37, 0)
        MEASURE("expval", 0, observable="X")
    return p


def t_expval_H():
    with PREPARE(1) as p:
        gate.RY(0.37, 0)
        MEASURE("expval", 0, observable="H")
    return p


# Density Matrix
def t_density_subset():
    with PREPARE(2) as p:
        SUPERPOSE(0)
        ENTANGLE(0, 1)
        MEASURE("density matrix", 0)  # reduced density matrix on wire 0
    return p


if __name__ == "__main__":
    tests = [
        ("Bell probabilities", t_bell_probs),
        ("Probability subset (reversed wires)", t_probs_subset),
        ("CTRL-Z (two controls)", t_ctrl_Z),
        ("CRZ rotation", t_crz),
        ("State preparation", t_stateprep_1q),
        ("Basis state initialization", t_basisstate),
        ("Expectation value (Pauli X)", t_expval_X),
        ("Expectation value (Hadamard)", t_expval_H),
        ("Density matrix (subsystem)", t_density_subset),
    ]

    results = []
    all_ok = True

    for label, fn in tests:
        record = compare(label, fn, atol=ATOL, rtol=RTOL)
        results.append(record)
        all_ok &= record["pass"]

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(
            f"{r['label']:<38} {r['output_type']:<14} "
            f"{status:<5} max_abs_diff={r['max_abs_diff']:.3e} "
            f"atol={r['atol']:.1e} rtol={r['rtol']:.1e}"
        )

    max_overall = max(r["max_abs_diff"] for r in results)
    print("\nOverall maximum absolute difference:", f"{max_overall:.3e}")
    print(f"Tolerance used: atol={ATOL:.1e}, rtol={RTOL:.1e}")

    raise SystemExit(0 if all_ok else 1)