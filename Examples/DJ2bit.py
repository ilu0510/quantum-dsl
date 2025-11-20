#Deutsch-Jozsa 2 Bit Algorithm
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
    SUPERPOSE(a)
    SUPERPOSE(x0, x1)
    # black-box oracle------------
    USE(oracle, x0=x0, x1=x1, a=a)
    #-----------------------------
    SUPERPOSE(x0, x1)
    MEASURE("probs", x0, x1)

#--------------------------------------
#Constant Oracles
with PREPARE(3) as p:
    USE("dj_2bit", oracle="oracle_const0", x0=0, x1=1, a=2)
print(p())

with PREPARE(3) as p:
    USE("dj_2bit", oracle="oracle_const1", x0=0, x1=1, a=2)
print(p())
#-----------------------------------
# Balanced oracles
with PREPARE(3) as p:
    USE("dj_2bit", oracle="oracle_x0", x0=0, x1=1, a=2)
print(p())
# >> out: [0.0, 0.0, 1.0, 0.0]

with PREPARE(3) as p:
    USE("dj_2bit", oracle="oracle_x1", x0=0, x1=1, a=2)
print(p())
# >> out: [0.0, 1.0, 0.0, 0.0]

with PREPARE(3) as p:
    USE("dj_2bit", oracle="oracle_x0_x1", x0=0, x1=1, a=2)
print(p())
# >> out: [0.0, 0.0, 0.0, 1.0]   # |11>
