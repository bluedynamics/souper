import unittest
import doctest

optionflags = doctest.NORMALIZE_WHITESPACE | \
              doctest.ELLIPSIS | \
              doctest.REPORT_ONLY_FIRST_FAILURE

TESTFILES = [
    'soup.rst',
]


def test_suite():
    return unittest.TestSuite([
        doctest.DocFileSuite(
            filename,
            optionflags=optionflags,
        ) for filename in TESTFILES
    ])


if __name__ == '__main__':                                # pragma NO COVERAGE
    unittest.main(defaultTest='test_suite')               # pragma NO COVERAGE
