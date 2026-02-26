# DSL-Transpiler-for-PennyLane & Qiskit

A Python-based Domain-Specific Language (DSL) for quantum computing that simplifies quantum circuit design with an intuitive, declarative syntax.

The DSL compiles into a backend-agnostic Intermediate Representation (IR), which can then be transpiled into:

- **PennyLane**
- **Qiskit**

This project was developed as part of my internship with the Institute of Applied Artificial Intelligence & Robotics (IAAIR), with a focus on compiler design, IR inspection, and backend interoperability.

---

## Architecture Overview

The DSL follows a three-layer architecture:

### 1. User API Layer  
High-level declarative quantum circuit construction (`SUPERPOSE`, `ENTANGLE`, `MEASURE`, `@BLOCK`, etc.)

### 2. Intermediate Representation (IR)  
Backend-agnostic structured representation of:
- Operations
- Parameters
- Measurement intent
- Observable intent
- Block provenance

### 3. Backend Compilers
- `compile_to_pennylane()`
- `compile_to_qiskit()`

This separation enables backend portability without rewriting user code.

---

## Features

### Backend-Agnostic IR
- Structured intermediate representation
- Canonical validation
- Extractable circuit metadata

### Dual Transpilation Pipeline
- Compile to PennyLane
- Compile to Qiskit
- Select backend via `Program.compile(backend=...)`

### High-Level Abstractions
- Gate-level operations hidden behind declarative API

### Reusable Blocks
- Define modular subcircuits with `@BLOCK`
- Track provenance through IR

### Multiple Gate Types
- Single-qubit gates
- Two-qubit gates
- Controlled gates
- Rotation gates
- Multi-controlled abstractions

### Observable Handling
- Statevector
- Probabilities
- Expectation values
- Density matrices

### IR Inspection
- Structured IR export (`INSPECT_IR`)
- JSON output for analysis
- Debugging & compiler research support

### Optimisation Utilities
- Central-difference gradient descent
- Variational circuit experimentation

### Visualization
- ASCII circuit drawings
- Matplotlib circuit diagrams
- Backend-aware drawing

### Result Graphing
- Probability histograms
- Statevector amplitude plots
- Expectation value visualisation

### Compiler Benchmarking Utilities
- IR build time measurement
- Canonicalisation timing
- Memory usage tracking
- Scaling analysis (RQ5)

---

## Example Usage

```python
from dsl import *

with PREPARE(2) as p:
    SUPERPOSE(0)
    ENTANGLE(0, 1)
    MEASURE("probs", 0, 1)

# Compile to PennyLane
p.compile(backend="pennylane")
DRAW(p)

# Compile to Qiskit
p.compile(backend="qiskit")
DRAW(p)

print(p())
```

## Project Structure
quantum-dsl/
├── .gitignore
├── README.md
├── setup.py
├── dsl/
│   ├── __init__.py
│   ├── api.py           # User-facing DSL
│   ├── program.py       # Program & backend selection
│   ├── ir.py            # Backend-agnostic IR
│   └── compiler.py      # PennyLane + Qiskit compilers
├── Examples/            # Example algorithms
│   ├── Grover.py
│   ├── DJ2Bit.py
│   ├── QFT.py
│   ├── Qtele.py
│   └── VQE.py
├── ir_inspection_tests/ # IR inspection and benchmarking
├── rq5_ir_min_logs/     # IR timing experiment logs
└── rq5_qft_scaling_logs/# Scaling experiment outputs

## Requirements 
 - Python 3.11 recommended (PennyLane compatibility)
 - PennyLane
 - Qiskit
 - Numpy
 - Matplotlib
