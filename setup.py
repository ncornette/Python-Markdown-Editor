#!/usr/bin/env python
import os
import re

from setuptools import setup
from pip.req import parse_requirements

install_reqs = parse_requirements('./requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]

data_dirs = ['markdown_editor/libs', 'markdown_editor/styles']
data_files = ['markdown_editor/markdown_edit.html']

r = re.compile('^markdown_editor/')
datafiles = []
for data_dir in data_dirs:
    datafiles.extend(r.sub('', d) + '/' + f for d, _, files in os.walk(data_dir) if files for f in files)

datafiles.extend(r.sub('', f) for f in data_files)

setup(name='Python-Markdown-Editor',
      version='0.9',
      description='Standalone editor for your markdown files',
      author='Nicolas Cornette',
      author_email='nicolas.cornette@gmail.com',
      url='https://github.com/ncornette/Python-Markdown-Editor.git',
      install_requires=reqs,
      packages=['markdown_editor'],
      py_modules=['markdown_edit'],
      package_data={'markdown_editor': datafiles},
      entry_points={
          'console_scripts': [
              'markdown_edit = markdown_edit:main'
          ]
      }
      )
