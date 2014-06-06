#! coding: utf-8

from flask import Flask, request, jsonify, abort
from api import get_subtitles, check_subtitles

app = Flask(__name__)


@app.route('/subs/<imdb_ids>')
def subs(imdb_ids):
    if '-' in imdb_ids:
        imdb_ids = imdb_ids.split('-')
    else:
        imdb_ids = [imdb_ids]
    data = get_subtitles(imdb_ids)
    if data:
        return jsonify(data)
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


@app.route('/favicon.ico')
def favicon():
    return ''


@app.route('/')
def home():
    return 'Hi there :)'


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    resp = {'success': False,
            'subtitles': 0}
    return jsonify(resp)


@app.errorhandler(500)
def page_not_found(e):
    """Return a custom 500 error."""
    resp = {'success': False,
            'subtitles': -1}
    return jsonify(resp)
