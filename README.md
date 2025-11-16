## DSL-Transpiler-for-PennyLane
A Python-based Domain-Specific Language (DSL) for quantum computing that simplifies quantum circuit design with an intuitive, declarative syntax. Built on PennyLane, it provides high-level abstractions for quantum operations, reusable circuit blocks, and visualisation tools. This was developed as a part of my internship experience with the Institue of Applied Artificial Intelligence & Robotics (IAAIR).

## Features

- **High-level abstractions**: Simple functions like `SUPERPOSE()`, `ENTANGLE()`, and `MEASURE()`
- **Reusable blocks**: Define circuit fragments with `@BLOCK` and reuse with `USE()`
- **Multiple gate types**: Single-qubit, two-qubit, rotation, and multi-controlled gates
- **Visualization**: ASCII and matplotlib circuit drawings with `DRAW()`
- **Result graphing**: Histogram and statevector visualisations with `GRAPH()`
- **Built on PennyLane**: Leverages a powerful quantum computing framework

## Project Structure
```
quantum-dsl/
├── .gitignore
├── README.md
├── setup.py
├── dsl/
│   ├── api.py         # User-facing API
│   ├── program.py     # Program management
│   ├── ir.py          # Intermediate representation
│   └── compiler.py    # PennyLane compiler
└── Examples/
    ├── Grover.py      # Grover's search algorithm
    ├── DJ2Bit.py      # Deutsch-Jozsa algorithm
    └── Qtele.py       # Quantum teleportation
```

## Requirements

- Python 3.8+
- PennyLane
- NumPy
- Matplotlib
