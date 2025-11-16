from setuptools import setup, find_packages

setup(
    name="quantum-dsl",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pennylane",
        "matplotlib",
        "numpy",
    ],
)


