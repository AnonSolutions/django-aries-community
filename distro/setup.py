import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-aries-community',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    license='996.ICU License',  # see https://github.com/996icu/996.ICU
    description='A simple Django package to build web-based Indy/Aries agent applications.',
    long_description=README,
    url='https://github.com/AnonSolutions/django-aries-community',
    author='Ian Costanzo',
    author_email='ian@anon-solutions.ca',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',  
        'Operating System :: Unix',
        'Operating System :: MacOS',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
