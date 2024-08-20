import os
from setuptools import setup, find_packages

with open("README.md") as f:
    long_description = f.read()

setup(
    name="acc-fwu",
    version="0.1.2",
    package_dir={"": "src"},  # Sets 'acc-fwu' as the root directory for packages
    packages=find_packages(where="src"),  # Finds packages in the 'src' directory
    install_requires=[
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "acc-fwu=acc_fwu.cli:main",  # This should point to 'acc_fwu.cli:main'
        ],
    },
    author="John Bradshaw",
    author_email="acc-fwu@bradshaw.cloud",
    description="A tool to update Linode/ACC firewall rules with your current IP address.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/johnybradshaw/acc-firewall_updater",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)