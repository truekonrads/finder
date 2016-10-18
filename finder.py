#!/usr/bin/python
# By Konrads Smelkovs 

import json
from urllib2 import urlopen, Request, ProxyHandler, build_opener, HTTPError
from urllib import urlencode
from pprint import pprint
from urlparse import urlparse
import sys
import argparse
import os

# proxy_handler = ProxyHandler({'http': 'http://localhost:8080/',
# 'https': 'http://localhost:8080/'})
proxy_handler = ProxyHandler()
opener = build_opener(proxy_handler)
MAX_REQS = 50
ENDPOINT = "https://api.datamarket.azure.com/Bing/Search/Composite?"
KEY = ''
if KEY=='':
    print "You need a Bing API key from Azure Data Market. It's free: http://datamarket.azure.com/dataset/bing/search"
    sys.exit(-1)

class Bing(object):

    def __init__(self, key):
        self.key = key

    def query(self, query, maxreq=MAX_REQS, skip=0):
        url = ENDPOINT + urlencode({
            '$format': 'json',
            'Query': "'%s'" % query,
            '$top': maxreq,
            '$skip': skip,
            'Sources': "'web'"
        })
        basic_auth = "%s:%s" % (KEY, KEY)
        request = Request(url, None, {
                          'Authorization': "Basic " + basic_auth.encode('base64').replace("\n", "")})
        # print ">>URL: %s" % request.get_full_url()
        # pprint(request.header_items())
        try:
            content = opener.open(request)
        except HTTPError, e:
            if e.code == 400:
                print content.read()
            raise e
        result = json.loads(content.read())
        # pprint (result['d']['results'][0]['WebTotal'])
        # pprint(result['d']['results'][-1])
        return result['d']['results'][0]


def main():
    import sys
    for start_host in sys.argv[1:]:
        b = Bing(KEY)
        query = "site:%s " % start_host

        hosts = []
        while True:
            found_new_hosts = False
            query += " ".join(map(lambda x: "-site:%s " % x, hosts))
            try:
                res = b.query(query)
                lastgood = query
                # print query
                for result in res['Web']:
                    # pprint(result)
                    host = urlparse(result['Url']).hostname
                    # print host
                    if host not in hosts:
                        found_new_hosts = True
                        print "DEBUG: New host found: %s" % host
                        hosts.append(host)
                # pprint(res)

                if found_new_hosts == False:
                    break
            #
            except HTTPError, e:
                if e.code == 404:
                    break
                else:
                    raise e
        print "DEBUG: Done with -site, now just iterating"
        query = lastgood
        counter = 1
        while True:
            res = b.query(query, skip=MAX_REQS * counter)
            totalresults = int(res['WebTotal'])
            if totalresults == 0:
                break
            # pprint(res)
            if counter == 1:
                totalresults = int(res['WebTotal'])
                print "DEBUG: There are %i results" % totalresults
                reqs, rem = (divmod(totalresults, MAX_REQS))
                if rem > 0:
                    reqs += 1
                print "DEBUG: Making %i queries, hope that's all-right" % reqs
            for result in res['Web']:
                host = urlparse(result['Url']).hostname
                # print host
                if host not in hosts:
                    found_new_hosts = True
                    print "DEBUG: New host found: %s" % host
                    hosts.append(host)
            counter += 1
            if counter * MAX_REQS > totalresults:
                break
            # pprint(res)

        print "DEBUG: Found %i hosts associated with %s" % (len(hosts), start_host)
        print "\n".join(hosts)
if __name__ == "__main__":
    main()
