from setuptools import setup, find_packages
import sys

version = '1.6'

f = open('README.rst')
long_description = f.read()
f.close()

requires = []
if sys.version_info[:2] == (2, 4):
    requires.append('simplejson < 2.0.10')

setup(name='quantumrandom',
      version=version,
      description="A Python interface to the ANU Quantum Random Numbers Server",
      long_description=long_description,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: MIT License',
          'Topic :: Scientific/Engineering :: Mathematics',
          ],
      keywords='quantum random',
      author='Luke Macken',
      author_email='lmacken@redhat.com',
      url='http://github.com/lmacken/quantumrandom',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=requires,
      entry_points="""
        [console_scripts]
        qrandom = quantumrandom.cmd:main
        qrandom-dev = quantumrandom.dev:main
      """,
      )
