# program.py
from .ir import *
from .compiler import *

_stack = []

def current_program():
    if not _stack: 
        print("RunTime Error: No active Program")
    return _stack[-1]

class Program:
    def __init__(self, width):
        self.ir = IRProgram(width=width)
        self._compiled = None

    def append(self, op_or_meas): 
        self.ir.ops.append(op_or_meas)

    def compile(self, shots=None):
        self.ir.canon()
        self._compiled = compile_to_pennylane(self.ir)
        return self._compiled

    def __call__(self, *args, **kwargs):
        if self._compiled is None: self.compile()
        return self._compiled(*args, **kwargs)

    def __enter__(self): _stack.append(self); return self
    def __exit__(self, *exc): _stack.pop()
