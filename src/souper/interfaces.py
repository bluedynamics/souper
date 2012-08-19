from zope.interface import (
    Interface,
    Attribute,
)
from zope.interface.common.mapping import IFullMapping


class ISoup(Interface):
    """The Container Interface.
    """

    soup_name = Attribute(u"The identifier of this Soup")
    nextrecordindex = Attribute(u"The next record index to use.")


    def add(record):
        """Add record to soup.

        @param record: IRecord implementation
        @return: intid for record
        """

    def query(**kw):
        """Query Soup for Records.

        @param kw: Keyword arguments defining the query
        @return: list of records
        """

    def rebuild(self):
        """replaces the catalog and reindex all records."""

    def reindex(record=None):
        """Reindex the catalog for this soup.

        if record is None reindex all records, otherwise a list of records is
        expected.
        """

    def __delitem__(record):
        """Delete Record from soup.

        If given record not contained in soup, raise ValueError.

        @param record: IRecord implementation
        @raise: ValueError if record not exists in this soup.
        """


class IRecord(IFullMapping):
    """The record Interface.
    """

    intid = Attribute("The intid of this record. No longint!")


class ICatalogFactory(Interface):
    """Factory for the catalog used for Soup.
    """

    def __call__(context):
        """Create and return the Catalog.

        @param return: zope.app.catalog.catalog.Catalog instance
        """


class IStorageLocator(Interface):

    def storage(soup_name):
        """return soup with given soup_name
        """


class IRecordIndexer(Interface):
    """Interface to lookup values for being indexed from record.
    """
    
    def __call__(context, default):
        """returns value to be indexed.
        """


class INodeAttributeIndexer(IRecordIndexer):
    """Indexer for single node attribute value.
    """


class INodeTextIndexer(IRecordIndexer):
    """Indexer combining several node attributes for fulltext search.
    
    All combined attribute values must be string.
    """