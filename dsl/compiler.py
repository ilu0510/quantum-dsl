# compiler.py
import pennylane as qml
from .ir import *


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
            else:
                print(f"RuntimeError: Unsupported MEASURE kind: {m.kind}")

        return returns[0] if len(returns) == 1 else tuple(returns)

    return circuit

