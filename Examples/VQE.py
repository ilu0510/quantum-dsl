#Variational Quantum Eigensolver
from dsl import *

H = (obs.X(0) @ obs.X(1))

@BLOCK("vqe_ansatz")
def vqe_ansatz(params):
    theta0 = params[0]
    gate.RY(theta0, 0)
    gate.CNOT((0, 1))

def energy(theta):
    with PREPARE(2) as p:
        USE("vqe_ansatz", theta)
        MEASURE("expval", hamiltonian=H)
    return p()

best_params, best_E = OPTIMISE(energy_fn=energy, init_params=[0.1], steps=30, stepsize=0.4, eps=1e-6, history=True, graph=True,)

print("Final energy:", best_E)
print("Final params:", best_params)

