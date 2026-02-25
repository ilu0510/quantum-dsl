from dsl import *

with PREPARE(2) as p:
    @BLOCK("bell")
    def bell():
        SUPERPOSE(0)
        ENTANGLE(0, 1)

    USE("bell")
    MEASURE("probs", 0, 1)

print(INSPECT_IR(p))
