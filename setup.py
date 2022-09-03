from setuptools import setup, find_packages
from pathlib import Path
setup(
    name="cartrackerreader",
    version="1.0.1",
    description="Python app for reading the storage of the car tracker via USB serial port",
    long_description=(Path(__file__).parent / 'PyPI Description.md').read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/Grvs44/cartrackerreader",
    author="Joe Greaves",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    packages=find_packages(),
    python_requires=">=3.9, <4",
    install_requires=["pyserial"],
    entry_points={
        "gui_scripts": [
            "cartrackerreader=cartrackerreader:main",
        ],
    },
)
