"""This is a Python package that provides following features:
    1. Manage ssh info.
    2. Auto login remote servers even if they must be logined through many jumps.
    3. Auto run commands after login.
"""

import sys

__verison__ = '0.1.1'
__title__ = 'slm'
__author__ = 'fortime'
__email__ = 'palfortime@gmail.com'
__url__ = 'https://github.com/fortime/slm'
__description__ = """slm - ssh login manager
"""

try:
    from setuptools import setup, find_packages
    from setuptools.command.egg_info import egg_info
except ImportError:
    print('%s now needs setuptools in order to build.' % __title__)
    print('Install it using your package manager (usually python-setuptools) or via pip \
           (pip install setuptools).')
    sys.exit(1)

setup(
        name=__title__,
        version=__verison__,
        author=__author__,
        author_email=__email__,
        description=__description__,
        url=__url__,
        install_requires=[
            'PyYAML>=3.12',
            'libtmux>=0.7.7',
            'treelib>=1.5.1',
            'cmd2'
            ],
        tests_require=[
            ],
        data_files=[],
        package_dir={__title__: 'src/{0}'.format(__title__)},
        packages=find_packages('src'),
        cmdclass={},
        test_suite="test",
        license="GPLv3",
        scripts=[],
        entry_points={
            'console_scripts': [
                '{0}={0}.main:run'.format(__title__)
                ]
            },
        zip_safe=False,
        dependency_links=[
            ],
        )
