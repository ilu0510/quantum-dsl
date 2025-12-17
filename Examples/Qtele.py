#Quantum Teleportation

#---PennyLane---

import pennylane as qml
import numpy as np

def teleport(state):
    qml.StatePrep(state, wires=[0])
    qml.Hadamard(wires=1)
    qml.CNOT(wires=[1, 2])
    qml.CNOT(wires=[0, 1])
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[1, 2])
    qml.CZ(wires=[0, 2])

state_to_teleport = np.array([1 / np.sqrt(2), 1 / np.sqrt(2)])

dev = qml.device("default.qubit", wires=3)

@qml.qnode(dev)
def circuit():
    teleport(state_to_teleport)
    return qml.state()

print(qml.draw(circuit)())


 # ---DSL---

from dsl import *
import numpy as np

@BLOCK("teleport")
def teleport(state):
    STATE_PREP(state, 0)
    BELL_PHI_PLUS(1,2)
    gate.CNOT([0,1])
    SUPERPOSE(0)
    gate.CNOT([1,2])
    gate.CZ([0,2])
    
state_to_teleport = np.array([1/np.sqrt(2), 1/np.sqrt(2)])

with PREPARE(3) as p:
    USE("teleport", state=state_to_teleport)
    MEASURE("state")

DRAW(p, 'ascii')






