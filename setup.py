from setuptools import setup

setup(name='mficlient',
      version='0.3.0',
      description='A remote control client for Ubiquiti\'s mFi system',
      author='Dan Smith',
      author_email='dsmith+mficlient@danplanet.com',
      url='http://github.org/kk7ds/mficlient',
      packages=['mficlient'],
      scripts=['mfi'],
      install_requires=['requests'],
      tests_require=['mock'],
)
