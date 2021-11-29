import glob
import os
import sys
from distutils.core import setup
from typing import List


def get_version(filename):
    import ast
    version = None
    with open(filename) as f:
        for line in f:
            if line.startswith('__version__'):
                version = ast.parse(line).body[0].value.s
                break
        else:
            raise ValueError('No version found in %r.' % filename)
    if version is None:
        raise ValueError(filename)
    return version


def _get_all_files(parent: str, child: str) -> List[str]:
    path = os.path.abspath(os.path.join(parent, child))
    hidden = glob.glob(os.path.join(path, ".**"), recursive=True)
    nonhidden = glob.glob(os.path.join(path, "**"), recursive=True)
    items = hidden + nonhidden
    files = filter(os.path.isfile, items)
    files = list(map(lambda p: os.path.relpath(p, parent), files))
    return files


if sys.version_info < (3, 6):
    msg = 'cattleman works with Python 3.6 and later.\nDetected %s.' % str(sys.version)
    sys.exit(msg)

lib_version = get_version(filename='include/cattleman/__init__.py')

setup(
    name='cattleman',
    packages=[
        'cattleman',
        'cattleman.cli',
        'cattleman.cli.commands',
        'cattleman.utils'
    ],
    package_dir={
        'cattleman': 'include/cattleman'
    },
    package_data={
        "cattleman": [
            "schemas/*/*.json"
        ],
    },
    version=lib_version,
    license='MIT',
    description='TODO: DESCRIPTION_HERE',
    author='Andrea F. Daniele',
    author_email='afdaniele@ttic.edu',
    url='https://github.com/afdaniele/cattleman',
    download_url='https://github.com/afdaniele/cattleman/tarball/{}'.format(lib_version),
    zip_safe=False,
    include_package_data=True,
    keywords=['TODO', 'code', 'container', 'containerization', 'package', 'toolkit', 'docker'],
    install_requires=[
        # TODO: verify this list is correct
        'docker>=4.4.0',
        'cbor2',
        'requests',
        'jsonschema',
        'termcolor',
        'sshconf',
        'ipaddress',
        'cryptography',
        *(['dataclasses'] if sys.version_info < (3, 7) else [])
    ],
    scripts=[
        'include/cattleman/bin/cattle'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
