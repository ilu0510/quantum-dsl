#api.py
from .program import Program, current_program
from .ir import *
from .compiler import *
import pennylane as qml
from matplotlib import pyplot as plt
from pennylane import numpy as np
from pprint import pformat
from pennylane import qchem

def PREPARE(n):
    if not isinstance(n, int) or n <= 0:
        raise TypeError("PREPARE expects a postive integer for number of qubits")
    return Program(width=n)

def SUPERPOSE(*wires):
    if not wires:
        raise ValueError("SUPERPOSE expects at least one wire.")
    for w in wires: 
        current_program().append(Op("H", [w]))

def ENTANGLE(a, b):
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("ENTANGLE expects two wire indices.")
    current_program().append(Op("CNOT", [a, b]))

def STATE_PREP(state, wire):
    current_program().append(Op("StatePrep", [wire], params=(state,)))

def BASIS_STATE(state, wire=None):
    if wire is None:
        wire = list(range(len(state)))
    if len(state) != len(wire):
        raise ValueError(f"State length {len(state)} must match number of wires {len(wire)}")
    current_program().append(Op("BasisState", wire, params=(state,)))

# ---Quantum Chemistry ---

def SINGLE_EXCITATION(theta, wires):
    if not isinstance(theta, (int, float)):
        raise TypeError("SINGLE_EXCITATION expects a numeric angle")
    if len(wires) != 2:
        raise ValueError("SINGLE_EXCITATION requires exactly 2 wires")
    current_program().append(Op("SingleExcitation", wires, params=(theta,)))

def DOUBLE_EXCITATION(theta, wires):
    if not isinstance(theta, (int, float)):
        raise TypeError("DOUBLE_EXCITATION expects a numeric angle")
    if len(wires) != 4:
        raise ValueError("DOUBLE_EXCITATION requires exactly 4 wires")
    current_program().append(Op("DoubleExcitation", wires, params=(theta,)))

def HARTREE_FOCK(electrons, orbitals, basis='occupation_number'):
    wires = list(range(orbitals))
    current_program().append(Op("HartreeFock", wires, params=(electrons, basis)))

def MOLECULAR_HAMILTONIAN(
    symbols,
    geometry,
    charge=0,
    mult=1,
    basis="sto-3g",
    method="dhf",
    active_electrons=None,
    active_orbitals=None,
    mapping="jordan_wigner",
    outpath=".",
    wires=None,
    args=None,
    convert_tol=1e12,  
):
    molecule = qchem.Molecule(
        symbols,
        geometry,
        charge=charge,
        mult=mult,
        basis_name=basis,  
    )

    H, n_qubits = qchem.molecular_hamiltonian(
        molecule,
        method=method,
        active_electrons=active_electrons,
        active_orbitals=active_orbitals,
        mapping=mapping,
        outpath=outpath,
        wires=wires,
        args=args,
        convert_tol=convert_tol,
    )

    return H, n_qubits

# --- Results and Visualisation ---

def MEASURE(kind, *wires, **kwargs):
    if kind not in ("state", "probs", "expval"):
        raise ValueError("MEASURE kind must be 'state', 'probs', or 'expval'.")

    # --- PROBABILITY MEASURE ---
    if kind == "probs":
        if not wires:
            raise ValueError("MEASURE('probs', ...) expects at least one wire.")
        current_program().append(Measure(kind, wires))
        return

    # --- EXPECTATION VALUE ---
    if kind == "expval":
        # Case 1: User supplied a full Hamiltonian
        hamiltonian = kwargs.get("hamiltonian")
        if hamiltonian is not None:
            # No need for wires; Hamiltonians define their own wires
            current_program().append(Measure(kind, None, operator=hamiltonian))
            return

        # Case 2: Simple observable like X, Y, Z, H
        if not wires or len(wires) != 1:
            raise ValueError("MEASURE('expval', wire) expects exactly one wire when no Hamiltonian is provided.")
        
        observable = kwargs.get("observable")
        if observable not in ("X", "Y", "Z", "H"):
            raise ValueError("MEASURE('expval', ...) requires observable='X', 'Y', 'Z', or 'H'.")
        
        current_program().append(Measure(kind, wires, observable=observable))
        return

    # --- STATEVECTOR MEASURE ---
    if kind == "state":
        current_program().append(Measure(kind, wires))
        return    

def DRAW(circ, draw_type="ascii"):
    if draw_type not in ("ascii", "diagram"):
        raise ValueError("DRAW 'draw_type' must be 'ascii' or 'diagram'.")
    if hasattr(circ, 'compile'):
        circuit = circ._compiled
        if circuit is None:
            circ.compile()
            circuit = circ._compiled
    else:
        circuit = circ
    
    if draw_type == "ascii":
        print(qml.draw(circuit)())
    elif draw_type == "diagram":
        fig, ax = qml.draw_mpl(circuit)()
        plt.show()
        return fig

def GRAPH(program, graph_type="probs"):

    if graph_type not in ("probs", "statevector", "expval"):
        raise ValueError("GRAPH 'graph_type' must be 'probs', 'statevector' or 'expval'.")


    results = program()    
    last_op = program.ir.ops[-1]
    kind = last_op.kind   

    if graph_type == "expval":
        if kind != "expval":
            raise ValueError("GRAPH('expval') requires MEASURE('expval') in the program.")

        # Make results into a 1D numpy array, even if it's a scalar or tuple
        values = np.atleast_1d(np.array(results, dtype=float))

        # Simple labels: expval_0, expval_1, ...
        if values.size == 1:
            labels = ["expval"]
        else:
            labels = [f"expval_{i}" for i in range(values.size)]

        plt.figure(figsize=(6, 4))
        plt.bar(labels, values)

        plt.xlabel('Observable', fontsize=14)
        plt.ylabel('Expectation value', fontsize=14)
        plt.title('Expectation Values', fontsize=18)

        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)

        plt.tight_layout()
        plt.show()
        return


    results = np.asarray(results)
    n_states = len(results)
    n_qubits = int(np.log2(n_states))
    labels = [format(i, f'0{n_qubits}b') for i in range(n_states)]

    if graph_type == "probs":
        if kind == "state":
            probs = np.abs(results) ** 2
        elif kind == "probs":
            probs = results
        else:
            raise ValueError("GRAPH(probs) requires MEASURE('state') or MEASURE('probs').")

        plt.figure(figsize=(12, 6))
        plt.bar(labels, probs)

        plt.xlabel('Basis States', fontsize=14)
        plt.ylabel('Probability', fontsize=14)
        plt.title('Measurement Probabilities', fontsize=18)

        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)

        plt.tight_layout()
        plt.show()
        return

    if graph_type == "statevector":

        # Cannot plot statevector unless user measured 'state'
        if kind != "state":
            raise ValueError("GRAPH('statevector') requires MEASURE('state') in the program.")

        real_parts = np.real(results)
        imag_parts = np.imag(results)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7))

        # --- Real part ---
        ax1.bar(labels, real_parts, color='blue')
        ax1.set_xlabel('Basis States', fontsize=14)
        ax1.set_ylabel('Real Amplitude', fontsize=14)
        ax1.set_title('Real Part of Statevector', fontsize=18)
        ax1.tick_params(axis='both', labelsize=12)

        # --- Imag part ---
        ax2.bar(labels, imag_parts, color='red')
        ax2.set_xlabel('Basis States', fontsize=14)
        ax2.set_ylabel('Imaginary Amplitude', fontsize=14)
        ax2.set_title('Imaginary Part of Statevector', fontsize=18)
        ax2.tick_params(axis='both', labelsize=12)

        plt.tight_layout()
        plt.show()
        return


# ---Bell States---
def BELL_PHI_PLUS(a, b):
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("BELL_PHI_PLUS expects two integer wires.")
    current_program().append(Op("H", [a]))
    ENTANGLE(a, b)

def BELL_PHI_MINUS(a, b):
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("BELL_PHI_MINUS expects two integer wires.")
    current_program().append(Op("H", [a]))
    ENTANGLE(a, b)
    current_program().append(Op("Z", [b]))

def BELL_PSI_PLUS(a, b):
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("BELL_PSI_PLUS expects two integer wires.")
    current_program().append(Op("H", [a]))
    ENTANGLE(a, b)
    current_program().append(Op("X", [b]))

def BELL_PSI_MINUS(a, b):
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("BELL_PSI_MINUS expects two integer wires.")
    current_program().append(Op("H", [a]))
    ENTANGLE(a, b)
    current_program().append(Op("Z", [b]))
    current_program().append(Op("X", [b]))

def _is_numeric(x):
    return isinstance(x, (int, float, np.number)) or hasattr(x, "__array__")

class _Gate:

    #---Single Qubit Gtaes---
    def H(self, *wires): 
        if not wires:
            raise ValueError("gate.H expects at least one wire.")
        for w in wires: 
            current_program().append(Op("H", [w]))
    def X(self, *wires): 
        if not wires:
            raise ValueError("gate.X expects at least one wire.")
        for w in wires:
            current_program().append(Op("X", [w]))
    def Y(self, *wires):
        if not wires:
            raise ValueError("gate.Y expects at least one wire.") 
        for w in wires:
            current_program().append(Op("Y", [w]))
    def Z(self, *wires): 
        if not wires:
            raise ValueError("gate.Z expects at least one wire.")
        for w in wires:
            current_program().append(Op("Z", [w]))

    def SWAP(self, *pairs):
        if not pairs:
            raise ValueError("gate.SWAP expects at least one (wire_a, wire_b) pair.")
        for a, b in pairs:
            current_program().append(Op("SWAP", [a, b]))
    
    #---Rotation Gates---
    def RX(self, theta, w):
        if not _is_numeric(theta):
            raise TypeError("RX expects a numeric angle.")
        current_program().append(Op("RX", [w], params=(theta,)))
    def RY(self, theta, w):
        if not _is_numeric(theta):
            raise TypeError("RY expects a numeric angle.")
        current_program().append(Op("RY", [w], params=(theta,)))
    def RZ(self, theta, w):
        if not _is_numeric(theta):
            raise TypeError("RZ expects a numeric angle.")
        current_program().append(Op("RZ", [w], params=(theta,)))

    #---Modifying the CNOT, CZ, CY gates so it can take in tuples---
    def CNOT(self, *pairs):
        if not pairs:
            raise ValueError("gate.CNOT expects at least one (control, target) tuple.")
        for c, t in pairs:
            current_program().append(Op("CNOT", [c, t]))

    def CZ(self, *pairs):
        if not pairs:
            raise ValueError("gate.CZ expects at least one (control, target) tuple.")
        for c, t in pairs:
            current_program().append(Op("CZ", [c, t]))

    def CY(self, *pairs):
        if not pairs:
            raise ValueError("gate.CY expects at least one (control, target) tuple.")
        for c, t in pairs:
            current_program().append(Op("CY", [c, t]))

    #---Controlled Gates---
    def CTRL(self, gate_name, control_wires, target_wire):
        if not isinstance(control_wires, list):
            control_wires = [control_wires]
        if not control_wires:
            raise ValueError("gate.CTRL expects at least one control wire.")
        current_program().append(Op("CTRL", [*control_wires, target_wire], params=(gate_name,)))

        #---Controlled Rotation Gates---
    def CRX(self, theta, control, target):
        if not _is_numeric(theta):
            raise TypeError("CRX expects a numeric angle.")
        current_program().append(Op("CRX", [control, target], params=(theta,)))

    def CRY(self, theta, control, target):
        if not _is_numeric(theta):
            raise TypeError("CRY expects a numeric angle.")
        current_program().append(Op("CRY", [control, target], params=(theta,)))

    def CRZ(self, theta, control, target):
        if not _is_numeric(theta):
            raise TypeError("CRZ expects a numeric angle.")
        current_program().append(Op("CRZ", [control, target], params=(theta,)))

    

gate = _Gate()

# --- Observables ---
class _Obs:
    def X(self, w): return qml.PauliX(w)
    def Y(self, w): return qml.PauliY(w)
    def Z(self, w): return qml.PauliZ(w)
    def H(self, w): return qml.Hadamard(w)

obs = _Obs()


# ---BLOCKS---

_BLOCKS = {}

def BLOCK(name=None):
    if not isinstance(name, str) or name.strip() == "":
        raise TypeError("@BLOCK requires a non-empty string name")
    def _register(fn):
        if name in _BLOCKS:
            print(f"RuntimeError: BLOCK {name} already exists.")
            return fn
        _BLOCKS[name] = fn
        return fn
    return _register

def USE(name, *args, **kwargs): 
    fn = _BLOCKS.get(name)
    if fn is None:
        raise ValueError(f"Unknown BLOCK {name}")
    fn(*args, **kwargs)

# --- Optimise --- 

def OPTIMISE(
    energy_fn,
    init_params,
    steps=30,
    stepsize=0.2,
    eps=1e-6,
    history=False,
    graph=False,
):

    params = np.array(init_params, dtype=float)
    if params.ndim == 0:
        params = params.reshape((1,))

    energies = []

    def central_diff(f, x):
        g = np.zeros_like(x)
        for i in range(len(x)):
            x_fwd = x.copy(); x_fwd[i] += eps
            x_bwd = x.copy(); x_bwd[i] -= eps
            g[i] = (f(x_fwd) - f(x_bwd)) / (2 * eps)
        return g

    for s in range(steps):
        E = float(energy_fn(params))
        energies.append(E)

        if history:
            print(f"Step {s:3d} | Energy = {E: .6f} | Params = {params}")

        g = central_diff(energy_fn, params)
        params = params - stepsize * g

    final_energy = float(energy_fn(params))

    if graph:
        plt.plot(range(len(energies)), energies)
        plt.xlabel("Step")
        plt.ylabel("Energy")
        plt.title("Energy vs Optimisation Step")
        plt.show()

    return params, final_energy


# --- Inspect IR ---

def INSPECT_IR(program, format="dict"):
    if format not in ("dict", "text"):
        raise ValueError("INSPECT_IR 'format' must be 'dict' or 'text'.")
    if format == "dict":
        ir_data = {
            "qubits": program.ir.width,
            "operations": [
                {
                    "op": op.name if hasattr(op, "name") else "MEASURE",
                    "wires": op.wires,
                    "params": list(op.params) if hasattr(op, "params") else [],
                    "kind": op.kind if hasattr(op, "kind") else None
                }
                for op in program.ir.ops
            ]
        }
        return pformat(ir_data, indent=2, sort_dicts=False) 
    elif format == "text":
        lines = []
        lines.append(f"Qubits: {program.ir.width}")
        lines.append("\nInstructions:")
        for i, op in enumerate(program.ir.ops, 1):
            if hasattr(op, "name"):
                if op.params:
                    lines.append(f"  {i}. {op.name}(wires={op.wires}, params={op.params})")
                else:
                    lines.append(f"  {i}. {op.name}(wires={op.wires})")
            else:
                lines.append(f"  {i}. MEASURE(kind='{op.kind}', wires={op.wires})")
        return "\n".join(lines)
