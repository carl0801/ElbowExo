import ctypes
import os

# Load the shared library
lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__), "filter_lib.so"))

# Define the argument and return types for the Rust function
lib.add.argtypes = (ctypes.c_int, ctypes.c_int)
lib.add.restype = ctypes.c_int

# Python function to wrap the Rust function
def add(a, b):
    return lib.add(a, b)
