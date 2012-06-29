Soup Creation
=============

Create object which can store soup data,

::

    >>> from zope.interface import implementer
    >>> from node.ext.zodb import OOBTNode
    >>> context = OOBTNode()
    
The we need some simple StorageLocator::

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
    ...        if soup_name not in self.context.attrs:
    ...            self.context.attrs[soup_name] = SoupData()
    ...        return self.context.attrs[soup_name]

    >>> provideAdapter(StorageLocator, adapts=[Interface], name='mysoup')

and query the soup named 'mysoup'.

If soup data for given soup id is not present yet, i will be created
transparently and annotated to ISoupAnnotatable.

::

    >>> from souper.soup import get_soup
    >>> soup = get_soup('mysoup', context)
    >>> soup
    <souper.soup.Soup object at 0x...>

Our catalog factory. You MUST provide an ICatalogFactory implementation for each
soup. It must be registered as utility with desired soup id.

::

    >>> from zope.component import getUtility
    >>> from souper.interfaces import ICatalogFactory
    >>> catalogfactory = getUtility(ICatalogFactory, name='mysoup')
    Traceback (most recent call last):
    ...
        raise ComponentLookupError(interface, name)
    ComponentLookupError: (<InterfaceClass souper.interfaces.ICatalogFactory>, 'mysoup')
    
    >>> from zope.component import provideUtility
    >>> from repoze.catalog.catalog import Catalog
    >>> from repoze.catalog.indexes.field import CatalogFieldIndex    
    >>> from repoze.catalog.indexes.text import CatalogTextIndex
    >>> from repoze.catalog.indexes.keyword import CatalogKeywordIndex
    >>> from souper.soup import NodeAttributeIndexer
    
    >>> @implementer(ICatalogFactory)
    ... class MySoupCatalogFactory(object):
    ...
    ...     def __call__(self):
    ...         catalog = Catalog()
    ...         userindexer = NodeAttributeIndexer('user')
    ...         catalog[u'user'] = CatalogFieldIndex(userindexer)
    ...         textindexer = NodeAttributeIndexer('user')
    ...         catalog[u'text'] = CatalogTextIndex(textindexer)
    ...         keywordindexer = NodeAttributeIndexer('keywords')
    ...         catalog[u'keywords'] = CatalogKeywordIndex(keywordindexer)
    ...         return catalog
    
    >>> provideUtility(MySoupCatalogFactory(), name="mysoup")
    >>> catalogfactory = getUtility(ICatalogFactory, name='mysoup')
    >>> catalogfactory
    <MySoupCatalogFactory object at 0x...>

    >>> catalog = catalogfactory()
    >>> catalog.__class__
    <class 'repoze.catalog.catalog.Catalog'>
    
    >>> sorted(catalog.items())
    [(u'keywords', <repoze.catalog.indexes.keyword.CatalogKeywordIndex object at 0x...>), 
    (u'text', <repoze.catalog.indexes.text.CatalogTextIndex object at 0x...>), 
    (u'user', <repoze.catalog.indexes.field.CatalogFieldIndex object at 0x...>)]
    
    
Record
======

Create a Record and add it to soup.::

    >>> from souper.soup import Record
    >>> record = Record()
    >>> record.attrs['user'] = 'user1'
    >>> record.attrs['text'] = u'foo bar baz'
    >>> record.attrs['keywords'] = [u'1', u'2', u'ü']
    >>> rid = soup.add(record)
    
Query
=====

Check querying::

    >>> from repoze.catalog.query import Eq 
    >>> [r for r in soup.query(Eq('user', 'user1'))]
    [<Record object 'None' at ...>]

    >>> [r for r in soup.query(Eq('user', 'nonexists'))]
    []

Add some more Records::

    >>> record = Record()
    >>> record.attrs['user'] = 'user1'
    >>> record.attrs['text'] = u'foo bar bam'
    >>> record.attrs['keywords'] = [u'1', u'3', u'4']
    >>> rid = soup.add(record)    
    >>> record = Record()
    >>> record.attrs['user'] = 'user2'
    >>> record.attrs['text'] = u'foo x y'
    >>> record.attrs['keywords'] = [u'1', u'4', u'5']
    >>> rid = soup.add(record)    
    >>> u1records = [r for r in soup.query(user=2*('user1',))]
    >>> u1records
    [<Record object 'None' at ...>, <Record object 'None' at ...>]

Change user attribute of one record::

    >>> u1records[0].attrs['user'] = 'user2'

The query still returns the old result. The Record must be reindexed::

    >>> len(list(soup.query(user=2*('user1',))))
    2

    >>> soup.reindex([u1records[0]])
    >>> len(list(soup.query(user=2*('user1',))))
    1

    >>> len(list(soup.query(user=2*('user2',))))
    2

Check Text index::

    >>> len(list(soup.query(text='foo')))
    3

    >>> len(list(soup.query(text='bar')))
    2

    >>> len(list(soup.query(text='x')))
    1

    >>> len(list(soup.query(text='fo')))
    0

Check keyword index::

    >>> len(list(soup.query(keywords=['1'])))
    3
    
    >>> len(list(soup.query(keywords=[u'ü'])))
    1

You can reindex all records in soup at once::

    >>> all = [r for r in soup.data.values()]
    >>> all = sorted(all, key=lambda x: x.attrs['user'])
    >>> len(all)
    3

    >>> all[-1].attrs['user'] = 'user3'
    >>> soup.reindex()
    >>> len(list(soup.query(user=2*('user3',))))
    1
    
Rebuild
=======

You can also rebuild the catalog. In this case the catalog factory is called
again and the new catalog is used. Lets modify catalog of our catalog factory.
Never do this in production evironments::

    >>> from collective.soup.interfaces import INodeAttributeIndexer
    >>> from zope.catalog.field import FieldIndex
    >>> catalogfactory = getUtility(ICatalogFactory, name='mysoup')
    >>> catalogfactory.catalog[u'name'] = FieldIndex(field_name='name',
    ...                                   interface=INodeAttributeIndexer)
    >>> catalogfactory.catalog[u'name']
    <zope.catalog.field.FieldIndex object at ...>

Set name attribute on some record data, reindex soup and check results::

    >>> all[0].attrs['name'] = 'name'
    >>> all[1].attrs['name'] = 'name'
    >>> all[2].attrs['name'] = 'name'
    >>> soup.reindex()
    >>> len(list(soup.query(name=2*('name',))))
    3

Delete
======

Delete records::

    >>> del soup[all[0]]
    >>> len(list(soup.query(name=2*('name',))))
    2
    
LazyRecords
===========

For huge expected results we can query LazyRecords. They return the real record
on call::

    >>> lazy = [l for l in soup.lazy(name=2*('name',))]
    >>> lazy
    [<collective.soup.soup.LazyRecord object at ...>,
    <collective.soup.soup.LazyRecord object at ...>]

    >>> lazy[0]()
    <Record object 'None' at ...>

    >>> soup = getSoup(site, u'mysoup')
    >>> len(list(soup.query(name=2*('name',))))
    2

Clear soup
==========

::

    >>> soup.clear()
    >>> len(soup.data)
    0
