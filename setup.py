from setuptools import setup, find_packages

exec(open('audioio/version.py').read())

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='audioio',
    version=__version__,
    author='Jan Benda, Joerg Henninger',
    author_email="jan.benda@uni-tuebingen.de",
    description="Platform independent interfacing of numpy arrays of floats with audio files and devices.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bendalab/audioio",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    entry_points={
        'console_scripts': [
            'audioconverter = audioio.audioconverter:main',
            'audiomodules = audioio.audiomodules:main',
        ]},
    install_requires=['numpy']
)
