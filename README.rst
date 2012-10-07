ZODB Storage for lots of (light weight) data. Utilizes
`repoze.catalog <http://pypi.python.org/pypi/repoze.catalog>`_,
`ZODB BTrees <http://www.zodb.org/documentation/guide/modules.html#btrees-package>`_,
`node <http://pypi.python.org/pypi/node>`_ (and ``node.ext.zodb``).

Souper is a tool for programmers. It offers an integrated storage tied together
with indexes in a catalog. The records in the storage are generic. It is
possible to store any data on a record if it is persistent pickable in ZODB.

Souper can be used used in any python application using the ZODB, such as
`Pyramid <http://docs.pylonsproject.org/en/latest/docs/pyramid.html>`_ or
`Plone <http://plone.org>`_.


Using Souper
============


Providing a Locator
-------------------

Soups are looked up by adapting ``souper.interfaces.IStorageLocator`` to
some context. Souper does not provide any default locator. So first one need
to be provided. Let's assume context is some persistent dict-like instance::

    >>> from zope.interface import implementer
    >>> from zope.interface import Interface
    >>> from zope.component import provideAdapter 
    >>> from souper.interfaces import IStorageLocator    
    >>> from souper.soup import SoupData
    >>> @implementer(IStorageLocator)
    ... class StorageLocator(object):
    ...     
    ...     def __init__(self, context):
    ...        self.context = context
    ...
    ...     def storage(self, soup_name):
    ...        if soup_name not in self.context:
    ...            self.context[soup_name] = SoupData()
    ...        return self.context[soup_name]

    >>> provideAdapter(StorageLocator, adapts=[Interface])
 
So we have locator creating soups by name on the fly. Now its easy to get a soup
by name::

    >>> from souper.soup import get_soup
    >>> soup = get_soup('mysoup', context)
    >>> soup
    <souper.soup.Soup object at 0x...>


Providing a Catalog Factory
---------------------------

Depending on your needs the catalog and its indexes may look different from
use-case to use-case. The catalog factory is responsible to create a catalog
for a soup. The factory is a named utility implementing ``souper.interfaces.ICatalogFactory``.
The name of the utility has to the the same as the soup have.

Here ``repoze.catalog`` is used and to let the indexes access the data on the
records by key the ``NodeAttributeIndexer`` is used. For special cases one may
write its custom indexers, but the default one is fine most of the time:: 

    >>> from souper.interfaces import ICatalogFactory
    >>> from souper.soup import NodeAttributeIndexer
    >>> from zope.component import provideUtility
    >>> from repoze.catalog.catalog import Catalog
    >>> from repoze.catalog.indexes.field import CatalogFieldIndex    
    >>> from repoze.catalog.indexes.text import CatalogTextIndex
    >>> from repoze.catalog.indexes.keyword import CatalogKeywordIndex
    
    >>> @implementer(ICatalogFactory)
    ... class MySoupCatalogFactory(object):
    ...
    ...     def __call__(self, context=None):
    ...         catalog = Catalog()
    ...         userindexer = NodeAttributeIndexer('user')
    ...         catalog[u'user'] = CatalogFieldIndex(userindexer)
    ...         textindexer = NodeAttributeIndexer('text')
    ...         catalog[u'text'] = CatalogTextIndex(textindexer)
    ...         keywordindexer = NodeAttributeIndexer('keywords')
    ...         catalog[u'keywords'] = CatalogKeywordIndex(keywordindexer)
    ...         return catalog
    
    >>> provideUtility(MySoupCatalogFactory(), name="mysoup")
 
The catalog factory is used soup-internal only but one may want to check if it
works fine:: 

    >>> catalogfactory = getUtility(ICatalogFactory, name='mysoup')
    >>> catalogfactory
    <MySoupCatalogFactory object at 0x...>

    >>> catalog = catalogfactory()
    >>> sorted(catalog.items())
    [(u'keywords', <repoze.catalog.indexes.keyword.CatalogKeywordIndex object at 0x...>), 
    (u'text', <repoze.catalog.indexes.text.CatalogTextIndex object at 0x...>), 
    (u'user', <repoze.catalog.indexes.field.CatalogFieldIndex object at 0x...>)]
        

Adding records
--------------

As mentioned above the ``souper.soup.Record`` is the one and only kind of data
added to the soup. A record has attributes containing the data::

    >>> from souper.soup import get_soup
    >>> from souper.soup import Record
    >>> soup = get_soup('mysoup', context)
    >>> record = Record()
    >>> record.attrs['user'] = 'user1'
    >>> record.attrs['text'] = u'foo bar baz'
    >>> record.attrs['keywords'] = [u'1', u'2', u'ü']
    >>> record_id = soup.add(record)

A record may contains other records. But to index them one would need a custom
indexer, so usally conatined records are valuable for later display, not for
searching:: 

    >>> record['subrecord'] = Record()
    >>> record['homeaddress'].attrs['zip'] = '6020'
    >>> record['homeaddress'].attrs['town'] = 'Innsbruck'
    >>> record['homeaddress'].attrs['country'] = 'Austria'


Access data
-----------

Even without any query a record can be fetched by id::

    >>> from souper.soup import get_soup
    >>> soup = get_soup('mysoup', context)
    >>> record = soup.get(record_id)

All records can be accessed using utilizing the container BTree::    
    
    >>> soup.data.keys()[0] == record_id
    True


Query data
----------

`How to query a repoze catalog is documented well. <http://docs.repoze.org/catalog/usage.html#searching>`_
Sorting works the same too. Queries are passed to soups ``query`` method (which
uses then repoze catalog). It returns a generator:: 

    >>> from repoze.catalog.query import Eq 
    >>> [r for r in soup.query(Eq('user', 'user1'))]
    [<Record object 'None' at ...>]

    >>> [r for r in soup.query(Eq('user', 'nonexists'))]
    []

To also get the size of the result set pass a ``with_size=True`` to the query.
The first item returned by the generator is the size::
    
    >>> [r for r in soup.query(Eq('user', 'user1'), with_size-True)]
    [1, <Record object 'None' at ...>]
    
    
To optimize handling of large result sets one may not to fetch the record but a
generator returning light weight objects. Records are fetched on call::

    >>> lazy = [l for l in soup.lazy(Eq('name', 'name'))]
    >>> lazy
    [<souper.soup.LazyRecord object at ...>, 
    
    >>> lazy[0]()
    <Record object 'None' at ...>

Here the size is passed as first value of the geneartor too if ``with_size=True``
is passed.


Delete a record
---------------

To remove a record from the soup python ``del`` is used like one would do on
any dict:: 

    >>> del soup[record_id]


Reindex
-------

After a records data changed it needs a reindex::

    >>> record.attrs['user'] = 'user1'
    >>> soup.reindex(records=[record])

Sometimes one may want to reindex all data. Then ``reindex`` has to be
called without parameters. It may take a while::

    >>> soup.reindex()


Rebuild catalog
---------------

Usally after a change of catalog factory was made - i.e. some index was added -
a rebuild of the catalog i needed. It replaces the current catalog with a new
one created by the catalog factory and reindexes all data. It may take while::   

    >>> soup.rebuild()


Reset (or clear) the soup
-------------------------

To remove all data from the soup and empty and rebuild the catalog call
``clear``. Attention: all data is lost!

::

    >>> soup.clear()


Installation Notes
==================

In order to use souper ``node.ext.zodb`` is needed. As this beta was released
there was no release (will be done soon). Please check
`pypi <http://pypi.python.org>`_ if it is there, otherwise please fetch
`node.ext.zodb from github <https://github.com/bluedynamics/node.ext.zodb>`_


Source Code
===========

The sources are in a GIT DVCS with its main branches at
`github <http://github.com/bluedynamics/souper>`_.

We'd be happy to see many forks and pull-requests to make souper even better.


Contributors
============

- Robert Niederreiter <rnix [at] squarewave [dot] at>

- Jens W. Klein <jk [at] kleinundpartner [dot] at>
