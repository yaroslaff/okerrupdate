from setuptools import setup
import os
import okerrupdate


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='okerrupdate',
      version=okerrupdate.__version__,
      description='client-side okerr module and utilities',
      url='https://github.com/yaroslaff/okerrupdate',
      author='Yaroslav Polyakov',
      author_email='yaroslaff@gmail.com',
      license='MIT',
      packages=['okerrupdate'],
      scripts=['scripts/okerrupdate', 'scripts/okerrmod', 'scripts/okerrapi'],
      include_package_data=True,

      long_description = read('README.md'),
      long_description_content_type='text/markdown',

      install_requires=['requests == 2.32.4', 'urllib3 == 2.5.0', 'psutil', 'python-dotenv'],
      zip_safe=False
      )

