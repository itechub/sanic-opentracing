#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import versioneer

version = versioneer.get_version()
setup(
    name="sanic_opentracing",
    cmdclass=versioneer.get_cmdclass(),
    version=version,
    url="https://github.com/shady-robot/sanic-opentracing/",
    download_url="https://github.com/shady-robot/sanic-opentracing/tarball/" + version,
    license="BSD",
    author="Shady Robot",
    author_email="darkercookies@gmail.com",
    description="OpenTracing support for Sanic applications",
    long_description=open("README.rst").read(),
    packages=["sanic_opentracing", "tests"],
    platforms="any",
    install_requires=["sanic", "opentracing>=2.0,<3"],
    extras_require={
        "tests": [
            "coverage",
            "flake8<3",  # see https://github.com/zheller/flake8-quotes/issues/29
            "flake8-quotes",
            "mock",
        ]
    },
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
