# In the root of your vivarium-template project

from setuptools import setup, find_packages

setup(
    name='vivarium-vcornea',  # The name users will use to pip install
    version='0.1.0',
    packages=find_packages(), # Automatically find your 'processes' and other modules
    author='Joel Vanin',
    author_email='jvanin@iu.edu',
    description='A Vivarium wrapper for the vCornea CompuCell3D model.',
    install_requires=[
        'vivarium-core',
        'pandas',
        'fastparquet',
        ],
    entry_points={
        'console_scripts': [
            'run_vcornea_test=experiments.run_vcornea_test:main', # Makes your test runnable from command line
        ],
    },
)