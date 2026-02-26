# compiler.py
import pennylane as qml
from .ir import *

PL_NAME_MAP = {
    "H": qml.Hadamard,
    "X": qml.PauliX,
    "Y": qml.PauliY,
    "Z": qml.PauliZ,
    "SWAP": qml.SWAP,
    "CNOT": qml.CNOT,
    "RX": qml.RX,
    "RY": qml.RY,
    "RZ": qml.RZ,
    "CZ": qml.CZ,
    "CY": qml.CY,
    "CRX": qml.CRX, 
    "CRY": qml.CRY,
    "CRZ": qml.CRZ,
    "CTRL": None,
    "StatePrep": qml.StatePrep,
    "BasisState": qml.BasisState,
    "SingleExcitation": qml.SingleExcitation,
    "DoubleExcitation": qml.DoubleExcitation,
    "HartreeFock": None,
}

def compile_to_pennylane(ir):
    dev = qml.device("default.qubit", wires=ir.width)

    @qml.qnode(dev)
    def circuit():
        outputs = []
        for op in ir.ops:
            if hasattr(op, "name"):
                if op.name == "CTRL":
                    gate_name = op.params[0]
                    control_wires = op.wires[:-1]
                    target_wire = op.wires[-1]
                    base_gate = PL_NAME_MAP[gate_name]
                    qml.ctrl(base_gate, control=control_wires)(target_wire)
                
                elif op.name == "StatePrep":
                    state = op.params[0]
                    qml.StatePrep(state, op.wires)
                
                elif op.name == "BasisState":
                    state = op.params[0]
                    qml.BasisState(state, wires=op.wires)
                
                elif op.name == "HartreeFock":
                    electrons = op.params[0]
                    basis = op.params[1] if len(op.params) > 1 else 'occupation_number'
                    orbitals = len(op.wires)
                    hf_state_array = qml.qchem.hf_state(electrons, orbitals, basis=basis)
                    qml.BasisState(hf_state_array, wires=op.wires)
                
                elif op.name == "DoubleExcitation":
                    theta = op.params[0]
                    qml.DoubleExcitation(theta, wires=op.wires)
                
                elif op.name == "SingleExcitation":
                    theta = op.params[0]
                    qml.SingleExcitation(theta, wires=op.wires)
                else:
                    gate = PL_NAME_MAP[op.name]
                    if op.params:
                        gate(*op.params, wires=op.wires)
                    else:
                        gate(wires=op.wires)
            else:   
                outputs.append(op)

        if not outputs:
            raise RuntimeError("No MEASURE outputs specified.")

        returns = []
        for m in outputs:
            if m.kind == "state":
                returns.append(qml.state())
            elif m.kind == "probs":
                returns.append(qml.probs(wires=m.wires))
            elif m.kind == "expval":
                if getattr(m, "operator", None) is not None:
                    returns.append(qml.expval(m.operator))
                else:
                    obs_gate = PL_NAME_MAP[m.observable]
                    returns.append(qml.expval(obs_gate(wires=m.wires)))
            elif m.kind == "density matrix":
                wires = list(range(ir.width)) if m.wires is None else list(m.wires)
                returns.append(qml.density_matrix(wires=wires))
            else:
                print(f"RuntimeError: Unsupported MEASURE kind: {m.kind}")

        return returns[0] if len(returns) == 1 else tuple(returns)

    return circuit


def compile_to_qiskit(ir, shots=None):

    try:
        from qiskit import QuantumCircuit
        from qiskit.circuit.library import Initialize
        from qiskit.quantum_info import Statevector, DensityMatrix, partial_trace, Pauli
        import numpy as _np
    except Exception as e:
        raise ImportError(
            "Qiskit backend requires qiskit installed in this interpreter. "
            "Try: python -m pip install qiskit"
        ) from e

    qc = QuantumCircuit(ir.width)

    # --- Build circuit from IR ops ---
    for node in ir.ops:
        if not hasattr(node, "name"):
            continue  # measurement handled after we build unitary

        name = node.name
        w = node.wires
        p = node.params or ()

        if name == "H":
            qc.h(w[0])
        elif name == "X":
            qc.x(w[0])
        elif name == "Y":
            qc.y(w[0])
        elif name == "Z":
            qc.z(w[0])

        elif name == "SWAP":
            qc.swap(w[0], w[1])

        elif name == "CNOT":
            qc.cx(w[0], w[1])
        elif name == "CZ":
            qc.cz(w[0], w[1])
        elif name == "CY":
            qc.cy(w[0], w[1])

        elif name == "RX":
            qc.rx(float(p[0]), w[0])
        elif name == "RY":
            qc.ry(float(p[0]), w[0])
        elif name == "RZ":
            qc.rz(float(p[0]), w[0])

        elif name == "CRX":
            qc.crx(float(p[0]), w[0], w[1])
        elif name == "CRY":
            qc.cry(float(p[0]), w[0], w[1])
        elif name == "CRZ":
            qc.crz(float(p[0]), w[0], w[1])

        elif name == "CTRL":
            # Your encoding: Op("CTRL", [*control_wires, target_wire], params=(gate_name,))
            gate_name = p[0]
            control_wires = w[:-1]
            target_wire = w[-1]

            # Build a 1-qubit base gate instruction, then control it
            tmp = QuantumCircuit(1, name=f"{gate_name}_base")
            if gate_name == "X":
                tmp.x(0)
            elif gate_name == "Y":
                tmp.y(0)
            elif gate_name == "Z":
                tmp.z(0)
            elif gate_name == "H":
                tmp.h(0)
            elif gate_name == "RX":
                raise ValueError("CTRL(RX, ...) not representable with your current CTRL encoding. "
                                 "Use CRX/CRY/CRZ for controlled rotations.")
            elif gate_name == "RY":
                raise ValueError("CTRL(RY, ...) not representable with your current CTRL encoding. "
                                 "Use CRX/CRY/CRZ for controlled rotations.")
            elif gate_name == "RZ":
                raise ValueError("CTRL(RZ, ...) not representable with your current CTRL encoding. "
                                 "Use CRX/CRY/CRZ for controlled rotations.")
            else:
                raise ValueError(f"Unsupported CTRL base gate: {gate_name}")

            base_gate = tmp.to_gate()
            cgate = base_gate.control(len(control_wires))
            qc.append(cgate, control_wires + [target_wire])

        elif name == "BasisState":
            # PennyLane BasisState expects a bitstring array/list length = wires
            bits = list(node.params[0])
            if len(bits) != len(w):
                raise ValueError("BasisState params length must match wires length")
            # Apply X to wires where bit=1 (assumes |0...0> initial)
            for bit, wire in zip(bits, w):
                if int(bit) == 1:
                    qc.x(wire)

        elif name == "StatePrep":
            # Arbitrary statevector initialization on given wires.
            state = _np.asarray(node.params[0], dtype=complex)
            init = Initialize(state)
            qc.append(init, w)

        else:
            # Skip chemistry ops as per your constraint
            if name in ("SingleExcitation","DoubleExcitation","HartreeFock"):
                raise NotImplementedError(f"{name} is not supported in Qiskit backend (chem excluded).")
            raise ValueError(f"Unsupported op for Qiskit backend: {name}")

    # --- Collect measurement intents (do NOT add qc.measure unless you want shot sampling) ---
    measures = [m for m in ir.ops if not hasattr(m, "name")]
    if not measures:
        raise RuntimeError("No MEASURE outputs specified.")

    # Helpers
    def _wire_probs_from_statevec(statevec, wires):
        # Return probs marginal over selected wires in computational basis
        # Qiskit uses little-endian convention for bitstrings; we keep consistent ordering by explicit marginalization.
        n = ir.width
        wires = list(wires)
        probs_full = _np.abs(_np.asarray(statevec.data))**2  # length 2^n

        # Build marginal by summing over unobserved qubits
        # Index bits: bit k corresponds to qubit k (little-endian)
        out_dim = 2 ** len(wires)
        out = _np.zeros(out_dim, dtype=float)
        for idx, p in enumerate(probs_full):
            out_idx = 0
            for j, q in enumerate(wires):
                bit = (idx >> q) & 1
                out_idx |= (bit << j)
            out[out_idx] += p
        return out

    def _expval_single(statevec, observable, wire):
        # observable in {"X","Y","Z","H"}
        if observable == "H":
            # Hadamard observable = H Z H = X in the computational basis
            observable = "X"
        pauli = {"X": "X", "Y": "Y", "Z": "Z"}[observable]
        # Build Pauli string on all qubits
        s = ["I"] * ir.width
        s[wire] = pauli
        P = Pauli("".join(reversed(s)))  # qiskit Pauli string is big-endian in label
        return float(_np.real(statevec.expectation_value(P)))

    def runner():
        # Use statevector simulation always; it supports all your current MEASURE kinds deterministically.
        sv = Statevector.from_instruction(qc)

        results = []
        for m in measures:
            if m.kind == "state":
                results.append(_np.asarray(sv.data))
            elif m.kind == "probs":
                if not m.wires:
                    raise ValueError("MEASURE('probs') requires wires for Qiskit backend.")
                results.append(_wire_probs_from_statevec(sv, m.wires))
            elif m.kind == "expval":
                if getattr(m, "operator", None) is not None:
                    # Your PennyLane path allows Hamiltonians; don’t implement unless you standardize operator IR.
                    raise NotImplementedError("MEASURE('expval', hamiltonian=...) not supported in Qiskit backend.")
                if not m.wires or len(m.wires) != 1:
                    raise ValueError("MEASURE('expval') expects exactly one wire in Qiskit backend.")
                results.append(_expval_single(sv, m.observable, m.wires[0]))
            elif m.kind == "density matrix":
                dm = DensityMatrix(sv)
                if m.wires is None:
                    results.append(_np.asarray(dm.data))
                else:
                    traced = partial_trace(dm, [q for q in range(ir.width) if q not in list(m.wires)])
                    results.append(_np.asarray(traced.data))
            else:
                raise ValueError(f"Unsupported MEASURE kind: {m.kind}")

        return results[0] if len(results) == 1 else tuple(results)

    # Expose the circuit too (useful for DRAW-like tooling)
    runner._qiskit_circuit = qc
    return runner

