import numpy as np
from dsl import *

def _as_np(x):
    if isinstance(x, tuple):
        return tuple(_as_np(t) for t in x)
    return np.asarray(x)

def allclose(a, b, atol=1e-9, rtol=1e-7):
    if isinstance(a, tuple) and isinstance(b, tuple):
        return len(a) == len(b) and all(allclose(x, y, atol, rtol) for x, y in zip(a, b))
    a = _as_np(a)
    b = _as_np(b)
    if a.shape == () and b.shape == ():
        return np.isclose(a, b, atol=atol, rtol=rtol)
    return np.allclose(a, b, atol=atol, rtol=rtol)

def compare(label, program_builder, atol=1e-9, rtol=1e-7):
    p = program_builder()

    p.compile(backend="pennylane")
    out_pl = p()

    p._compiled = None
    p.compile(backend="qiskit")
    out_qk = p()

    ok = allclose(out_pl, out_qk, atol=atol, rtol=rtol)
    print("\n" + "="*80)
    print(label, "=>", "OK" if ok else "FAIL")
    print("PennyLane:", out_pl)
    print("Qiskit   :", out_qk)
    return ok

#Bell State Probs
def t_bell_probs():
    with PREPARE(2) as p:
        SUPERPOSE(0)
        ENTANGLE(0, 1)
        MEASURE("probs", 0, 1)
    return p

#Wire Subset Probs (catching bit-ordering)
def t_probs_subset():
    with PREPARE(3) as p:
        gate.X(0)         # |100> (in wire indexing sense)
        SUPERPOSE(1)
        ENTANGLE(1, 2)
        # probs on wires (2,1) intentionally reversed to test ordering
        MEASURE("probs", 2, 1)
    return p

#Controlled gate 
def t_ctrl_Z():
    with PREPARE(3) as p:
        SUPERPOSE(0, 1)
        # Apply multi-control Z onto wire 2 (controls 0 and 1, target 2)
        gate.CTRL("Z", [0, 1], 2)
        MEASURE("state")
    return p


#Controlled Rotation Gate (catching bit-ordering)
def t_crz():
    with PREPARE(2) as p:
        SUPERPOSE(0)
        gate.CRZ(np.pi/3, 0, 1)
        MEASURE("state")
    return p

#State Prep
def t_stateprep_1q():
    state = np.array([1/np.sqrt(2), 1j/np.sqrt(2)], dtype=complex)
    with PREPARE(1) as p:
        STATE_PREP(state, 0)
        MEASURE("state")
    return p

#Basis State (bitstring mapping)
def t_basisstate():
    with PREPARE(3) as p:
        BASIS_STATE([1, 0, 1])   # expects X on wires 0 and 2 in qiskit path
        MEASURE("state")
    return p

#Expvals
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

#Density Matirx
def t_density_subset():
    with PREPARE(2) as p:
        SUPERPOSE(0)
        ENTANGLE(0, 1)
        MEASURE("density matrix", 0)  # reduced density matrix on wire 0
    return p


#Run
if __name__ == "__main__":
    tests = [
        ("Bell probs", t_bell_probs),
        ("Probs subset reversed wires", t_probs_subset),
        ("CTRL Z 2 controls", t_ctrl_Z),
        ("CRZ state", t_crz),
        ("StatePrep 1q", t_stateprep_1q),
        ("BasisState 3q", t_basisstate),
        ("Expval X", t_expval_X),
        ("Expval H", t_expval_H),
        ("Density matrix subset", t_density_subset),
    ]

    all_ok = True
    for label, fn in tests:
        all_ok &= compare(label, fn)

    raise SystemExit(0 if all_ok else 1)