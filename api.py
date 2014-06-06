#! coding: utf-8

import re
import simplejson
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue


def _get_movie_title(imdb_id):
    r = urlfetch.fetch('http://www.omdbapi.com/?i=' + imdb_id)
    if r.status_code == 200:
        return simplejson.loads(r.content).get('Title')


def _get_subtitles(imdb_id):
    return memcache.get(imdb_id)


def check_subtitles(imdb_id):
    lock_key = 'in_progress:%s' % imdb_id
    if memcache.get(key=lock_key):
        return None

    memcache.add(key=lock_key, value=True, time=500)

    movie_title = _get_movie_title(imdb_id)
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

            download_url = re.findall(
                '"(/subtitle/download\?.*?)"', html)[0]
            if download_url.startswith('/'):
                download_url = 'http://subscene.com' + download_url

            subtitle_id = re.findall('/subtitles/.*?(\d+)/ratings',
                                     html, re.MULTILINE)[0]

            info = {'id': int(subtitle_id),
                    'rating': rating,
                    'url': download_url}

            subtitle_lang = re.findall(' (\w+) subtitle</title>',
                                       html, re.MULTILINE)
            if subtitle_lang:
                subtitle_lang = subtitle_lang[0].lower()
                if subtitle_lang in subs:
                    subs[subtitle_lang].append(info)
                else:
                    subs[subtitle_lang] = [info]

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

    memcache.add(key=imdb_id, value=subs, time=86400)
    memcache.delete(key=lock_key)
    return True


def get_subtitles(imdb_ids):
    resp = {'subs': {},
            'subtitles': 0}

    for imdb_id in imdb_ids:
        subs = _get_subtitles(imdb_id)
        resp['subs'][imdb_id] = subs if subs else {}
        if subs:
            resp['subtitles'] += sum([len(subs[lang]) for lang in subs.keys()])
        else:
            taskqueue.add(url='/check_subtitles',
                          params={'imdb_id': imdb_id})

    resp['success'] = True
    return resp
