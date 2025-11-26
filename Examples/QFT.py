from dsl import *
import numpy as np


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
    gate.X(0,1)
    USE("qft", [0,1,2,3])
    MEASURE("state")   

DRAW(p, "ascii")
GRAPH(p, "statevector")



