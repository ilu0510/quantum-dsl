# ir.py
import pennylane as qml
class Op:
    def __init__(self, name, wires, params=None, origin=None):
        self.name = name
        self.wires = list(wires)
        self.params = params or ()
        self.origin = list(origin) if origin else []

class Measure:
    def __init__(self, kind, wires=None, observable=None, operator=None, basis=None, origin=None):
        self.kind = kind
        self.wires = None if wires is None else list(wires)
        self.observable = observable
        self.operator = operator
        self.basis = basis  # NEW: "Z", "X", "Y", "H", "operator-defined", "N/A"
        self.origin = list(origin) if origin else []

class IRProgram:
    def __init__(self, width, ops=None, wire_map=None):
        self.width = width
        self.ops = list(ops or [])

        
        if wire_map is None:
            self.wire_map = {f"q[{i}]": i for i in range(width)}
        else:
            self.wire_map = dict(wire_map)

    def canon(self):
        # Keep your existing name checks, but add wire range checks.
        for op in self.ops:
            if hasattr(op, "name"):
                if op.name not in PL_NAME_MAP:
                    raise NameError(f"Unknown gate {op.name}.")
                for w in op.wires:
                    if not isinstance(w, int):
                        raise TypeError(f"Wire {w} must be int.")
                    if not (0 <= w < self.width):
                        raise ValueError(f"Wire {w} out of range for width={self.width}.")
            else:
                # Measure checks
                if op.wires is not None:
                    for w in op.wires:
                        if not isinstance(w, int):
                            raise TypeError(f"Measure wire {w} must be int.")
                        if not (0 <= w < self.width):
                            raise ValueError(f"Measure wire {w} out of range for width={self.width}.")
        return self
    
    def extract_fields(self):
        ordered = []
        params = []
        meas_intent = []
        obs_intent = []

        for i, node in enumerate(self.ops, 1):
            if hasattr(node, "name"):  # Op
                ordered.append({
                    "index": i,
                    "type": "op",
                    "name": node.name,
                    "wires": node.wires,
                    "params": list(node.params),
                    "origin": node.origin,
                })
                if node.params:
                    params.append({
                        "index": i,
                        "name": node.name,
                        "params": list(node.params),
                    })
            else:  # Measure
                ordered.append({
                    "index": i,
                    "type": "measure",
                    "kind": node.kind,
                    "wires": node.wires,
                    "basis": node.basis,
                    "observable": node.observable,
                    "has_operator": node.operator is not None,
                    "origin": node.origin,
                })

                meas_intent.append({
                    "kind": node.kind,
                    "wires": node.wires,
                    "basis": node.basis,
                })

                # Observable intent = anything expval-related
                if node.kind == "expval":
                    if node.operator is not None:
                        obs_intent.append({
                            "type": "Hamiltonian",
                            "summary": str(node.operator),
                            "wires": node.wires,
                        })
                        params.append({
                            "index": i,
                            "name": "Hamiltonian",
                            "params": ["operator"],
                        })
                    else:
                        obs_intent.append({
                            "type": node.observable,
                            "wires": node.wires,
                        })

        return {
            "Circuit width": self.width,
            "Wire map": self.wire_map,
            "Ordered ops": ordered,
            "Parameters": params,
            "Measurement intent": meas_intent,
            "Observable intent": obs_intent,
        }

#Map
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