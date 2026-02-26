# program.py
from .ir import IRProgram
from .compiler import compile_to_pennylane, compile_to_qiskit

_stack = []
_block_stack = []

def current_program():
    if not _stack:
        raise RuntimeError("No active Program. Use `with PREPARE(n) as p:`")
    return _stack[-1]

def _current_origin():
    return list(_block_stack)

def push_block(name: str):
    _block_stack.append(name)

def pop_block():
    _block_stack.pop()

class Program:
    def __init__(self, width):
        self.ir = IRProgram(width=width)
        self._compiled = None
        self._backend = None

    def append(self, op_or_meas):
        if hasattr(op_or_meas, "origin") and not op_or_meas.origin:
            op_or_meas.origin = _current_origin()
        self.ir.ops.append(op_or_meas)

    def compile(self, shots=None, backend="pennylane"):
        self.ir.canon()
        self._backend = backend
        if backend == "pennylane":
            self._compiled = compile_to_pennylane(self.ir)
        elif backend == "qiskit":
            self._compiled = compile_to_qiskit(self.ir, shots=shots)
        else:
            raise ValueError("backend must be 'pennylane' or 'qiskit'")
        return self._compiled

    def __call__(self, *args, **kwargs):
        if self._compiled is None:
            self.compile()
        return self._compiled(*args, **kwargs)

    def __enter__(self):
        _stack.append(self)
        return self

    def __exit__(self, *exc):
        _stack.pop()