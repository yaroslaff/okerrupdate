from setuptools import setup
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='okerrupdate',
    version='1.2.10',
    description='client-side okerr module and utilities',
    url='https://gitlab.com/yaroslaff/okerrupdate',
    author='Yaroslav Polyakov',
    author_email='yaroslaff@gmail.com',
    license='MIT',
    packages=['okerrupdate'],
    scripts=['scripts/okerrupdate','scripts/okerrmod'],
    include_package_data=True,

    long_description = read('README.md'),
    long_description_content_type='text/markdown',

    install_requires=['requests', 'psutil', 'python-dotenv'],
    zip_safe=False
)    

