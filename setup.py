from distutils.core import setup
from setuptools import find_packages

setup(name='audioio',
      version='0.1',
      packages=find_packages(exclude=['contrib', 'doc', 'tests*']),
      description='Platform independent reading of audio files as well as recording and
playing of audio data.',
      author='Jan Benda, Joerg Henninger',
      requires=['numpy']
      )
