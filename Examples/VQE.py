# #Variational Quantum Eigensolver
import pennylane as qml
from pennylane import numpy as np
import matplotlib.pyplot as plt

#Device
dev = qml.device("default.qubit", wires=2)

#Hamiltonian
H = qml.PauliX(0) @ qml.PauliX(1)

#Ansatz 
def ansatz(params):
    qml.RY(params[0], wires=0)
    qml.CNOT(wires=[0, 1])

#QNode
@qml.qnode(dev)
def vqe_all(params):
    ansatz(params)
    return (
        qml.expval(H),
        qml.state(),
        qml.probs(wires=[0, 1])
    )

# For optimisation, we only use the energy
def cost(params):
    energy, _, _ = vqe_all(params)
    return energy

# Optimisation loop
params = np.array([0.1], requires_grad=True)
opt = qml.GradientDescentOptimizer(stepsize=0.4)
steps = 30
energies = []
for i in range(steps):
    params = opt.step(cost, params)
    energy = cost(params)
    energies.append(float(energy))
    print(f"Step {i:02d} | Energy = {energy:.8f} | Params = {params}")
    
final_energy, final_state, final_probs = vqe_all(params)
print("\nFinal energy:", final_energy)
print("Final params:", params)

# Plot: Energy vs optimisation step
plt.figure()
plt.plot(range(len(energies)), energies, marker="o")
plt.xlabel("Step")
plt.ylabel("Energy")
plt.title("Energy vs Optimisation Step")
plt.grid(True)
plt.show()

labels = ["00", "01", "10", "11"]

#Plot: Statevector
real_parts = np.real(final_state)
imag_parts = np.imag(final_state)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8), sharex=True)
#Real part
ax1.bar(labels, real_parts)
ax1.set_title("Real Part of Statevector", fontsize=22)
ax1.set_xlabel("Basis States", fontsize=16)
ax1.set_ylabel("Real Amplitude", fontsize=16)
ax1.tick_params(axis="both", labelsize=14)

#Imag part
ax2.bar(labels, imag_parts)
ax2.set_title("Imaginary Part of Statevector", fontsize=22)
ax2.set_xlabel("Basis States", fontsize=16)
ax2.set_ylabel("Imaginary Amplitude", fontsize=16)
ax2.tick_params(axis="both", labelsize=14)

plt.tight_layout()
plt.show()

#Plot: Probabilities
plt.figure(figsize=(8, 4))
plt.bar(labels, final_probs)
plt.xlabel("Basis State")
plt.ylabel("Probability")
plt.title("Final Measurement Probabilities")
plt.grid(True)
plt.show()



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