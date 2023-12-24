from flask import Flask, render_template, redirect, url_for, request

from ..backend.database import WebDBHandler
from ..backend.search import WordSearch
from .. import DB_PATH

app = Flask(__name__)
db = WebDBHandler(DB_PATH)
search = WordSearch(db)


@app.route('/')
def start_page():
    return render_template('index.html')


@app.route('/read', methods=['GET', "POST"])
def read_page():
    if request.method == ['GET']:
        query = request.args
        print(query)
        return render_template('read.html')
    else:
        return render_template('read.html')


@app.route('/search', methods=['GET', "POST"])
def search_page():
    return render_template('search.html', res=())


@app.route('/results', methods=['GET'])
def results():
    if request.method == 'GET':
        query = request.args
        res = search.search(request.args)
        print(res)
        return render_template('search.html', res=res, q=query)