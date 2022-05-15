from setuptools import setup, find_packages

setup(
    name="FAST Protocol implementation",
    version="1.0",
    url="github.com",
    license="MIT",
    install_requires=["ecpy","p2pnetwork","pycryptodome"],
    author="Benjamin Y. S. Kjaer, Oliver H. Joergensen, Silas P. Nielsen",
    description="some description",
    python_requires='>=3.6'
)