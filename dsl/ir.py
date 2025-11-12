# ir.py
import pennylane as qml
class Op:
    def __init__(self, name, wires, params=None):
        self.name, self.wires, self.params = name, wires, params or ()

class Measure:
    def __init__(self, kind, wires): 
        self.kind = kind
        self.wires = wires

class IRProgram:
    def __init__(self, width, ops=None):
        self.width, self.ops = width, list(ops or [])
    def canon(self):
        for op in self.ops:
            if hasattr(op, "name"):
                if op.name not in PL_NAME_MAP:
                    print(f"NameError: Unknown gate {op.name}.")
        return self

#Map
PL_NAME_MAP = {
    "H": qml.Hadamard,
    "X": qml.PauliX,
    "Y": qml.PauliY,
    "Z": qml.PauliZ,
    "CNOT": qml.CNOT,
    "RX": qml.RX,
    "RY": qml.RY,
    "RZ": qml.RZ,
    "CZ": qml.CZ,
    "CY": qml.CY,
    "CTRL": None,
    "StatePrep": qml.StatePrep,
}