import random
from zope.interface import implementer
from zope.component import (
    getUtility,
    queryAdapter,
)
from BTrees.IOBTree import IOBTree
from BTrees.Length import Length
from persistent import Persistent
from plumber import (
    default,
    plumber,
    Part,
)
from node.ext.zodb import OOBTNode
from .interfaces import (
    ISoup,
    IRecord,
    ICatalogFactory,
    IStorageLocator,
    INodeAttributeIndexer,
)


def get_soup(soup_name, context):
    return Soup(soup_name, context)


class SoupData(Persistent):

    def __init__(self):
        self.data = IOBTree()
        self.catalog = None
        self._length = Length()

    @property
    def length(self):
        return self._length

    def __len__(self):
        return self.length()


@implementer(ISoup)
class Soup(object):

    def __init__(self, soup_name, context):
        """initialize soup with its name and some context used in
        conjunction with the IStorageLocator adapter lookup.
        """
        self.soup_name = soup_name
        self.context = context

    @property
    def storage(self):
        locator = queryAdapter(self.context, IStorageLocator)
        if not locator:
            raise ValueError("Can't find IStorageLocator adapter for context "
                             "%s in order to locate soup '%s'." % \
                             (repr(self.context), self.soup_name))
        return locator.storage(self.soup_name)

    @property
    def data(self):
        return self.storage.data

    @property
    def catalog(self):
        """returns the catalog of the soup

        if the catalog does not exist it creates a new and empty catalog using
        the named utility ICatalogFactory.
        """
        storage = self.storage
        if not storage.catalog:
            factory = getUtility(ICatalogFactory, name=self.soup_name)
            storage.catalog = factory()
        return storage.catalog

    def add(self, record):
        """adds a new record to the soup, creates soup unique id and index it.
        """
        record.intid = self._generateid()
        self.data[record.intid] = record
        self.storage.length.change(1)
        self.catalog.index_doc(record.intid, record)
        return record.intid

    def query(self, queryobject, sort_index=None, limit=None, sort_type=None,
              reverse=False, names=None):
        result = self.catalog.query(queryobject, sort_index=sort_index,
                                    limit=limit, sort_type=sort_type,
                                    reverse=reverse, names=names)
        for iid in result[1]:
            yield self.data[iid]

    def lazy(self, queryobject, sort_index=None, limit=None, sort_type=None,
              reverse=False, names=None):
        result = self.catalog.query(queryobject, sort_index=sort_index,
                                    limit=limit, sort_type=sort_type,
                                    reverse=reverse, names=names)
        for iid in result[1]:
            yield LazyRecord(iid, self)

    def clear(self):
        self.storage.__init__()
        self.rebuild()

    def rebuild(self):
        """trashed the existing catalog and creates a new one using the
        named utility ICatalogFactory.
        """
        self.storage.catalog = getUtility(ICatalogFactory,
                                          name=self.soup_name)()
        self.reindex()

    def reindex(self, records=None):
        """reindex one or more specific records or all records.

        if records is not given all records are indexed. Otherwise for records
        an iterable of records is expected.
        """
        if records is None:
            records = self.data.values()
        for record in records:
            self.catalog.index_doc(record.intid, record)

    def __delitem__(self, record):
        """remove one specific record and unindex it.
        """
        try:
            del self.data[record.intid]
            self.storage.length.change(-1)
        except Exception, e:
            raise e
        self.catalog.unindex_doc(record.intid)

    _v_nextid = None
    _randrange = random.randrange

    def _generateid(self):
        # taken from zope.app.intid.
        while True:
            if self._v_nextid is None:
                self._v_nextid = self._randrange(0, 2 ** 31)
            intid = self._v_nextid
            self._v_nextid += 1
            if intid not in self.data:
                return intid
            self._v_nextid = None


class LazyRecord(object):

    def __init__(self, intid, soup):
        self.intid = intid
        self.soup = soup

    def __call__(self):
        return self.soup.data[self.intid]


@implementer(IRecord)
class RecordPart(Part):
    intid = default(None)


class Record(OOBTNode):
    __metaclass__ = plumber
    __plumbing__ = RecordPart


@implementer(INodeAttributeIndexer)
class NodeAttributeIndexer(object):

    def __init__(self, attr_key):
        self.attr_key = attr_key

    def __call__(self, nodecontext, default):
        if self.attr_key in nodecontext.attrs:
            return nodecontext.attrs[self.attr_key]
        return default
