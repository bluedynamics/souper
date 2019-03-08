# -*- coding: utf-8 -*-
import doctest
import re
import unittest
import six


optionflags = (
    doctest.NORMALIZE_WHITESPACE
    | doctest.ELLIPSIS
    | doctest.REPORT_ONLY_FIRST_FAILURE
)

TESTFILES = ["soup.rst"]


class Py23DocChecker(doctest.OutputChecker):

    def check_output(self, want, got, optionflags):
        if want != got and six.PY2:
            # if running on py2, ignore any "u" prefixes in the output
            got = re.sub("(\\W|^)u'(.*?)'", "\\1'\\2'", got)
            got = re.sub("(\\W|^)u\"(.*?)\"", "\\1\"\\2\"", got)
            # also ignore "b" prefixes in the expected output
            # want = re.sub("b'(.*?)'", "'\\1'", want)
            # want = want.lstrip('ldap.')

        return doctest.OutputChecker.check_output(self, want, got, optionflags)


def test_suite():
    return unittest.TestSuite(
        [
            doctest.DocFileSuite(
                filename,
                optionflags=optionflags,
                checker=Py23DocChecker(),
            )
            for filename in TESTFILES
        ]
    )


if __name__ == "__main__":  # pragma NO COVERAGE
    unittest.main(defaultTest="test_suite")  # pragma NO COVERAGE
