"""
Django HAL
==========

A set of utilities for building HAL REST APIs in Django.

"""

import os
from setuptools import setup, find_packages


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE_PATH = os.path.join(PROJECT_DIR, 'VERSION')
README_FILE_PATH = os.path.join(PROJECT_DIR, 'README.rst')


def read(path):
  if not os.path.isfile(path):
    raise EnvironmentError("File not found: %s" % path)
  with open(path) as f:
    return f.read().strip()


if __name__ == '__main__':
  setup(
    name='django-hal',
    version=read(VERSION_FILE_PATH),
    description=read(README_FILE_PATH),
    author='Nick Zarczynski',
    author_email='nick@unb.services',
    url='https://github.com/unbservices/django-hal',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    # For a full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
      'Development Status :: 2 - Pre-Alpha',
      'Environment :: Web Environment',
      'Framework :: Django',
      'Framework :: Django :: 1.8',
      'License :: OSI Approved :: MIT License',
      'Natural Language :: English',
      'Operating System :: OS Independent',
      'Programming Language :: Python',
      'Programming Language :: Python :: 2.7',
    ],
  )
