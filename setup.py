from setuptools import setup, find_packages

exec(open('audioio/version.py').read())

setup(
    version = __version__,
    packages = ['audioio']
    #packages = find_packages(exclude = ['docs', 'tests', 'site'])
)
