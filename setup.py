
from setuptools import setup

entrypoints = {
        'console_scripts': ['HydXS=HydXS.cli_interface:app'],
    }

setup(name='HydXS',
      version='0.1a',
      description='A tool for automatic detection of bankfull boundaries from river cross section data',
      url='http://github.com/sailngarbwm/HydXS',
      author='kathryn russell',
      author_email='kathryn.russel@unimelb.edu.au',
      license='CC',
      packages=['HydXS'],
      entry_points = entrypoints,
      zip_safe=False)