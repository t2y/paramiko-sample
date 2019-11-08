import os
from setuptools import find_packages, setup

cur_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(cur_dir, 'README.md')) as f:
    long_description = f.read()

setup(
    name='paramiko-sample',
    version='0.1.0',
    description='paramiko sample',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries',
    ],
    author='Tetsuya Morimoto',
    author_email='tetsuya dot morimoto at gmail dot com',
    url='https://github.com/t2y/paramiko-sample',
    license='Apache License 2.0',
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['paramiko'],
    tests_require=['tox', 'pytest', 'pytest-codestyle', 'pytest-flakes'],
    entry_points = {
        'console_scripts': [
            'paramiko-ssh=paramiko_sample.main:main',
        ],
    },
)
