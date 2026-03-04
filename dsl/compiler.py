# # compiler.py
# import pennylane as qml
# from .ir import *

# PL_NAME_MAP = {
#     "H": qml.Hadamard,
#     "X": qml.PauliX,
#     "Y": qml.PauliY,
#     "Z": qml.PauliZ,
#     "SWAP": qml.SWAP,
#     "CNOT": qml.CNOT,
#     "RX": qml.RX,
#     "RY": qml.RY,
#     "RZ": qml.RZ,
#     "CZ": qml.CZ,
#     "CY": qml.CY,
#     "CRX": qml.CRX, 
#     "CRY": qml.CRY,
#     "CRZ": qml.CRZ,
#     "CTRL": None,
#     "StatePrep": qml.StatePrep,
#     "BasisState": qml.BasisState,
#     "SingleExcitation": qml.SingleExcitation,
#     "DoubleExcitation": qml.DoubleExcitation,
#     "HartreeFock": None,
# }

# def _pl_operator_from_pauli_sum(spec):
#     # spec: {"type":"pauli_sum","n_qubits":N,"terms":[{"coeff":c,"ops":{"0":"X","1":"Z"}}...]}
#     if spec.get("type") != "pauli_sum":
#         raise ValueError(f"Unsupported Hamiltonian spec type: {spec.get('type')}")

#     terms = []
#     for t in spec["terms"]:
#         coeff = float(t["coeff"])
#         ops = t["ops"]  # dict wire(str)->"X"/"Y"/"Z"
#         op = None
#         # Build tensor product in a stable order
#         for wire_str in sorted(ops.keys(), key=lambda s: int(s)):
#             w = int(wire_str)
#             p = ops[wire_str]
#             if p == "X":
#                 piece = qml.PauliX(w)
#             elif p == "Y":
#                 piece = qml.PauliY(w)
#             elif p == "Z":
#                 piece = qml.PauliZ(w)
#             else:
#                 raise ValueError(f"Unsupported Pauli in spec: {p}")

#             op = piece if op is None else (op @ piece)

#         if op is None:
#             # Identity term: PennyLane doesn't have a clean "I" op for expval;
#             # but you can treat it as coeff * I => constant shift.
#             # For now, disallow identity-only term.
#             raise ValueError("Identity-only Hamiltonian terms are not supported in this minimal implementation.")

#         terms.append(coeff * op)

#     # Sum terms
#     H = terms[0]
#     for k in range(1, len(terms)):
#         H = H + terms[k]
#     return H


# def _qiskit_sparsepauli_from_pauli_sum(spec, n_qubits):
#     # Build SparsePauliOp from pauli-sum spec (Qiskit Pauli labels are big-endian)
#     from qiskit.quantum_info import SparsePauliOp
#     import numpy as _np

#     if spec.get("type") != "pauli_sum":
#         raise ValueError(f"Unsupported Hamiltonian spec type: {spec.get('type')}")

#     labels = []
#     coeffs = []
#     for t in spec["terms"]:
#         coeff = float(t["coeff"])
#         ops = {int(k): v for k, v in t["ops"].items()}  # wire(int)->"X"/"Y"/"Z"
#         # Start with all identities in little-endian, then reverse for big-endian label
#         chars = ["I"] * n_qubits
#         for w, p in ops.items():
#             chars[w] = p
#         label_big_endian = "".join(reversed(chars))
#         labels.append(label_big_endian)
#         coeffs.append(coeff)

#     return SparsePauliOp(labels, coeffs=_np.array(coeffs, dtype=float))

# def compile_to_pennylane(ir):
#     dev = qml.device("default.qubit", wires=ir.width)

#     @qml.qnode(dev)
#     def circuit():
#         outputs = []
#         for op in ir.ops:
#             if hasattr(op, "name"):
#                 if op.name == "CTRL":
#                     gate_name = op.params[0]
#                     control_wires = op.wires[:-1]
#                     target_wire = op.wires[-1]
#                     base_gate = PL_NAME_MAP[gate_name]
#                     qml.ctrl(base_gate, control=control_wires)(target_wire)
                
#                 elif op.name == "StatePrep":
#                     state = op.params[0]
#                     qml.StatePrep(state, op.wires)
                
#                 elif op.name == "BasisState":
#                     state = op.params[0]
#                     qml.BasisState(state, wires=op.wires)
                
#                 elif op.name == "HartreeFock":
#                     electrons = op.params[0]
#                     basis = op.params[1] if len(op.params) > 1 else 'occupation_number'
#                     orbitals = len(op.wires)
#                     hf_state_array = qml.qchem.hf_state(electrons, orbitals, basis=basis)
#                     qml.BasisState(hf_state_array, wires=op.wires)
                
#                 elif op.name == "DoubleExcitation":
#                     theta = op.params[0]
#                     qml.DoubleExcitation(theta, wires=op.wires)
                
#                 elif op.name == "SingleExcitation":
#                     theta = op.params[0]
#                     qml.SingleExcitation(theta, wires=op.wires)
#                 else:
#                     gate = PL_NAME_MAP[op.name]
#                     if op.params:
#                         gate(*op.params, wires=op.wires)
#                     else:
#                         gate(wires=op.wires)
#             else:   
#                 outputs.append(op)

#         if not outputs:
#             raise RuntimeError("No MEASURE outputs specified.")

#         returns = []
#         for m in outputs:
#             if m.kind == "state":
#                 returns.append(qml.state())
#             elif m.kind == "probs":
#                 returns.append(qml.probs(wires=m.wires))
#             elif m.kind == "expval":
#                 if getattr(m, "hamiltonian_spec", None) is not None:
#                     H = _pl_operator_from_pauli_sum(m.hamiltonian_spec)
#                     returns.append(qml.expval(H))
#                 else:
#                     obs_gate = PL_NAME_MAP[m.observable]
#                     returns.append(qml.expval(obs_gate(wires=m.wires)))
#             elif m.kind == "density matrix":
#                 wires = list(range(ir.width)) if m.wires is None else list(m.wires)
#                 returns.append(qml.density_matrix(wires=wires))
#             else:
#                 print(f"RuntimeError: Unsupported MEASURE kind: {m.kind}")

#         return returns[0] if len(returns) == 1 else tuple(returns)

#     return circuit


# def compile_to_qiskit(ir, shots=None):

#     try:
#         from qiskit import QuantumCircuit
#         from qiskit.circuit.library import Initialize
#         from qiskit.quantum_info import Statevector, DensityMatrix, partial_trace, Pauli
#         import numpy as _np
#     except Exception as e:
#         raise ImportError(
#             "Qiskit backend requires qiskit installed in this interpreter. "
#             "Try: python -m pip install qiskit"
#         ) from e

#     qc = QuantumCircuit(ir.width)

#     # --- Build circuit from IR ops ---
#     for node in ir.ops:
#         if not hasattr(node, "name"):
#             continue 

#         name = node.name
#         w = node.wires
#         p = node.params or ()

#         if name == "H":
#             qc.h(w[0])
#         elif name == "X":
#             qc.x(w[0])
#         elif name == "Y":
#             qc.y(w[0])
#         elif name == "Z":
#             qc.z(w[0])

#         elif name == "SWAP":
#             qc.swap(w[0], w[1])

#         elif name == "CNOT":
#             qc.cx(w[0], w[1])
#         elif name == "CZ":
#             qc.cz(w[0], w[1])
#         elif name == "CY":
#             qc.cy(w[0], w[1])

#         elif name == "RX":
#             qc.rx(float(p[0]), w[0])
#         elif name == "RY":
#             qc.ry(float(p[0]), w[0])
#         elif name == "RZ":
#             qc.rz(float(p[0]), w[0])

#         elif name == "CRX":
#             qc.crx(float(p[0]), w[0], w[1])
#         elif name == "CRY":
#             qc.cry(float(p[0]), w[0], w[1])
#         elif name == "CRZ":
#             qc.crz(float(p[0]), w[0], w[1])

#         elif name == "CTRL":
#             gate_name = p[0]
#             control_wires = w[:-1]
#             target_wire = w[-1]

#             tmp = QuantumCircuit(1, name=f"{gate_name}_base")
#             if gate_name == "X":
#                 tmp.x(0)
#             elif gate_name == "Y":
#                 tmp.y(0)
#             elif gate_name == "Z":
#                 tmp.z(0)
#             elif gate_name == "H":
#                 tmp.h(0)
#             elif gate_name == "RX":
#                 raise ValueError("CTRL(RX, ...) not representable with your current CTRL encoding. "
#                                  "Use CRX/CRY/CRZ for controlled rotations.")
#             elif gate_name == "RY":
#                 raise ValueError("CTRL(RY, ...) not representable with your current CTRL encoding. "
#                                  "Use CRX/CRY/CRZ for controlled rotations.")
#             elif gate_name == "RZ":
#                 raise ValueError("CTRL(RZ, ...) not representable with your current CTRL encoding. "
#                                  "Use CRX/CRY/CRZ for controlled rotations.")
#             else:
#                 raise ValueError(f"Unsupported CTRL base gate: {gate_name}")

#             base_gate = tmp.to_gate()
#             cgate = base_gate.control(len(control_wires))
#             qc.append(cgate, control_wires + [target_wire])

#         elif name == "BasisState":
#             bits = list(node.params[0])
#             if len(bits) != len(w):
#                 raise ValueError("BasisState params length must match wires length")
#             # Apply X to wires where bit=1 (assumes |0...0> initial)
#             for bit, wire in zip(bits, w):
#                 if int(bit) == 1:
#                     qc.x(wire)

#         elif name == "StatePrep":
#             state = _np.asarray(node.params[0], dtype=complex)
#             init = Initialize(state)
#             qc.append(init, w)

#         else:
#             if name in ("SingleExcitation","DoubleExcitation","HartreeFock"):
#                 raise NotImplementedError(f"{name} is not supported in Qiskit backend (chem excluded).")
#             raise ValueError(f"Unsupported op for Qiskit backend: {name}")

#     measures = [m for m in ir.ops if not hasattr(m, "name")]
#     if not measures:
#         raise RuntimeError("No MEASURE outputs specified.")

#     # Helpers
#     def _wire_probs_from_statevec(statevec, wires):
#         n = ir.width
#         wires = list(wires)
#         probs_full = _np.abs(_np.asarray(statevec.data))**2  # length 2^n

#         out_dim = 2 ** len(wires)
#         out = _np.zeros(out_dim, dtype=float)
#         for idx, p in enumerate(probs_full):
#             out_idx = 0
#             for j, q in enumerate(wires):
#                 bit = (idx >> q) & 1
#                 out_idx |= (bit << j)
#             out[out_idx] += p
#         return out

#     def _expval_single(statevec, observable, wire):
#         if observable in ("X", "Y", "Z"):
#             pauli = {"X": "X", "Y": "Y", "Z": "Z"}[observable]
#             s = ["I"] * ir.width
#             s[wire] = pauli
#             P = Pauli("".join(reversed(s)))
#             return float(_np.real(statevec.expectation_value(P)))

#         if observable == "H":
#             Hmat = (1.0 / _np.sqrt(2.0)) * _np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex)

#             op = _np.array([[1.0 + 0j]])
#             for q in range(ir.width):
#                 op = _np.kron(op, Hmat if q == wire else _np.eye(2, dtype=complex))

#             psi = _np.asarray(statevec.data, dtype=complex)
#             expval = _np.vdot(psi, op @ psi)  # <psi|O|psi>
#             return float(_np.real(expval))

#         raise ValueError(f"Unsupported observable: {observable}")

#     def runner():
#         sv = Statevector.from_instruction(qc)

#         results = []
#         for m in measures:
#             if m.kind == "state":
#                 results.append(_np.asarray(sv.data))
#             elif m.kind == "probs":
#                 if not m.wires:
#                     raise ValueError("MEASURE('probs') requires wires for Qiskit backend.")
#                 results.append(_wire_probs_from_statevec(sv, m.wires))
#             elif m.kind == "expval":
#                 if getattr(m, "hamiltonian_spec", None) is not None:
#                     H = _qiskit_sparsepauli_from_pauli_sum(m.hamiltonian_spec, n_qubits=ir.width)
#                     results.append(float(_np.real(sv.expectation_value(H))))
#                 else:
#                     if not m.wires or len(m.wires) != 1:
#                         raise ValueError("MEASURE('expval') expects exactly one wire in Qiskit backend when no Hamiltonian is provided.")
#                     results.append(_expval_single(sv, m.observable, m.wires[0]))
#                 if not m.wires or len(m.wires) != 1:
#                     raise ValueError("MEASURE('expval') expects exactly one wire in Qiskit backend.")
#                 results.append(_expval_single(sv, m.observable, m.wires[0]))
#             elif m.kind == "density matrix":
#                 dm = DensityMatrix(sv)
#                 if m.wires is None:
#                     results.append(_np.asarray(dm.data))
#                 else:
#                     traced = partial_trace(dm, [q for q in range(ir.width) if q not in list(m.wires)])
#                     results.append(_np.asarray(traced.data))
#             else:
#                 raise ValueError(f"Unsupported MEASURE kind: {m.kind}")

#         return results[0] if len(results) == 1 else tuple(results)

#     runner._qiskit_circuit = qc
#     return runner


# compiler.py
import pennylane as qml
from .ir import *

# -------------------------------
# PennyLane gate name mapping
# -------------------------------
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
    "CTRL": None,  # handled specially
    "StatePrep": qml.StatePrep,
    "BasisState": qml.BasisState,
    "SingleExcitation": qml.SingleExcitation,
    "DoubleExcitation": qml.DoubleExcitation,
    "HartreeFock": None,  # handled specially
}

# -------------------------------
# Hamiltonian helpers
# -------------------------------
def _pl_operator_from_pauli_sum(spec: dict):
    """
    spec format:
      {"type":"pauli_sum","n_qubits":N,
       "terms":[{"coeff":c,"ops":{"0":"X","1":"Z"}} ...]}
    """
    if spec.get("type") != "pauli_sum":
        raise ValueError(f"Unsupported Hamiltonian spec type: {spec.get('type')}")

    terms = []
    for t in spec.get("terms", []):
        coeff = float(t["coeff"])
        ops = t["ops"]  # dict wire(str)->"X"/"Y"/"Z"
        op = None

        for wire_str in sorted(ops.keys(), key=lambda s: int(s)):
            w = int(wire_str)
            p = ops[wire_str]
            if p == "X":
                piece = qml.PauliX(w)
            elif p == "Y":
                piece = qml.PauliY(w)
            elif p == "Z":
                piece = qml.PauliZ(w)
            else:
                raise ValueError(f"Unsupported Pauli in spec: {p}")

            op = piece if op is None else (op @ piece)

        if op is None:
            # Identity-only term: skip for now (or implement constant shift if you want)
            raise ValueError(
                "Identity-only Hamiltonian terms are not supported in this minimal implementation."
            )

        terms.append(coeff * op)

    if not terms:
        raise ValueError("Empty Hamiltonian spec terms.")

    H = terms[0]
    for k in range(1, len(terms)):
        H = H + terms[k]
    return H


def _qiskit_sparsepauli_from_pauli_sum(spec: dict, n_qubits: int):
    """
    Build Qiskit's SparsePauliOp from pauli-sum spec.
    Qiskit Pauli labels are big-endian.
    """
    from qiskit.quantum_info import SparsePauliOp
    import numpy as _np

    if spec.get("type") != "pauli_sum":
        raise ValueError(f"Unsupported Hamiltonian spec type: {spec.get('type')}")

    labels = []
    coeffs = []

    for t in spec.get("terms", []):
        coeff = float(t["coeff"])
        ops = {int(k): v for k, v in t["ops"].items()}  # wire(int)->"X"/"Y"/"Z"

        chars = ["I"] * n_qubits  # little-endian indexing here
        for w, p in ops.items():
            if p not in ("X", "Y", "Z", "I"):
                raise ValueError(f"Unsupported Pauli in spec: {p}")
            chars[w] = p

        label_big_endian = "".join(reversed(chars))
        labels.append(label_big_endian)
        coeffs.append(coeff)

    if not labels:
        raise ValueError("Empty Hamiltonian spec terms.")

    return SparsePauliOp(labels, coeffs=_np.array(coeffs, dtype=float))


# -------------------------------
# PennyLane compiler
# -------------------------------
def compile_to_pennylane(ir: IRProgram):
    dev = qml.device("default.qubit", wires=ir.width)

    @qml.qnode(dev)
    def circuit():
        outputs = []

        for op in ir.ops:
            if hasattr(op, "name"):
                # ----- Ops -----
                if op.name == "CTRL":
                    gate_name = op.params[0]
                    control_wires = op.wires[:-1]
                    target_wire = op.wires[-1]
                    base_gate = PL_NAME_MAP.get(gate_name)
                    if base_gate is None:
                        raise ValueError(f"Unsupported CTRL base gate for PennyLane: {gate_name}")
                    qml.ctrl(base_gate, control=control_wires)(target_wire)

                elif op.name == "StatePrep":
                    state = op.params[0]
                    qml.StatePrep(state, wires=op.wires)

                elif op.name == "BasisState":
                    state = op.params[0]
                    qml.BasisState(state, wires=op.wires)

                elif op.name == "HartreeFock":
                    electrons = op.params[0]
                    basis = op.params[1] if len(op.params) > 1 else "occupation_number"
                    orbitals = len(op.wires)
                    hf_state_array = qml.qchem.hf_state(electrons, orbitals, basis=basis)
                    qml.BasisState(hf_state_array, wires=op.wires)

                else:
                    gate_fn = PL_NAME_MAP.get(op.name)
                    if gate_fn is None:
                        raise ValueError(f"Unsupported op for PennyLane backend: {op.name}")
                    if op.params:
                        gate_fn(*op.params, wires=op.wires)
                    else:
                        gate_fn(wires=op.wires)

            else:
                # ----- Measure nodes -----
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
                if getattr(m, "hamiltonian_spec", None) is not None:
                    H = _pl_operator_from_pauli_sum(m.hamiltonian_spec)
                    returns.append(qml.expval(H))
                else:
                    obs_gate = PL_NAME_MAP.get(m.observable)
                    if obs_gate is None:
                        raise ValueError(f"Unsupported observable for PennyLane expval: {m.observable}")
                    returns.append(qml.expval(obs_gate(wires=m.wires)))

            elif m.kind == "density matrix":
                wires = list(range(ir.width)) if m.wires is None else list(m.wires)
                returns.append(qml.density_matrix(wires=wires))

            else:
                raise ValueError(f"Unsupported MEASURE kind: {m.kind}")

        return returns[0] if len(returns) == 1 else tuple(returns)

    return circuit


# -------------------------------
# Qiskit compiler
# -------------------------------
def compile_to_qiskit(ir: IRProgram, shots=None):
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

    # ----- Build the circuit (unitary part) -----
    for node in ir.ops:
        if not hasattr(node, "name"):
            continue  # measurements handled later

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
            gate_name = p[0]
            control_wires = w[:-1]
            target_wire = w[-1]

            tmp = QuantumCircuit(1, name=f"{gate_name}_base")
            if gate_name == "X":
                tmp.x(0)
            elif gate_name == "Y":
                tmp.y(0)
            elif gate_name == "Z":
                tmp.z(0)
            elif gate_name == "H":
                tmp.h(0)
            else:
                raise ValueError(
                    f"Unsupported CTRL base gate: {gate_name}. "
                    "Use CRX/CRY/CRZ for controlled rotations."
                )

            base_gate = tmp.to_gate()
            cgate = base_gate.control(len(control_wires))
            qc.append(cgate, control_wires + [target_wire])

        elif name == "BasisState":
            bits = list(node.params[0])
            if len(bits) != len(w):
                raise ValueError("BasisState params length must match wires length")
            for bit, wire in zip(bits, w):
                if int(bit) == 1:
                    qc.x(wire)

        elif name == "StatePrep":
            state = _np.asarray(node.params[0], dtype=complex)
            init = Initialize(state)
            qc.append(init, w)

        else:
            if name in ("SingleExcitation", "DoubleExcitation", "HartreeFock"):
                raise NotImplementedError(
                    f"{name} is not supported in Qiskit backend (chem excluded)."
                )
            raise ValueError(f"Unsupported op for Qiskit backend: {name}")

    measures = [m for m in ir.ops if not hasattr(m, "name")]
    if not measures:
        raise RuntimeError("No MEASURE outputs specified.")

    # ----- Measurement helpers -----
    def _sv_qiskit_to_pl_order(vec):
        v = _np.asarray(vec, dtype=complex)
        n = ir.width
        t = v.reshape([2] * n)                       # axes: q0, q1, ..., q{n-1}
        t = _np.transpose(t, axes=list(reversed(range(n))))  # axes: q{n-1}, ..., q0
        return t.reshape(-1)
    
    def _dm_qiskit_to_pl_order(dm):
        rho = _np.asarray(dm, dtype=complex)
        n = ir.width
        t = rho.reshape([2] * n + [2] * n)  # (ket axes q0..q{n-1}, bra axes q0..q{n-1})
        perm = list(reversed(range(n))) + [n + i for i in reversed(range(n))]
        t = _np.transpose(t, axes=perm)
        return t.reshape(2**n, 2**n)

    def _wire_probs_from_statevec(statevec, wires):
        wires = list(wires)
        probs_full = _np.abs(_np.asarray(statevec.data)) ** 2  # length 2^n
        out_dim = 2 ** len(wires)
        out = _np.zeros(out_dim, dtype=float)

        for idx, pval in enumerate(probs_full):
            out_idx = 0
            for j, q in enumerate(wires):
                bit = (idx >> q) & 1
                out_idx |= (bit << j)
            out[out_idx] += pval
        return out

    def _expval_single(statevec, observable, wire):
        if observable in ("X", "Y", "Z"):
            pauli = {"X": "X", "Y": "Y", "Z": "Z"}[observable]
            s = ["I"] * ir.width
            s[wire] = pauli
            P = Pauli("".join(reversed(s)))  # big-endian label
            return float(_np.real(statevec.expectation_value(P)))

        if observable == "H":
            # explicit matrix observable on the chosen wire
            Hmat = (1.0 / _np.sqrt(2.0)) * _np.array(
                [[1.0, 1.0], [1.0, -1.0]], dtype=complex
            )
            op = _np.array([[1.0 + 0j]])
            for q in range(ir.width):
                op = _np.kron(op, Hmat if q == wire else _np.eye(2, dtype=complex))
            psi = _np.asarray(statevec.data, dtype=complex)
            expval = _np.vdot(psi, op @ psi)
            return float(_np.real(expval))

        raise ValueError(f"Unsupported observable: {observable}")

    # ----- Runner (statevector-based, deterministic) -----
    def runner():
        sv = Statevector.from_instruction(qc)

        results = []
        for m in measures:
            if m.kind == "state":
                results.append(_sv_qiskit_to_pl_order(sv.data))

            elif m.kind == "probs":
                if not m.wires:
                    raise ValueError("MEASURE('probs') requires wires for Qiskit backend.")
                results.append(_wire_probs_from_statevec(sv, m.wires))

            elif m.kind == "expval":
                if getattr(m, "hamiltonian_spec", None) is not None:
                    H = _qiskit_sparsepauli_from_pauli_sum(
                        m.hamiltonian_spec, n_qubits=ir.width
                    )
                    results.append(float(_np.real(sv.expectation_value(H))))
                else:
                    if not m.wires or len(m.wires) != 1:
                        raise ValueError(
                            "MEASURE('expval') expects exactly one wire in Qiskit backend "
                            "when no Hamiltonian is provided."
                        )
                    results.append(_expval_single(sv, m.observable, m.wires[0]))

            elif m.kind == "density matrix":
                dm = DensityMatrix(sv)
                if m.wires is None:
                    results.append(_dm_qiskit_to_pl_order(dm.data))
                else:
                    traced = partial_trace(dm, [q for q in range(ir.width) if q not in list(m.wires)])
                    results.append(_np.asarray(traced.data))


            else:
                raise ValueError(f"Unsupported MEASURE kind: {m.kind}")

        return results[0] if len(results) == 1 else tuple(results)

    # attach circuit for DRAW()
    runner._qiskit_circuit = qc
    return runner
