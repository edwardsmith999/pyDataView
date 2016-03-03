#!/usr/bin/env python

from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup( name = "pyDataViewer",
       version = "1.0",
       author = ["Edward Smith","David Trevelyan"]
       author_email = "edward.smith05@imperial.ac.uk",
       url = "https://github.com/edwardsmith999/pyDataView",
       classifiers=['Development Status :: 3 - Alpha',
                     'Programming Language :: Python :: 2.7'],
       packages=find_packages(exclude=['contrib', 'docs', 'tests']),
       keywords='visualisation scientific data',
       license = "GPL",
       install_requires=['numpy', 'scipy', 'matplotlib', 'wxpython'],
       extras_require = {'Channelflow_plots':  ["h5py"], 
                         'cpl_plots',:["skimage"]},
       description = "Data Viewer GUI written in python, wxpython and matplotlib",
       long_description = long_description,
       entry_points={
            'console_scripts': [
                'pyDataView=pyDataView:main',
            ],
       },
)
~                                                                                                                                           
~                                                                                                                                           
~                                                                                                                                           
~                                                                                                                                           
~                                                                                                                                           
~                                                                                                                                           
~                                                                                                                                           
~                                        
