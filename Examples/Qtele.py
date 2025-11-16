#Quantum Teleportation



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
    MEASURE("probs", 2)

state_to_teleport = np.array([1/np.sqrt(2), 1/np.sqrt(2)])

with PREPARE(3) as p:
    USE("teleport", state=state_to_teleport)

GRAPH(p, "probs")
