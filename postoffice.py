"""Fetches data for post office savings accounts"""

import urllib2
from lxml.etree import HTML
import re
import json


def main():
    s = urllib2.urlopen('http://www.postoffice.co.uk/interest-rates')
    page = s.read()
    tree = HTML(page)
    account_details = map(parse_table, get_account_tables(tree))
    print json.dumps(account_details)

def get_account_tables(tree):
    "Extract the tables containing interest rates"
    return tree.xpath('//article[@id="overview"]//table[//*[contains(text(), "Minimum Balance")]]')

def get_account_meta(tree):
    name_string = ' '.join(tree.xpath('./preceding::strong[position()=1]/text()'))


    questionable = False
    if 'only applies to' in name_string:
        effective_date = None
    elif '(' in name_string:
        m = re.search(
            r"\(accounts opened on or after (.*)\)", name_string)
        if m is None:
            questionable = True
            effective_date = None
        else:
            effective_date = m.group(1)
            
    else:
        effective_date = None

    name = re.sub(r'\([^)]+\)', '', name_string).strip()
    return dict(name=name, effective_date=effective_date,
        questionable=questionable)


def parse_table(tree):
    "Pull out information from an account table"
    meta_details = get_account_meta(tree)

    try:
        header_row, good_rate_row = tree.xpath('.//tr')
        bad_rate_row = None
    except ValueError:
        header_row, good_rate_row, bad_rate_row = tree.xpath('.//tr')

    check_header_row(header_row)

    rate_string = good_rate_row.xpath('./td/text()')[2]
    rate = parse_percent(rate_string)

    if bad_rate_row is not None:
        check_row_has_good_rate(good_rate_row)

    return dict(meta_details, rate=rate)

def check_header_row(header_row):
    _empty, _balance, aer, _gross = header_row.xpath('td')
    aer_string =  aer.xpath('string()')

    assert 'Current' in aer_string and 'AER' in aer_string, aer_string

def check_row_has_good_rate(row):
    "Check that this row is actually the row for a good rate"
    cell_text = row.xpath('td[position()=1]/text()')[0]
    if 'Including 12 month introductory bonus' in cell_text:
        return
    elif 'Including 12 month bonus from account' in cell_text:
        return
    elif 'Including 18 month bonus from account' in cell_text:
        return
    else:
        raise ValueError(cell_text)

#--- UTILITY FUNCTIONS

def parse_percent(string):
    "Parse a percentage strictly"
    assert string[-1] == '%'
    return float(string[:-1]) / 100


if __name__ == '__main__':
    main()

