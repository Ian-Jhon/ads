# coding: utf-8

""" Searching for publications through NASA's ADS system. """

from __future__ import division, print_function

__author__ = "Andy Casey <acasey@mso.anu.edu.au>"

# Standard library
import json
import logging
import multiprocessing
import time

# Third party
import requests
import requests_futures.sessions

# Module specific
import parser as parse
from utils import get_dev_key, get_api_settings

__all__ = ['search']

DEV_KEY = get_dev_key()
ADS_HOST = 'http://adslabs.org/adsabs/api/search/'


class Article(object):
    """An object to represent a single publication in NASA's Astrophysical
    Data System."""

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        return None

    # TODO __repr__

    # TODO bibtex @property

    @property
    def references(self):
        if hasattr(self, '_references'):
            return self._references

        else:
            articles, metadata, request = search("references(bibcode:{bibcode})"
                .format(bibcode=self.bibcode), rows=200)
            self._references = articles
            return articles

    @property
    def citations(self):
        if hasattr(self, '_citations'):
            return self._citations

        else:
            articles, metadata, request = search("citations(bibcode:{bibcode})"
                .format(bibcode=self.bibcode), rows=200)
            self._citations = articles
            return articles


    def build_reference_tree(self, depth):
        """Builds a reference tree for this paper.

        Inputs
        ------
        depth : int
            The number of levels to fetch in the reference tree.

        Returns
        -------
        num_articles_in_tree : int
            The total number of referenced articles in the reference tree.
        """

        try: depth = int(depth)
        except TypeError:
            raise TypeError("depth must be an integer-like type")

        if depth < 1:
            raise ValueError("depth must be a positive integer")

        session = requests_futures.sessions.FuturesSession()

        # To understand recursion, first you must understand recursion.
        level = [self]
        total_articles = len(level)

        for level_num in xrange(depth):

            level_requests = []
            for article in level:
                payload = _build_payload("references(bibcode:{bibcode})"
                    .format(bibcode=article.bibcode))

                level_requests.append(session.get(ADS_HOST, params=payload))

            # Complete all requests
            new_level = []
            for request, article in zip(level_requests, level):
                data = request.result().json()["results"]["docs"]

                setattr(article, "_references", [Article(**doc_info) for doc_info in data])
                new_level.extend(article.references)

            level = sum([new_level], [])
            total_articles += len(level)

        return total_articles          


    def build_citation_tree(self, depth):
        """Builds a citation tree for this paper.

        Inputs
        ------
        depth : int
            The number of levels to fetch in the citation tree.

        Returns
        -------
        num_articles_in_tree : int
            The total number of cited articles in the citation tree.
        """

        try: depth = int(depth)
        except TypeError:
            raise TypeError("depth must be an integer-like type")

        if depth < 1:
            raise ValueError("depth must be a positive integer")

        session = requests_futures.sessions.FuturesSession()

        # To understand recursion, first you must understand recursion.
        level = [self]
        total_articles = len(level)

        for level_num in xrange(depth):

            level_requests = []
            for article in level:
                payload = _build_payload("citations(bibcode:{bibcode})"
                    .format(bibcode=article.bibcode))

                level_requests.append(session.get(ADS_HOST, params=payload))

            # Complete all requests
            new_level = []
            for request, article in zip(level_requests, level):
                data = request.result().json()["results"]["docs"]

                setattr(article, "_citations", [Article(**doc_info) for doc_info in data])
                new_level.extend(article.citations)

            level = sum([new_level], [])
            total_articles += len(level)

        return total_articles     




def _build_payload(query=None, authors=None, dates=None, affiliation=None, 
    sort='date', order='desc', start=0, rows=20):
    """Builds a dictionary payload for NASA's ADS based on the input criteria."""

    query = parse.query(query, authors, dates)

    # Check inputs
    start = parse.start(start)
    rows = parse.rows(rows)
    sort, order = parse.ordering(sort, order)

    # Filters
    date_filter = parse.dates(dates)
    affiliation_filter = parse.affiliation(affiliation)

    filters = (date_filter, affiliation_filter)
    for query_filter in filters:
        if query_filter is not None:
            query += query_filter

    payload = {
        "q": query,
        "dev_key": DEV_KEY,
        "sort": "{sort} {order}".format(sort=sort.upper(), order=order),
        "start": start,
        "fmt": "json",
        "rows": rows,
        "filter": "database:astronomy" # For the moment,..
        }

    return payload


def search(query=None, authors=None, dates=None, affiliation=None,
    sort='date', order='desc', start=0, rows=20):
    """Search ADS and retrieve Article objects."""

    payload = _build_payload(**locals())

    r = requests.get(ADS_HOST, params=payload)
    
    if r.status_code == 200:

        results = r.json()
        metadata = results['meta']

        articles = []
        for docinfo in results['results']['docs']:
            articles.append(Article(**docinfo))

        return articles
        return (articles, metadata, r)



    else:
        return r # For debugging -- remove this later
        return (False, {
                'error': r.text
            })