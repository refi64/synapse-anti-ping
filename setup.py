# type: ignore

import setuptools

with open('requirements.txt') as fp:
    reqs = fp.read().splitlines()

setuptools.setup(
    name='synapse-anti-ping',
    # Keep in sync with pyproject.toml
    version='0.1.0',
    author='Ryan Gonzalez',
    description='A Synapse antispam module to defeat mass pings',
    packages=['synapse_anti_ping'],
    install_requires=reqs,
    python_requires='>=3.6',
)
