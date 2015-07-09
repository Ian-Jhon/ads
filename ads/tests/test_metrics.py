"""
Tests for MetricsQuery
"""
import unittest

from .mocks import MockMetricsResponse

from ads.metrics import MetricsQuery, MetricsResponse
from ads.config import METRICS_URL


class TestMetricsQuery(unittest.TestCase):
    """
    test the MetricsQuery object
    """

    def test_init(self):
        """
        an initialized MetricsQuery object should have a bibcode attributes
        that is a list
        """
        self.assertEqual(MetricsQuery('bibcode').bibcodes, ['bibcode'])
        self.assertEqual(MetricsQuery(['b1', 'b2']).bibcodes, ['b1', 'b2'])

    def test_execute(self):
        """
        MetricsQuery.execute() should return a MetricsResponse object, and
        that object should be set as the .response attribute
        """
        mq = MetricsQuery('bibcode')
        with MockMetricsResponse(METRICS_URL):
            retval = mq.execute()
        self.assertIsInstance(mq.response, MetricsResponse)
        self.assertEqual(retval, mq.response.metrics)


class TestMetricsResponse(unittest.TestCase):
    """
    test MetricsResponse object
    """

    def test_init(self):
        """
        """
        pass

if __name__ == '__main__':
    unittest.main(verbosity=2)