import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pysh",
    version="0.8.0",
    author="Zbigniew Kaleta aka. Radagast",
    description="Tools for Bash-like programming in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    install_requires=[
        'psutil',
      ],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: MIT",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.3',
)
