from setuptools import setup, find_packages
import os

version = '1.0'
shortdesc = \
'Souper - Generic Indexed Storage based on ZODB'
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'HISTORY.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'LICENSE.rst')).read()
tests_require = ['interlude']

setup(name='souper',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Software Development',
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
            'License :: OSI Approved :: BSD License',
      ],
      keywords='zodb zope pyramid node plone',
      author='BlueDynamics Alliance',
      author_email='dev@bluedynamics.com',
      url=u'http://packages.python.org/souper',
      license='Simplified BSD',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['souper'],
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          'setuptools',
          'node.ext.zodb',
          'repoze.catalog',
      ],
      tests_require=tests_require,
      test_suite="souper.tests.test_suite",
      extras_require = dict(
          test=tests_require,
      ),
)
