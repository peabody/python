#!/usr/bin/python
'''
A personal library I use to encapsulate YouTube's data API.

I don't much care for google's provided client library, hence this class which
I hope is straight and to the point.

I add to it as I need functionality.
'''

# python 3 compatibility
from __future__ import print_function, division, unicode_literals, absolute_import

import os, sys, requests, time, json
from itertools import count
from functools import partial
from hammock import Hammock

class entry(object):
    '''Utility class for json data.  If you pass this to json.loads as an
       object_hook it results in a convenient object for accessing the return data.

       YT API v2 JSON data has some quirks I've attempted to work around.  v2 JSON is
       converted from xml and as such has weird conventions.  Data which represents the
       text of an xml tag is accessible via a $t property, but since $ isn't a valid
       character for a python identifier, I take these properties and add them
       as a 'value' attribute as well.'''
    def __init__(self, entries):
        if entries.has_key('$t'):
            self.value = entries['$t']
        self.__dict__.update(entries)

    def __getitem__(self, item):
        return self.__dict__[item]
        
    def __str__(self):
        if hasattr(self, 'value'): return self.value
        return str(self.__dict__)

class Yapi(object):
    '''
    This is a class wrapper object whose methods encapsulate youtube's data API.
    '''
    
    def __init__(self):
        self.call = Hammock('https://gdata.youtube.com/')
        
    def get_comments(self, videoid):
        '''
        After this method is called, converted comment JSON data will be
        accessible via self.comments for the given videoid
        '''

        # load first page of comment data
        # The comments method is only accessible via the v2 api
        resp = self.call.feeds.api.videos(videoid)\
                   .comments.GET(params={'orderby':'published','alt':'json'})
        self.comments = []
        
        # loop indefinitely until no next page is signalled
        # TODO: see about updating the call to return more results per page
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
        '''
        This is a convenience method which renders to ascii the comment information I'm
        most interested in, namely, number of comments, the comment authors and
        comment content.  Must be called after get_comments.
        '''
        # make quick function to print to given output
        p = partial(print, file=output)

        # encoder utility
        e = lambda x: x.encode('us-ascii', 'ignore')
        
        p('Number of comments: {0}'.format(len(self.comments)))
        p();p()

        for comment in self.comments:
            p()
            p('=' * 60)
            p(e('author: ' + comment.author[0].name.value)))
            p(e('Date: ' + comment.updated.value)))
            p()
            p(e(comment.content.value))

def main():
    pass

if __name__ == '__main__': main()
    
