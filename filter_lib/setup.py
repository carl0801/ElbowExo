from setuptools import setup
from setuptools_rust import RustExtension

setup(
    name="filter_package",
    version="0.1.0",
    rust_extensions=[RustExtension("filter_package.filter_lib")],
    packages=["filter_package"],
    # Ensure that the rust library is built during package installation
    zip_safe=False,
)
