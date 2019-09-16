# -*- coding: utf-8 -*-
from BTrees.IOBTree import IOBTree
from BTrees.Length import Length
from node.ext.zodb import OOBTNode
from persistent import Persistent
from plumber import Behavior
from plumber import default
from plumber import plumbing
from souper.interfaces import ICatalogFactory
from souper.interfaces import INodeAttributeIndexer
from souper.interfaces import INodeTextIndexer
from souper.interfaces import IRecord
from souper.interfaces import ISoup
from souper.interfaces import IStorageLocator
from zope.component import getUtility
from zope.component import queryAdapter
from zope.interface import implementer
import random
import six


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
        """Initialize soup with its name and some context used in
        conjunction with the IStorageLocator adapter lookup.
        """
        self.soup_name = soup_name
        self.context = context

    @property
    def storage(self):
        locator = queryAdapter(self.context, IStorageLocator)
        if not locator:
            raise ValueError(
                "Can't find IStorageLocator adapter for context "
                "%s in order to locate soup '%s'."
                % (repr(self.context), self.soup_name)
            )
        return locator.storage(self.soup_name)

    @property
    def data(self):
        return self.storage.data

    @property
    def catalog(self):
        """Return the catalog of the soup.

        If the catalog does not exist it creates a new and empty catalog using
        the named utility ICatalogFactory.
        """
        storage = self.storage
        if not storage.catalog:
            factory = getUtility(ICatalogFactory, name=self.soup_name)
            storage.catalog = factory(self.context)
        return storage.catalog

    def get(self, intid):
        return self.data[intid]

    def add(self, record):
        """Add a new record to the soup, create soup unique id and index it.
        """
        record.intid = self._generateid()
        self.data[record.intid] = record
        self.storage.length.change(1)
        self.catalog.index_doc(record.intid, record)
        return record.intid

    def query(
        self,
        queryobject,
        sort_index=None,
        limit=None,
        sort_type=None,
        reverse=False,
        names=None,
        with_size=False,
    ):
        size, iids = self.catalog.query(
            queryobject,
            sort_index=sort_index,
            limit=limit,
            sort_type=sort_type,
            reverse=reverse,
            names=names,
        )
        if with_size:
            yield size
        for iid in iids:
            yield self.data[iid]

    def lazy(
        self,
        queryobject,
        sort_index=None,
        limit=None,
        sort_type=None,
        reverse=False,
        names=None,
        with_size=False,
    ):
        size, iids = self.catalog.query(
            queryobject,
            sort_index=sort_index,
            limit=limit,
            sort_type=sort_type,
            reverse=reverse,
            names=names,
        )
        if with_size:
            yield size
        for iid in iids:
            yield LazyRecord(iid, self)

    def clear(self):
        self.storage.__init__()
        self.rebuild()

    def rebuild(self):
        """Drop the existing catalog and create a new one using the
        named utility ICatalogFactory.
        """
        self.storage.catalog = getUtility(
            ICatalogFactory, name=self.soup_name
        )(self.context)
        self.reindex()

    def reindex(self, records=None):
        """Reindex one or more specific records or all records.

        If records is not given all records are indexed. Otherwise for records
        an iterable of records is expected.
        """
        if records is None:
            records = self.data.values()
        for record in records:
            self.catalog.index_doc(record.intid, record)

    def __delitem__(self, record):
        """Remove one specific record and unindex it.
        """
        try:
            del self.data[record.intid]
            self.storage.length.change(-1)
        except Exception as e:
            raise e
        self.catalog.unindex_doc(record.intid)

    _v_nextid = None
    _randrange = random.randrange

    def _generateid(self):
        # Taken from zope.app.intid.
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
class RecordBehavior(Behavior):
    intid = default(None)


@plumbing(RecordBehavior)
class Record(OOBTNode):
    pass


@implementer(INodeAttributeIndexer)
class NodeAttributeIndexer(object):

    def __init__(self, attr):
        self.attr = attr

    def __call__(self, context, default):
        if self.attr in context.attrs:
            return context.attrs[self.attr]
        return default


@implementer(INodeTextIndexer)
class NodeTextIndexer(object):

    def __init__(self, attrs):
        self.attrs = attrs

    def __call__(self, context, default):
        values = list()
        for attr in self.attrs:
            value = context.attrs.get(attr, u"")
            if isinstance(value, six.binary_type):
                value = value.decode("utf-8")
            if not isinstance(value, six.string_types):
                value = str(value)
            value = value.strip()
            if not value:
                continue
            values.append(value)
        if not values:
            return default
        return u" ".join(values)
