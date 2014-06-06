#! coding: utf-8

import re
import simplejson
from time import time
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue


class Database(db.Model):
    val = db.TextProperty()

    @classmethod
    def get(cls, key):
        resp = cls.get_by_key_name(key)
        if resp:
            return simplejson.loads(resp.val)

    @classmethod
    def set(cls, key, val):
        entity = cls(key_name=key, val=simplejson.dumps(val))
        entity.put()
        return val


database = Database()


def get_movie_title(imdb_id):
    r = urlfetch.fetch('http://www.omdbapi.com/?i=' + imdb_id)
    if r.status_code == 200:
        return simplejson.loads(r.content).get('Title')


def extract_download_url(html):
    download_url = re.findall('"(/subtitle/download\?.*?)"',
                              html.replace('\n', ''))[0]
    if download_url.startswith('/'):
        download_url = 'http://subscene.com' + download_url
    return download_url


def get_download_url(subtitle_id):
    key = 'subtitle:%s' % subtitle_id
    subtitle = database.get(key)
    if not subtitle:
        return False

    download_url = memcache.get('download:%s' % subtitle_id)
    if not download_url:
        r = urlfetch.fetch(subtitle.get('subtitle_url'))
        download_url = extract_download_url(r.content.replace('\n', ''))
        memcache.add('download:%s' % subtitle_id, download_url, time=1800)
    return download_url


def check_subtitles(imdb_id):
    movie_title = get_movie_title(imdb_id)
    if not movie_title:
        return False

    movie_hash = re.sub('[^a-zA-Z0-9]+', '-', movie_title.lower())
    r = urlfetch.fetch('http://subscene.com/subtitles/' + movie_hash)

    subs = {}
    sub_urls = re.findall(' href=\"(/subtitles/.*?)\"',
                          r.content, re.MULTILINE)

    def parse_subtitle_info(rpc):
        try:
            r = rpc.get_result()
        except urlfetch.DownloadError:
            return False

        if r.status_code == 200:
            html = r.content.replace('\n', '')

            rating = re.findall(
                '<div .*?rating .*?span>(.*?)</span>', html)
            if rating and rating[0].isdigit():
                rating = int(rating[0])
            else:
                rating = -1

            rating_count = re.findall(
                '<div.*?rating .*? data-hint=".*? (\d+) .*?"', html)
            if rating_count and rating_count[0].isdigit():
                rating_count = int(rating_count[0])
                rating *= rating_count
            else:
                rating = -1

            subtitle_id = re.findall('/subtitles/.*?(\d+)/ratings', html)[0]
            subtitle_url = re.findall('\?ReturnUrl=(.*?)"', html)[0]

            info = {'id': int(subtitle_id),
                    'rating': rating,
                    'subtitle_url': subtitle_url}
            database.set('subtitle:%s' % subtitle_id, info)
            memcache.add('download:%s' % subtitle_id,
                         extract_download_url(html), 1800)

            subtitle_lang = re.findall(' (\w+) subtitle</title>',
                                       html, re.MULTILINE)
            if subtitle_lang:
                subtitle_lang = subtitle_lang[0].lower()
                if subtitle_lang in subs:
                    subs[subtitle_lang].append(info)
                else:
                    subs[subtitle_lang] = [info]
            return True
        return False

    # Use a helper function to define the scope of the callback.
    def create_callback(rpc):
        return lambda: parse_subtitle_info(rpc)

    rpcs = []
    for url in set(sub_urls):
        if url.startswith('/'):
            url = 'http://subscene.com' + url
        print url
        rpc = urlfetch.create_rpc(deadline=60)
        rpc.callback = create_callback(rpc)
        urlfetch.make_fetch_call(rpc, url)
        rpcs.append(rpc)

    # Finish all RPCs, and let callbacks process the results.
    for rpc in rpcs:
        rpc.wait()

    database.set('movie:%s' % imdb_id, subs)
    database.set('last_updated:%s' % imdb_id, time())
    memcache.delete(key='in_progress:%s' % imdb_id)     # remove lock
    return True


def get_subtitles(imdb_ids):
    resp = {'subs': {},
            'subtitles': 0}

    for imdb_id in imdb_ids:
        subs = database.get('movie:%s' % imdb_id)
        if subs:
            data = {}
            for lang in subs.keys():
                subs[lang].sort(key=lambda k: k['rating'])
                data[lang] = [subs[lang][-1]]
                data[lang][0]['download_url'] = '/subtitle/%s.zip' \
                                                % subs[lang][-1]['id']
            resp['subs'][imdb_id] = data
        else:
            resp['subs'][imdb_id] = {}

        last_updated = None
        if subs:
            resp['subtitles'] += sum([len(subs[lang]) for lang in subs.keys()])
            last_updated = database.get('last_updated:%s' % imdb_id)

        if not last_updated or time() - last_updated > 86400:
            lock_key = 'in_progress:%s' % imdb_id
            if not memcache.get(key=lock_key):
                taskqueue.add(url='/check_subtitles',
                              params={'imdb_id': imdb_id})
                memcache.add(key=lock_key, value=True, time=500)

    resp['success'] = True
    return resp
