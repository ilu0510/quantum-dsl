# #Variational Quantum Eigensolver

# #---PennyLane---
# import pennylane as qml
# from pennylane import numpy as np
# import matplotlib.pyplot as plt

# dev = qml.device("default.qubit", wires=2)
# H = qml.PauliX(0) @ qml.PauliX(1)

# @qml.qnode(dev)
# def vqe_circuit(params):
#     qml.RY(params[0], wires=0)
#     qml.CNOT(wires=[0, 1])
#     return qml.expval(H)

# def cost(params):
#     return vqe_circuit(params)

# # Optimisation loop
# params = np.array([0.1], requires_grad=True)
# opt = qml.GradientDescentOptimizer(stepsize=0.4)
# steps = 30

# energies = []

# for i in range(steps):
#     params = opt.step(cost, params)     
#     energy = cost(params)                
#     energies.append(float(energy))

#     print(f"Step {i:02d} | Energy = {energy:.8f} | Params = {params}")

# print("\nFinal energy:", cost(params))
# print("Final params:", params)

# plt.figure()
# plt.plot(range(len(energies)), energies, marker="o")
# plt.xlabel("Step")
# plt.ylabel("Energy")
# plt.title("Energy vs Optimisation Step")
# plt.grid(True)
# plt.show()



#---DSL--- 
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

best_params, best_E = OPTIMISE(energy_fn=energy,
                               init_params=[0.1], 
                               steps=15, 
                               stepsize=0.5, 
                               eps=1e-6, 
                               history=True, 
                               graph=True,)

print("Final energy:", best_E)
print("Final params:", best_params)

with PREPARE(2) as p_state:
    USE("vqe_ansatz", best_params)    
    MEASURE("state")                  

GRAPH(p_state, "statevector")
GRAPH(p_state, "probs")