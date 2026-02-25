# inspect_ir_examples.py
# Purpose: Build example circuits and verify INSPECT_IR output & JSON export.
# No execution, no plotting.

from dsl import *
from pennylane import numpy as np

def show(program, name: str, as_json: bool = True):
    print("\n" + "=" * 80)
    print(f"EXAMPLE: {name}")
    print("=" * 80)

    if as_json:
        fields, path = INSPECT_IR(program, format="dict", name=name, print_output=True)
        print(f"\n[JSON written] {path}")
    else:
        INSPECT_IR(program, format="text", print_output=True)


# ---------------------------------------------------------------------
# 1) Bell state (with BLOCK provenance)
# ---------------------------------------------------------------------
def example_bell():
    with PREPARE(2) as p:
        @BLOCK("bell")
        def bell():
            SUPERPOSE(0)
            ENTANGLE(0, 1)

        USE("bell")
        MEASURE("probs", 0, 1)

    show(p, "Bell state (BLOCK + probs)")


# ---------------------------------------------------------------------
# 2) Deutsch–Jozsa 2-bit (multiple oracles)
#   NOTE: We only build programs and inspect IR; we do NOT execute p().
# ---------------------------------------------------------------------
def register_dj_blocks():
    @BLOCK("oracle_const0")
    def oracle_const0(x0, x1, a):
        return

    @BLOCK("oracle_const1")
    def oracle_const1(x0, x1, a):
        gate.X(a)

    @BLOCK("oracle_x0")
    def oracle_x0(x0, x1, a):
        gate.CNOT((x0, a))

    @BLOCK("oracle_x1")
    def oracle_x1(x0, x1, a):
        gate.CNOT((x1, a))

    @BLOCK("oracle_x0_x1")
    def oracle_x0_x1(x0, x1, a):
        gate.CNOT((x0, a), (x1, a))

    @BLOCK("dj_2bit")
    def dj_2bit(oracle, x0, x1, a):
        gate.X(a)
        SUPERPOSE(a, x0, x1)
        USE(oracle, x0=x0, x1=x1, a=a)
        SUPERPOSE(x0, x1)
        MEASURE("probs", x0, x1)

def example_deutsch_jozsa():
    register_dj_blocks()

    oracles = [
        "oracle_const0",
        "oracle_const1",
        "oracle_x0",
        "oracle_x1",
        "oracle_x0_x1",
    ]

    for oracle_name in oracles:
        with PREPARE(3) as p:
            USE("dj_2bit", oracle=oracle_name, x0=0, x1=1, a=2)
        show(p, f"Deutsch–Jozsa 2-bit (oracle={oracle_name})")


# ---------------------------------------------------------------------
# 3) Grover (3 qubits) – oracle + diffusion blocks, repeated use
# ---------------------------------------------------------------------
def register_grover_blocks():
    @BLOCK("oracle_grover")
    def oracle_grover():
        gate.X(0, 2)
        gate.CTRL("Z", [0, 2], 1)
        gate.X(0, 2)

    @BLOCK("diffusion")
    def diffusion():
        SUPERPOSE(0, 1, 2)
        gate.X(0, 1, 2)
        gate.CTRL("Z", [0, 1], 2)
        gate.X(0, 1, 2)
        SUPERPOSE(0, 1, 2)

def example_grover():
    register_grover_blocks()

    with PREPARE(3) as p:
        SUPERPOSE(0, 1, 2)
        USE("oracle_grover")
        USE("diffusion")
        USE("oracle_grover")
        USE("diffusion")
        MEASURE("probs", 0, 1, 2)

    show(p, "Grover (3 qubits, repeated BLOCK expansion)")


# ---------------------------------------------------------------------
# 4) Quantum Fourier Transform (4 qubits)
# ---------------------------------------------------------------------
def register_qft_block():
    @BLOCK("qft")
    def qft(wires):
        n = len(wires)
        for i in range(n):
            SUPERPOSE(wires[i])
            for j in range(i + 1, n):
                angle = np.pi / (2 ** (j - i))
                gate.CRZ(angle, wires[j], wires[i])

        # swap ends
        for i in range(n // 2):
            gate.SWAP((wires[i], wires[n - 1 - i]))

def example_qft():
    register_qft_block()

    with PREPARE(4) as p:
        gate.X(0, 1, 2)
        USE("qft", [0, 1, 2, 3])
        MEASURE("state")

    show(p, "QFT (4 qubits, rotations + swaps + state measure)")


# ---------------------------------------------------------------------
# 5) Quantum teleportation (3 qubits)
#   NOTE: fix CZ usage: gate.CZ((control, target))
# ---------------------------------------------------------------------
def register_teleport_block():
    @BLOCK("teleport")
    def teleport(state):
        STATE_PREP(state, 0)
        BELL_PHI_PLUS(1, 2)
        ENTANGLE(0, 1)
        SUPERPOSE(0)
        ENTANGLE(1, 2)
        gate.CZ((0, 2))  # <-- tuple, not list

def example_teleport():
    register_teleport_block()

    state_to_teleport = np.array([1 / np.sqrt(2), 1 / np.sqrt(2)])

    with PREPARE(3) as p:
        USE("teleport", state=state_to_teleport)
        MEASURE("density matrix", 2)

    show(p, "Teleportation (StatePrep + Bell + density matrix on wire 2)")


# ---------------------------------------------------------------------
# 6) VQE (IR focus only)
#   We do NOT run OPTIMISE (that executes circuits + plots).
#   We just build:
#     - an ansatz circuit
#     - an expval measurement with a Hamiltonian operator
# ---------------------------------------------------------------------
def register_vqe_block():
    @BLOCK("vqe_ansatz")
    def vqe_ansatz(params):
        theta0 = params[0]
        gate.RY(theta0, 0)
        gate.CNOT((0, 1))

def example_vqe():
    register_vqe_block()

    # Example Hamiltonian (operator intent)
    H = (obs.X(0) @ obs.X(1))

    with PREPARE(2) as p:
        USE("vqe_ansatz", [0.1])
        MEASURE("expval", hamiltonian=H)

    show(p, "VQE (ansatz + expval Hamiltonian)")

    # Also inspect a 'state' measurement variant
    with PREPARE(2) as p_state:
        USE("vqe_ansatz", [0.1])
        MEASURE("state")

    show(p_state, "VQE (ansatz + state measurement)")


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
if __name__ == "__main__":
    example_bell()
    example_deutsch_jozsa()
    example_grover()
    example_qft()
    example_teleport()
    example_vqe()