"""
Tests for SearchQuery and it's query proxy class.
"""
import unittest

from mocks import MockSolrResponse

from ads.core import SearchQuery, query


class TestSearchQuery(unittest.TestCase):
    """
    Tests for SearchQuery. Depends on SolrResponse.
    """

    def test_iter(self):
        """
        the iteration method should handle pagination automatically
        based on rows and max_rows; use the mock solr server to query
        data row by row and ensure that the data return as expected
        """

        sq = SearchQuery(q="unittest", rows=1, max_pages=20)
        with MockSolrResponse(sq.api_endpoint):
            self.assertEqual(sq._query['start'], 0)
            self.assertEqual(next(sq).bibcode, '1971Sci...174..142S')
            self.assertEqual(len(sq.articles), 1)
            self.assertEqual(sq._query['start'], 1)
            self.assertEqual(next(sq).bibcode, '2012GCN..13229...1S')
            self.assertEqual(len(list(sq)), 19)  # 2 already returned
            with self.assertRaisesRegexp(
                    StopIteration,
                    "Maximum number of pages queried"):
                next(sq)
            sq.max_pages = 500
            self.assertEqual(len(list(sq)), 28-19-2)
            with self.assertRaisesRegexp(
                    StopIteration,
                    "All records found"):
                next(sq)



if __name__ == '__main__':
    unittest.main(verbosity=2)
