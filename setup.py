from setuptools import setup, find_packages, Command


version = __import__('pytest_sftpserver').get_version()


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
    version=version,
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
