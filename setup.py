
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

INSTALL_REQUIRES = [
    'pymongo',
    'requests',
    'bottle',
    'colorlog',
    'urllib3',
]

setup(
    version='1.0',
    description='Tissegram',
    url='https://github.com/lchagnoleau/Tissegram',
    name = "Tissegram",
    author="Loic Chagnoleau",
    author_email = "loic.chagnoleau@gmail.com",
    license='GPL-3.0',
    install_requires=INSTALL_REQUIRES,
    include_package_data=True,
    packages = find_packages()
)