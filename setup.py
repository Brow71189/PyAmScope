# -*- coding: utf-8 -*-

"""
To upload to PyPI, PyPI test, or a local server:
python setup.py bdist_wheel upload -r <server_identifier>
"""

import setuptools

setuptools.setup(
    name="AmScope",
    version="0.0.1",
    author="Andreas Mittelberger",
    author_email="Brow71189@gmail.com",
    description="Amscope camera driver python wrapper",
    url="https://github.com/Brow71189/SwiftCam",
    packages=["AmScope"],
    license='MIT',
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python :: 3.5",
    ],
    zip_safe=False,
    include_package_data=True,
    python_requires='~=3.5',
)