"""
Core interface to the adsws-api, including data models and user facing
interfaces
"""

import warnings
import math
import json
import requests
import os
import six
import sys
from werkzeug.utils import cached_property
import json

from .exceptions import SolrResponseParseError, APIResponseError
from .config import SEARCH_URL, METRICS_URL
from .config import TOKEN_FILES, TOKEN_ENVIRON_VARS
from . import __version__

PY3 = sys.version_info > (3, )


class APIResponse(object):
    """
    Base class that represents an adsws-api http response
    """
    response = None

    def get_ratelimits(self):
        """
        Return the current, maximum, and reset rate limits from the response
        header as a dictionary. The values will be strings.
        """
        return {
            "limit": self.response.headers.get('X-RateLimit-Limit'),
            "remaining": self.response.headers.get('X-RateLimit-Remaining'),
            "reset": self.response.headers.get('X-RateLimit-Reset')
        }

    @classmethod
    def load_http_response(cls, HTTPResponse):
        """
        This method should return an instansitated class and set its response
        to the requests.Response object.
        """
        if not HTTPResponse.ok:
            raise APIResponseError(HTTPResponse.text)
        c = cls(HTTPResponse.text)
        c.response = HTTPResponse
        return c


class SolrResponse(APIResponse):
    """
    Base class for storing a solr response
    """

    def __init__(self, raw):
        """
        De-serialize a json string representing a solr response
        :param raw: complete json response from solr
        :type raw: basestring
        """
        self._raw = raw
        self.json = json.loads(raw)
        self._articles = None
        try:
            self.responseHeader = self.json['responseHeader']
            self.params = self.json['responseHeader']['params']
            self.response = self.json['response']
            self.numFound = self.response['numFound']
            self.docs = self.response['docs']
        except KeyError as e:
            raise SolrResponseParseError("{}".format(e))

    @property
    def articles(self):
        """
        articles getter
        """
        if self._articles is None:
            self._articles = []
            for doc in self.docs:
                self._articles.append(Article(**doc))
        return self._articles


class MetricsResponse(APIResponse):
    """
    Data structure that represents a response from the ads metrics service
    """

    def __init__(self, raw):
        self._raw = raw
        self.metrics = json.loads(raw)

    def __str__(self):
        return self.__unicode__() if PY3 else self.__unicode__().encode("utf-8")

    def __unicode__(self):
        return self.metrics


class Article(object):
    """
    An object to represent a single record in NASA's Astrophysical
    Data System.
    """

    def __init__(self, **kwargs):
        """
        :param kwargs: Set object attributes from kwargs
        """

        if "id" not in kwargs:
            warnings.warn(
                "No article id found -- on-demand attribute lookup will fail",
                RuntimeWarning
            )

        self._raw = kwargs
        for key, value in six.iteritems(kwargs):
            setattr(self, key, value)

    def __str__(self):
        return self.__unicode__() if PY3 else self.__unicode__().encode("utf-8")
        
    def __unicode__(self):
        author = self.first_author or "Unknown author"
        if self.author and len(self.author) > 1:
            author += " et al."

        return u"<{author} {year}, {bibcode}>".format(
            author=author,
            year=self.year,
            bibcode=self.bibcode,
        )

    def __eq__(self, other):
        if (not hasattr(self, 'bibcode') or not hasattr(other, 'bibcode') or
                self.bibcode is None or other.bibcode is None):
            raise TypeError("Cannot compare articles without bibcodes")
        return self.bibcode == other.bibcode

    def __ne__(self, other):
        return not self.__eq__(other)

    def keys(self):
        return self._raw.keys()

    def items(self):
        return self._raw.items()

    def iteritems(self):
        return six.iteritems(self._raw)

    @property
    def bibtex(self):
        """Return a BiBTeX entry for the current article."""
        raise NotImplementedError

    @property
    def references(self):
        """Retrieves reference list for the current article and stores them."""
        raise NotImplementedError

    @property
    def citations(self):
        """Retrieves citation list for the current article and stores them."""
        raise NotImplementedError

    @property
    def metrics(self):
        """Retrieves metrics for the current article and stores them."""
        raise NotImplementedError

    def build_reference_tree(self, depth=1, **kwargs):
        """
        Builds a reference tree for this paper.

        :param depth: [optional]
            The number of levels to fetch in the reference tree.

        :type depth:
            int

        :param kwargs: [optional]
            Keyword arguments to pass to ``ads.search``.


        :returns:
            A list of references to the current article, with pre-loaded
            references down by ``depth``.
        """

        raise NotImplementedError

    def build_citation_tree(self, depth=1, **kwargs):
        """
        Builds a citation tree for this paper.

        :param depth: [optional]
            The number of levels to fetch in the citation tree.

        :type depth:
            int

        :param kwargs: [optional]
            Keyword arguments to pass to ``ads.search``.


        :returns:
            A list of citation to the current article, with pre-loaded
            citation down by ``depth``.
        """

        raise NotImplementedError

    def _get_field(self, field):
        """
        Queries the api for a single field for the record by `id`.
        This method should only be called indirectly by cached properties.
        :param field: name of the record field to load
        """
        if not hasattr(self, "id") or self.id is None:
            raise APIResponseError("Cannot query an article without an id")
        sq = SearchQuery(q="id:{}".format(self.id), fl=field)
        value = next(sq).__getattribute__(field)
        self._raw[field] = value
        return value

    @cached_property
    def abstract(self):
        return self._get_field('abstract')

    @cached_property
    def aff(self):
        return self._get_field('aff')

    @cached_property
    def author(self):
        return self._get_field('author')

    @cached_property
    def citation_count(self):
        return self._get_field('citation_count')

    @cached_property
    def bibstem(self):
        return self._get_field('bibstem')

    @cached_property
    def database(self):
        return self._get_field('database')

    @cached_property
    def identifier(self):
        return self._get_field('identifier')

    @cached_property
    def first_author_norm(self):
        return self._get_field('first_author_norm')

    @cached_property
    def issue(self):
        return self._get_field('issue')

    @cached_property
    def keyword(self):
        return self._get_field('keyword')

    @cached_property
    def page(self):
        return self._get_field('page')

    @cached_property
    def property(self):
        return self._get_field('property')

    @cached_property
    def pub(self):
        return self._get_field('pub')

    @cached_property
    def pubdate(self):
        return self._get_field('pubdate')

    @cached_property
    def read_count(self):
        return self._get_field('read_count')

    @cached_property
    def title(self):
        return self._get_field('title')

    @cached_property
    def volume(self):
        return self._get_field('volume')

    @cached_property
    def year(self):
        return self._get_field('year')
    

class BaseQuery(object):
    """
    Represents an arbitrary query to the adsws-api
    """
    _session = None
    _token = None

    @property
    def token(self):
        """
        set the instance attribute `token` following the following logic,
        stopping whenever a token is found. Raises NoTokenFound is no token
        is found
        2. environment variables TOKEN_ENVIRON_VARS
        3. file containing plaintext as the contents in TOKEN_FILES
        """
        if self._token is None:
            for v in map(os.environ.get, TOKEN_ENVIRON_VARS):
                if v is not None:
                    self._token = v
                    return self._token
            for f in TOKEN_FILES:
                try:
                    with open(f) as fp:
                        self._token = fp.read().strip()
                        return self._token
                except IOError:
                    pass
            warnings.warn("No token found", RuntimeWarning)
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    @property
    def session(self):
        """
        http session interface, transparent proxy to requests.session
        """
        if self._session is None:
            self._session = requests.session()
            self._session.headers.update(
                {
                    "Authorization": "Bearer {}".format(self.token),
                    "User-Agent": "ads-api-client/{}".format(__version__),
                    "Content-Type": "application/json",
                }
            )
        return self._session

    def __call__(self):
        return self.execute()

    def execute(self):
        """
        Each subclass should define their own execute method
        """
        raise NotImplementedError


class SearchQuery(BaseQuery):
    """
    Represents a query to apache solr
    """
    HTTP_ENDPOINT = SEARCH_URL
    DEFAULT_FIELDS = ["author", "first_author", "bibcode", "id", "year"]

    def __init__(self, query_dict=None, q=None, fq=None, fl=DEFAULT_FIELDS,
                 sort=None, start=0, rows=50, max_pages=3, **kwargs):
        """
        constructor
        :param query_dict: raw query that will be sent unmodified. raw takes
            precedence over individually defined query params
        :type query_dict: dict
        :param q: solr "q" param (query)
        :param fq: solr "fq" param (filter query)
        :param fl: solr "fl" param (filter limit)
        :param sort: solr "sort" param (sort)
        :param start: solr "start" param (start)
        :param rows: solr "rows" param (rows)
        :param max_pages: Maximum number of pages to return. This value may
            be modified after instansiation to increase the number of results
        :param kwargs: kwargs to add to `q` as "key:value"
        """
        self._articles = []
        self.response = None  # current SolrResponse object
        self.max_pages = max_pages
        self.__iter_counter = 0  # Counter for our custom iterator method
        if query_dict is not None:
            query_dict.setdefault('rows', 50)
            query_dict.setdefault('start', 0)
            self._query = query_dict
        else:
            _ = {
                "q": q or '',
                "fq": fq,
                "fl": fl,
                "sort": sort,
                "start": start,
                "rows": rows,
            }
            # Filter out None values
            self._query = dict(
                (k, v) for k, v in six.iteritems(_) if v is not None
            )

            # Format and add kwarg (key, value) pairs to q
            if kwargs:
                _ = ['{}:"{}"'.format(k, v) for k, v in six.iteritems(kwargs)]
                self._query['q'] = '{} {}'.format(self._query['q'], ' '.join(_))

        assert self._query.get('rows') > 0, "rows must be greater than 0"
        assert self._query.get('q'), "q must not be empty"

    @property
    def articles(self):
        """
        Read-only articles attribute should not be modified directly, as
        it is used to gauge the progress of the query
        """
        return self._articles

    @property
    def progress(self):
        """
        Returns a string representation of the progress of the search such as
        "1234/5000", which refers to the number of results retrived / the
        total number of results found
        """
        if self.response is None:
            return "Query has not been executed"
        return "{}/{}".format(len(self.articles), self.response.numFound)

    @property
    def query(self):
        """
        Read-only query attribute should only be created at init. Create
        a new class instance to modify a query.
        SearchQuery.query represents the *next* query that will be executed
        """
        return self._query

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        """
        iterator method, for backwards compatibility with the list() workflow
        """
        # Allow immediate iteration without forcing a user to call .execute()
        # explicitly
        if self.response is None:
            self.execute()

        try:
            cur = self._articles[self.__iter_counter]
            # If no more articles, check to see if we should query for the
            # next page of results
        except IndexError:
            # If we already have all the results, then iteration is done.
            if len(self.articles) >= self.response.numFound:
                raise StopIteration("All records found")

            # if we have hit the max_pages limit, then iteration is done.
            page = math.ceil(len(self.articles)/self.query['rows'])
            if page > self.max_pages:
                raise StopIteration("Maximum number of pages queried")

            # We aren't on the max_page of results nor do we have all
            # results: execute the next query and yield from the newly
            # extended .articles array.
            self.execute()
            cur = self._articles[self.__iter_counter]

        self.__iter_counter += 1
        return cur

    def execute(self):
        """
        Sends the http request implied by the self.query
        In addition, set up the request such that we can call next()
        to provide the next page of results
        """
        self.response = SolrResponse.load_http_response(
            self.session.get(self.HTTP_ENDPOINT, params=self.query)
        )
        self._articles.extend(self.response.articles)
        self._query['start'] += self._query['rows']


class ExportQuery(BaseQuery):
    """
    Represents a query to the adsws export service
    """
    def __init__(self):
        raise NotImplementedError


class BigQuery(BaseQuery):
    """
    Represents a query to the adsws bigquery service
    """
    def __init__(self):
        raise NotImplementedError


class VisQuery(BaseQuery):
    """
    Represents a query to the adsws visualizations service
    """
    def __init__(self):
        raise NotImplementedError


class MetricsQuery(BaseQuery):
    """
    Represents a query to the adsws metrics service
    """

    HTTP_ENDPOINT = METRICS_URL

    def __init__(self, bibcodes):
        """
        :param bibcodes: Bibcodes to send to in the metrics query
        :type bibcodes: list or string
        """
        self.response = None  # current MetricsResponse object
        if isinstance(bibcodes, basestring):
            bibcodes = [bibcodes]
        self.bibcodes = bibcodes
        self.json_payload = json.dumps({"bibcodes": bibcodes})

    def execute(self):
        """
        Execute the http request to the metrics service
        """
        self.response = MetricsResponse.load_http_response(
            self.session.post(self.HTTP_ENDPOINT, data=self.json_payload)
        )
        return self.response


class query(SearchQuery):
    """
    Backwards compatible proxy to SearchQuery
    """
    def __init__(self, *args, **kwargs):
        """
        Override parent's __init__ to show the deprecation warning and
        re-construct the old query API into the newer SearchQuery api
        """
        warnings.warn(
            "ads.query will be deprectated. Use ads.SearchQuery in the future",
            DeprecationWarning
        )
        super(self.__class__, self).__init__(*args, **kwargs)


