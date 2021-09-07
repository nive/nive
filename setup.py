import os
import sys

from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))

try:
    README = open(os.path.join(here, 'readme.md')).read()
    CHANGES = open(os.path.join(here, 'changes.txt')).read()
except:
    README = ''
    CHANGES = ''

requires = [
    'Chameleon==3.6.2', # form error in 3.8.1
    'zope.interface',
    'pyramid>=1.10.1',
    'pyramid_chameleon',
    'iso8601',
    'pytz',
    'translationstring',
    'bs4',    # alternative - 'html2text'
    # 'pillow' optional. required for extensions.images.
]

setupkw = dict(
      name='nive',
      version='1.3.15',
      description='Nive 3 base package',
      long_description=README + '\n\n' + CHANGES,
      long_description_content_type="text/markdown",
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.7"
      ],
      author='Arndt Droullier, Nive GmbH',
      author_email='info@nive.co',
      url='https://niveapps.com/',
      keywords='cms framework pyramid',
      license='GPL 3',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="nive"
)

setup(**setupkw)
