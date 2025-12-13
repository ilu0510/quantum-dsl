import pennylane as qml
from pennylane import numpy as np

dev = qml.device("default.qubit", wires = 2)

hami = qml.PauliZ(0) @ qml.PauliZ(1)

@qml.qnode(dev)
def vqe_circuit(params):
    qml.RY(params[0], wires = 0)
    qml.RY(params[1], wires = 1)
    qml.CNOT(wires=[0,1])

    return qml.expval(hami)

test_params = np.array([0.0, 0.0], requires_grad=True)
print("Energy at params", test_params, "=", vqe_circuit(test_params))

def cost(params):
    """VQE cost function: expectation value of H."""
    return vqe_circuit(params)

# Initial parameters (random or chosen)
params = np.random.uniform(0, 2 * np.pi, 2, requires_grad=True)

opt = qml.GradientDescentOptimizer(stepsize=0.4)
num_steps = 50

print("Initial params:", params)
print("Initial energy:", cost(params))

for n in range(num_steps):
    params, energy = opt.step_and_cost(cost, params)

    if n % 10 == 0:
        print(f"Step {n:2d} | Energy = {energy:.6f} | Params = {params}")

print("\nOptimisation finished.")
print("Final energy:", cost(params))
print("Final params:", params)




