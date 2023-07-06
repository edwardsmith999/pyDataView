#!/usr/bin/env python

from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup( name = "pyDataView",
       version = "2.0.2",
       author = ["Edward Smith"],
       author_email = "edward.smith@brunel.ac.uk",
       url = "https://github.com/edwardsmith999/pyDataView",
       classifiers=['Development Status :: 3 - Alpha',
                     'Programming Language :: Python :: 3.6'],
       packages=find_packages(exclude=['contrib', 'docs', 'tests']),
       keywords='visualisation scientific data',
       license = "GPL",
       install_requires=['numpy', 'scipy', 'matplotlib', 'wxpython', 'vispy', ],
       extras_require = {'Channelflow_plots':  ["h5py"], 
                         'cpl_plots':["scikit-image"]},
       description = "Data Viewer GUI written in python, wxpython and matplotlib",
       long_description = long_description,
       long_description_content_type='text/markdown',
       entry_points={
            'console_scripts': [
                'pyDataView=pyDataView:main',
            ],
       },
)
