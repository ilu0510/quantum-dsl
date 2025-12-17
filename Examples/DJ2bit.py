#Deutsch-Jozsa 2 Bit Algorithm

#---PennyLane---

import pennylane as qml

def oracle_const0(x0, x1, a):
    return

def oracle_const1(x0, x1, a):
    qml.PauliX(wires=a)

def oracle_x0(x0, x1, a):
    qml.CNOT(wires=[x0, a])

def oracle_x1(x0, x1, a):
    qml.CNOT(wires=[x1, a])

def oracle_x0_x1(x0, x1, a):
    qml.CNOT(wires=[x0, a])
    qml.CNOT(wires=[x1, a])

def dj_2bit(oracle, x0, x1, a):
    qml.PauliX(wires=a)
    qml.Hadamard(wires=[a, x0, x1])
    oracle(x0, x1, a)
    qml.Hadamard(wires=[x0, x1])
    return qml.probs(wires=[x0, x1])

def run_dj(oracle_fn, n_qubits=3, x0=0, x1=1, a=2, shots=None):
    dev = qml.device("default.qubit", wires=n_qubits, shots=shots)
    @qml.qnode(dev)
    def circuit():
        return dj_2bit(oracle_fn, x0=x0, x1=x1, a=a)
    out = circuit()
    name = getattr(oracle_fn, "__name__", str(oracle_fn))
    print(f"{name} -> {out}")
    return out

run_dj(oracle_const0)
run_dj(oracle_const1)
run_dj(oracle_x0)
run_dj(oracle_x1)
run_dj(oracle_x0_x1)

#LOC: 32


#---DSL---

from dsl import *

@BLOCK("oracle_const0")
def oracle_const0(x0, x1, a):
    # f(x) = 0: do nothing
    return

@BLOCK("oracle_const1")
def oracle_const1(x0, x1, a):
    gate.X(a)

@BLOCK("oracle_x0")
def oracle_x0(x0, x1, a):
    # f(x) = x0
    gate.CNOT((x0, a))

@BLOCK("oracle_x1")
def oracle_x1(x0, x1, a):
    # f(x) = x1
    gate.CNOT((x1, a))

@BLOCK("oracle_x0_x1")
def oracle_x0_x1(x0, x1, a):
    # f(x) = x0 XOR x1
    gate.CNOT((x0, a), (x1, a))


@BLOCK("dj_2bit")
def dj_2bit(oracle, x0, x1, a):
    gate.X(a)
    SUPERPOSE(a, x0, x1)
    USE(oracle, x0=x0, x1=x1, a=a)
    SUPERPOSE(x0, x1)
    MEASURE("probs", x0, x1)

def run_dj(oracle_name, n_qubits=3, x0=0, x1=1, a=2):
    with PREPARE(n_qubits) as p:
        USE("dj_2bit", oracle=oracle_name, x0=x0, x1=x1, a=a)
    out = p()
    print(oracle_name, "->", out)
    return out

run_dj("oracle_const0")
run_dj("oracle_const1")
run_dj("oracle_x0")
run_dj("oracle_x1")
run_dj("oracle_x0_x1")

#LOC: 34



