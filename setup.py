from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in cefiro_customizations/__init__.py
from cefiro_customizations import __version__ as version

setup(
	name='cefiro_customizations',
	version=version,
	description='Customization dor DObulk',
	author='Element Labs',
	author_email='saeed@elementlabs.xyz',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
