from setuptools import setup, find_packages
setup(
    name="cartrackerreader",
    version="1.0.0",
    description="Python app for reading the storage of the car tracker via USB serial port",
    url="https://github.com/Grvs44/cartrackerreader",
    author="Joe Greaves",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9, <4",
    install_requires=["pyserial"],
    entry_points={
        "console_scripts": [
            "cartrackerreader=cartrackerreader:main",
        ],
    },
)
