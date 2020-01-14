import codecs
import os
import re

from setuptools import setup, find_packages, Command

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(
        r"^VERSION = \(([^\)]*)\)", version_file, re.M
    )
    if version_match:
        return '.'.join(i.strip() for i in version_match.group(1).split(','))
    raise RuntimeError('Unable to find version string.')


class Test(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        raise SystemExit(subprocess.call(['tox']))


with open("README.rst", "r") as readme:
    README = readme.read()

setup(
    name='pytest-sftpserver',
    version=find_version('pytest_sftpserver', '__version__.py'),
    author='Ulrich Petri',
    author_email='mail@ulo.pe',
    license='MIT License',
    description='py.test plugin to locally test sftp server connections.',
    long_description=README,
    url='http://github.com/ulope/pytest-sftpserver/',

    packages=find_packages(),
    package_data={"pytest_sftpserver": ["keys/*.pub", "keys/*.priv"]},
    install_requires=[
        "paramiko",
        "six",
    ],
    tests_require=[
        'tox',
    ],
    entry_points={
        'pytest11': ['sftpserver = pytest_sftpserver.plugin']
    },
    cmdclass={
        'test': Test
    },

    zip_safe=False,
    keywords='py.test pytest plugin server local sftp localhost',
    classifiers=[
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Testing'
    ]
)
