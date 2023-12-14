from flask import Flask, render_template, redirect, url_for

from ..backend.database import WebDBHandler
from .. import DB_PATH

app = Flask(__name__)
db = WebDBHandler(DB_PATH)

@app.route('/')
def start_page():
    return redirect(url_for('search'))


@app.route('/search')
def search():
    pos = db.get_pos_tags()
    gloss = db.get_glosses()
    print(pos, gloss)
    return


@app.route('/results', methods=['GET'])
def results():
    lemma = ''
    pos = ''
    gloss = ''