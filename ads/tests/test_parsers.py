from .. import parser as parse

def test_date_parser():

    assert parse.dates(2002)                == " pubdate:[2002 TO 2002]"
    assert parse.dates(2002.)               == " pubdate:[2002 TO 2002]"
    assert parse.dates("2002")              == " pubdate:[2002 TO 2002]"
    assert parse.dates("2002-07")           == " pubdate:[2002-07 TO 2002-07]"
    assert parse.dates("2002-07-15")        == " pubdate:[2002-07 TO 2002-07]"
    assert parse.dates("2002/07")           == " pubdate:[2002-07 TO 2002-07]"
    assert parse.dates("2002..2005")        == " pubdate:[2002-01 TO 2005-12]"
    assert parse.dates("2002..05")          == " pubdate:[2002-01 TO 2005-12]"
    assert parse.dates("2002-01..2006/07")  == " pubdate:[2002-01 TO 2006-07]"
    assert parse.dates((2002, 2005))        == " pubdate:[2002-01 TO 2005-12]"
    assert parse.dates((2002, 2005))        == " pubdate:[2002-01 TO 2005-12]"
    assert parse.dates((2002, ))            == " pubdate:[2002-01 TO *]"
    assert parse.dates((None, 2002))        == " pubdate:[* TO 2002-12]"
    assert parse.dates(2002.02)             == " pubdate:[2002-02 TO 2002-02]"
    assert parse.dates("2002/05..08")       == " pubdate:[2002-05 TO 2008-12]"
    assert parse.dates("2002-")             == " pubdate:[2002-01 TO *]"
    assert parse.dates("2002..")            == " pubdate:[2002-01 TO *]"
    assert parse.dates("..2002")            == " pubdate:[* TO 2002-12]"
    assert parse.dates("-2002")             == " pubdate:[* TO 2002-12]"



def test_ordering():

    order_options = ("asc", "desc", )
    sort_options = {
        "cited": "cited",
        "citations": "cited",
        "date": "date",
        "time": "date",
        "popular": "popularity",
        "popularity": "popularity",
        "relevance": "relevance"
    }

    for sort_input, sort_option in sort_options.iteritems():
        for order_option in order_options:
            
            assert (sort_option.lower(), order_option.lower()) == parse.ordering(sort_input, order_option)
            assert (sort_option.lower(), order_option.lower()) == parse.ordering(sort_input, order_option.upper())
            assert (sort_option.lower(), order_option.lower()) == parse.ordering(sort_input.upper(), order_option)
