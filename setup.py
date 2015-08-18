import codecs

from os import path
from setuptools import find_packages, setup


def read(*parts):
    filename = path.join(path.dirname(__file__), *parts)
    with codecs.open(filename, encoding="utf-8") as fp:
        return fp.read()


setup(
    author="Jeff Sternberg",
    author_email="jeffsternberg@gmail.com",
    description="Distributed locking in Python, with schmear",
    name="lox",
    long_description=read("README.md"),
    version="0.1",
    url="https://github.com/sternb0t/lox",
    license="MIT",
    keywords='distributed locking locks redis postgresql',
    packages=find_packages(),
    package_data={
        "lox": []
    },
    test_suite="lox.tests",
    tests_require=[
        "mox==0.5.3",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=[
        "psycopg2>=2.6.1",
        "pytz>=2015.4",
        "redis>=2.10.3"
    ],
    zip_safe=False
)
