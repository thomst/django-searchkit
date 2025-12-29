#!/usr/bin/env python

import os
from pathlib import Path
from setuptools import setup, find_packages


def get_version():
    """Get the local package version."""
    namespace = {}
    path = Path("searchkit", "__version__.py")
    exec(path.read_text(), namespace)
    return namespace["__version__"]


def read(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, encoding="utf-8") as file:
        return file.read()


get_version = get_version()
if 'dev' in get_version:
    dev_status = 'Development Status :: 3 - Alpha'
elif 'beta' in get_version:
    dev_status = 'Development Status :: 4 - Beta'
else:
    dev_status = 'Development Status :: 5 - Production/Stable'


setup(
    name="django-searchkit",
    version=get_version,
    description="Finally a real searchkit for django!",
    long_description=read("README.md"),
    long_description_content_type='text/markdown',
    author="Thomas Leichtfuß",
    author_email="thomas.leichtfuss@posteo.de",
    url="https://github.com/thomst/django-searchkit",
    license="BSD-2-Clause",
    platforms=["OS Independent"],
    packages=find_packages(include=['searchkit', 'searchkit.*']),
    package_data={'searchkit': ['static/**', 'templates/**'],},
    include_package_data=False,
    install_requires=[
        "Django>=4.0",
        "django-picklefield",
        "djangorestframework",
        "django-modeltree",
    ],
    classifiers=[
        dev_status,
        "Framework :: Django",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",
        "Framework :: Django :: 5.2",
        "Framework :: Django :: 6.0",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    zip_safe=True,
)
