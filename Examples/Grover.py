#Grover's Search Algorithm

from dsl.api import *

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

GRAPH(p, "statevector")
