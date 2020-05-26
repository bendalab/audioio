from distutils.core import setup
from setuptools import find_packages

exec(open('audioio/version.py').read())

setup(name='audioio',
      version=__version__,
      packages=find_packages(exclude=['contrib', 'doc', 'tests*']),
      entry_points={
        'console_scripts': [
            'audioconverter = audioio.audioconverter:main',
        ]},
      description='Platform independent reading of audio files as well as recording and playing of audio data.',
      author='Jan Benda, Joerg Henninger',
      requires=['numpy', 'pysoundfile', 'audioread', 'pyaudio']
      )
