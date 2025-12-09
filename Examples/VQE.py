import pennylane as qml
import numpy as np
from pennylane.qchem import Molecule, molecular_hamiltonian

# 1. Define molecule
symbols = ["H", "H"]
coordinates = np.array(
    [
        [-0.70108983, 0.0, 0.0],
        [ 0.70108983, 0.0, 0.0],
    ]
)

molecule = Molecule(
    symbols=symbols,
    coordinates=coordinates,  
    charge=0,
    mult=1,              
    basis_name="sto-3g",   
)

H, num_qubits = molecular_hamiltonian(molecule)

print("Number of qubits:", num_qubits)
print("Hamiltonian terms:", len(H.terms()[0]))

dev = qml.device("default.qubit", wires=num_qubits)

# --- 4. Hartree–Fock reference state ---
electrons = molecule.n_electrons  
hf_state = qml.qchem.hf_state(electrons, num_qubits)
print("HF bitstring:", hf_state)

@qml.qnode(dev)
def vqe_circuit(theta):
    qml.BasisState(hf_state, wires=range(num_qubits))
    qml.DoubleExcitation(theta[0], wires=[0, 1, 2, 3])

    return qml.expval(H)

def energy(theta_scalar):
    # wrap scalar into length-1 array
    return vqe_circuit(np.array([theta_scalar], dtype=float))


# --- 6. Optimize ---

def finite_diff_grad(theta_scalar, h=1e-3):
    # central difference
    return (energy(theta_scalar + h) - energy(theta_scalar - h)) / (2 * h)

theta = 0.0                      # initial value
lr = 0.4                         # learning rate
max_steps = 50

for n in range(max_steps):
    e = energy(theta)
    g = finite_diff_grad(theta)

    theta_new = theta - lr * g
    print(f"Step {n:2d} | E = {e:.8f} Ha | theta = {theta:.6f} | grad ≈ {g:.6f}")

    if abs(theta_new - theta) < 1e-6:
        theta = theta_new
        break

    theta = theta_new

final_energy = energy(theta)
print("\nOptimized theta (FD):", theta)
print("Optimized energy (FD):", final_energy)
