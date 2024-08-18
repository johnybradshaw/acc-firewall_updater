from setuptools import setup, find_packages

setup(
    name="acc-fwu",
    version="0.1.0",
    packages=find_packages(where="acc-fwu"),  # Finds packages in the 'acc-fwu' directory
    package_dir={"": "acc-fwu"},  # Sets 'acc-fwu' as the root directory for packages
    install_requires=[
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "acc-fwu=cli:main",  # This should point to 'acc_fwu.cli:main'
        ],
    },
    author="John Bradshaw",
    author_email="acc-fwu@bradshaw.cloud",
    description="A tool to update Linode/ACC firewall rules with your current IP address.",
    url="https://github.com/johnybradshaw/acc-firewall_updater",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)