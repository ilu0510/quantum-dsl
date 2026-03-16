#Grover's Search Algorithm

#---PennyLane---

import pennylane as qml
import numpy as np
import matplotlib.pyplot as plt
def oracle():
    qml.PauliX(wires=[0,2])
    qml.CCZ(wires=[0, 2, 1])
    qml.PauliX(wires=[0,2])
def diffusion():
    qml.Hadamard(wires=[0,1,2])
    qml.PauliX(wires=[0,1,2])
    qml.CCZ(wires=[0, 1, 2])
    qml.PauliX(wires=[0,1,2])
    qml.Hadamard(wires=[0,1,2])
dev = qml.device("default.qubit", wires=3)
@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=[0,1,2])
    oracle()
    diffusion()
    oracle()
    diffusion()
    return qml.probs(wires=[0, 1, 2])
print(qml.draw(circuit)())
probs = circuit()
print(probs)
labels = [format(i, "03b") for i in range(2**3)]
plt.figure()
plt.bar(labels, probs)
plt.xlabel("Basis state |q0 q1 q2>")
plt.ylabel("Probability")
plt.title("Measurement probabilities (qml.probs)")
plt.show()

#LOC: 32

# Qiskit
# Grover's Search Algorithm

# ---Qiskit---

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
import numpy as np
import matplotlib.pyplot as plt
def oracle(qc):
    qc.x([0, 2])
    qc.ccz(0, 2, 1)
    qc.x([0, 2])
def diffusion(qc):
    qc.h([0, 1, 2])
    qc.x([0, 1, 2])
    qc.ccz(0, 1, 2)
    qc.x([0, 1, 2])
    qc.h([0, 1, 2])
def circuit():
    qc = QuantumCircuit(3)
    qc.h([0, 1, 2])
    oracle(qc)
    diffusion(qc)
    oracle(qc)
    diffusion(qc)
    return qc
qc = circuit()
print(qc.draw())
probs = Statevector.from_instruction(qc).probabilities([0, 1, 2])
print(probs)
labels = [format(i, "03b") for i in range(2**3)]
plt.figure()
plt.bar(labels, probs)
plt.xlabel("Basis state |q0 q1 q2>")
plt.ylabel("Probability")
plt.title("Measurement probabilities")
plt.show()

# LOC: 31

#---DSL---

from dsl import *
@BLOCK("oracle")
def oracle():
    gate.X(0,2)
    gate.CTRL("Z", [0,2], 1)
    gate.X(0,2)
@BLOCK("diffusion")
def diffusion():
    SUPERPOSE(0,1,2)
    gate.X(0,1,2)
    gate.CTRL("Z", [0,1], 2)
    gate.X(0,1,2)
    SUPERPOSE(0,1,2)
with PREPARE(3) as p:
    SUPERPOSE(0,1,2)
    USE("oracle")
    USE("diffusion")
    USE("oracle")
    USE("diffusion")
    MEASURE("probs", 0, 1, 2)
INSPECT_IR(p)
print(p())
DRAW(p, "ascii")
GRAPH(p, "probs")

#LOC: 23