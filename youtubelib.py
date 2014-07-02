#!/usr/bin/python

# python 3 compatibility
from __future__ import print_function, division, unicode_literals, absolute_import

import os, sys, requests, time, json
from itertools import count
from functools import partial

from hammock import Hammock

class entry(object):
    '''Utility class for json data'''
    def __init__(self, entries):
        if entries.has_key('$t'):
            self.value = entries['$t']
        self.__dict__.update(entries)

    def __getitem__(self, item):
        return self.__dict__[item]
        
    def __str__(self):
        if hasattr(self, 'value'): return self.value
        return str(self.__dict__)

class yapi(object):
    
    def __init__(self):
        self.call = Hammock('https://gdata.youtube.com/')
        
    def get_comments(self, videoid):
        # load first page of comment data
        resp = self.call.feeds.api.videos(videoid).comments.GET(params={'orderby':'published','alt':'json'})
        self.comments = []
        
        # loop indefinitely until no next page is signalled
        for i in count():
            data = json.loads(resp.text, object_hook=entry)
            self.comments.extend(data.feed.entry)
            next_link = [x for x in data.feed.link if x.rel == 'next']
            if not next_link: break
            next_link = next_link.pop().href
            print('Processed page {0}, loading link {1}'.format(i,next_link))
            # be nice to youtube
            time.sleep(2)
            resp = requests.get(next_link)
            
    def print_comments(self, output=sys.stdout):
        # make quick function to print to given output
        p = partial(print, file=output)
        
        p('Number of comments: {0}'.format(len(self.comments)))
        p();p()

        for comment in self.comments:
            p()
            p('=' * 60)
            p((u'author: ' + comment.author[0].name.value).encode('us-ascii', 'ignore'))
            p((u'Date: ' + comment.updated.value).encode('us-ascii', 'ignore'))
            p()
            p(comment.content.value.encode('us-ascii', 'ignore'))

def main():
    pass

if __name__ == '__main__': main()
    