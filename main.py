#! coding: utf-8

from flask import Flask, request, jsonify, abort, redirect
from api import get_subtitles, check_subtitles, get_download_url

app = Flask(__name__)


@app.route('/subtitles/<imdb_ids>')
def subtitles(imdb_ids):
    if '-' in imdb_ids:
        imdb_ids = imdb_ids.split('-')
    else:
        imdb_ids = [imdb_ids]
    data = get_subtitles(imdb_ids)
    if data:
        return jsonify(data)
    else:
        resp = {'success': False,
                'subs': [],
                'subtitles': 0}
        return jsonify(resp)


@app.route('/subtitle/<subtitle_id>.zip')
def subtitle(subtitle_id):
    download_url = get_download_url(subtitle_id)
    if download_url:
        return redirect(download_url)
    else:
        abort(404)


@app.route('/check_subtitles', methods=['POST'])
def check_subs():
    imdb_id = request.form.get('imdb_id')
    ok = check_subtitles(imdb_id)
    if ok:
        return 'OK'
    else:
        abort(404)
