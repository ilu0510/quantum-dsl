#Quantum Fourier Transform

#---PennyLane---

import pennylane as qml
import numpy as np
import matplotlib.pyplot as plt

def qft(wires):
    n = len(wires)
    for i in range(n):
        qml.Hadamard(wires=wires[i])
        for j in range(i + 1, n):
            angle = np.pi / (2 ** (j - i))
            qml.CRZ(angle, wires=[wires[j], wires[i]])

    for i in range(n // 2):
        qml.SWAP(wires=[wires[i], wires[n - 1 - i]])


dev = qml.device("default.qubit", wires=4, shots=None)

@qml.qnode(dev)
def circuit():
    qml.PauliX(wires=[0,1,2])
    qft([0, 1, 2, 3])
    return qml.state()

print(qml.draw(circuit)())
state = circuit()

for i, amp in enumerate(state):
    b = format(i, "04b")
    print(f"|{b}>: {amp.real:+.6f} {amp.imag:+.6f}j")

labels = [format(i, "04b") for i in range(2**4)]
x = np.arange(len(labels))

plt.figure()
plt.bar(x, np.real(state))
plt.xticks(x, labels, rotation=45, ha="right")
plt.xlabel("Basis state |q0 q1 q2 q3>")
plt.ylabel("Re(amplitude)")
plt.title("Statevector amplitudes: real part")
plt.tight_layout()
plt.show()

plt.figure()
plt.bar(x, np.imag(state))
plt.xticks(x, labels, rotation=45, ha="right")
plt.xlabel("Basis state |q0 q1 q2 q3>")
plt.ylabel("Im(amplitude)")
plt.title("Statevector amplitudes: imaginary part")
plt.tight_layout()
plt.show()

#LOC: 41

#---DSL--- 
from dsl import *

@BLOCK("qft")
def qft(wires):
    n = len(wires)
    for i in range(n):
        SUPERPOSE(wires[i])
        for j in range (i+1, n):
            angle = np.pi/(2**(j-i))
            gate.CRZ(angle, wires[j], wires[i])

    for i in range(n//2):
        gate.SWAP((wires[i], wires[n-1-i]))

with PREPARE(4) as p:
    gate.X(0,1,2)
    USE("qft", [0,1,2,3]) 
    MEASURE("state")

print(p())
GRAPH(p, "statevector")

#LOC: 17






