from setuptools import setup, find_packages

setup(
    name="loafware",
    version="0.1.0",
    description="Modular control library for BREAD slices",
    author="Cameron K. Brooks",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=[
        "smbus2",
        # TODO: Add pyCRUMBS as a package so it can be installed with pip
    ],
)
