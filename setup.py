from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='quantumrandom',
      version=version,
      description="A Python interface to the ANU Quantum Random Numbers Server",
      long_description="""\
""",
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Topic :: Scientific/Engineering :: Mathematics',
          ],
      keywords='quantum random',
      author='Luke Macken',
      author_email='lmacken@redhat.com',
      url='http://github.com/lmacken/python-quantumrandom',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          'BeautifulSoup',
      ],
      entry_points="""
      """,
      )
