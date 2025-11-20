#api.py
from .program import Program, current_program
from .ir import *
from .compiler import *
import pennylane as qml
from matplotlib import pyplot as plt
import numpy as np
from pprint import pformat

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

def MEASURE(kind, *wires):
    if kind not in ("state", "probs"):
        raise ValueError("MEASURE kind must be either 'state' or 'probs'.")
    if kind == "probs" and not wires:
        raise ValueError("Measure('probs', ...) expects at least one wire.")
    current_program().append(Measure(kind, wires))

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
    if graph_type not in ("probs", "statevector"):
        raise ValueError("GRAPH 'graph_type' must be 'probs' or 'statevector'.")
    results = program()
    n_states = len(results)
    n_qubits = int(np.log2(n_states))
    labels = [format(i, f'0{n_qubits}b') for i in range(n_states)]
    
    if graph_type == "probs":
        plt.figure(figsize=(10, 6))
        plt.bar(labels, results)
        plt.xlabel('Basis States')
        plt.ylabel('Probability')
        plt.title('Measurement Probabilities')
        plt.show()
        
    elif graph_type == "statevector":
        real_parts = np.real(results)
        imag_parts = np.imag(results)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))
        
        ax1.bar(labels, real_parts, color='blue')
        ax1.set_xlabel('Basis States')
        ax1.set_ylabel('Real Amplitude')
        ax1.set_title('Real Part')
        
        ax2.bar(labels, imag_parts, color='red')
        ax2.set_xlabel('Basis States')
        ax2.set_ylabel('Imaginary Amplitude')
        ax2.set_title('Imaginary Part')
        
        plt.tight_layout()
        plt.show()

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
    
    #---Rotation Gates---
    def RX(self, theta, w): 
        if not isinstance(theta, (int, float)):
            raise TypeError("RX expects a numeric angle.")
        current_program().append(Op("RX", [w], params=(theta,)))
    def RY(self, theta, w):
        if not isinstance(theta, (int, float)):
            raise TypeError("RY expects a numeric angle.")
        current_program().append(Op("RY", [w], params=(theta,)))
    def RZ(self, theta, w):
        if not isinstance(theta, (int, float)):
            raise TypeError("RZ expects a numeric angle.")
        current_program().append(Op("RZ", [w], params=(theta,)))

gate = _Gate()


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
