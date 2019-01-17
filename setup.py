#
# Copyright (c) 2019, Magenta ApS
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import setuptools

setuptools.setup(
    name='os2rollekatalog_integration',
    version='0.1',
    description='Tool for integrating OS2MO with OS2Rollekatalog',
    author='Magenta ApS',
    author_email='info@magenta.dk',
    packages=setuptools.find_packages(),
    install_requires=[
        'os2mo-tools',
    ],
    dependency_links=['https://github.com/OS2mo/os2mo-tools/tarball/master#egg=os2mo-tools-0.1'],
    entry_points={
        # -*- Entry points: -*-
        'console_scripts': [
            'os2rollekatalog_integration=os2rollekatalog_integration.os2rollekatalog_integration:main',
        ],
    },

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MPL 2.0",
        "Operating System :: OS Independent",
    ]
)
