import os
from flask import Flask, request, render_template, url_for, jsonify, redirect
import sqlite3 as sql
from flask_sqlalchemy import SQLAlchemy
import json
import datetime
import schedule
import time
import requests

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'news.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Items(db.Model):
    s_n = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer)
    by = db.Column(db.String)
    type = db.Column(db.String)
    text = db.Column(db.String)
    times = db.Column(db.DateTime)
    url = db.Column(db.String)
    title = db.Column(db.String)

db.create_all()


def sync_data_at_intervals():
    url_1 = "https://hacker-news.firebaseio.com/v0/maxitem.json"
    payload_1 = "{}"
    response_1 = requests.request("GET", url_1, data=payload_1)
    maximum_id = eval(response_1.text)
    data_1 = [*range(maximum_id - 100, maximum_id), 1]
    for item_id in data_1:
        url_2 = "https://hacker-news.firebaseio.com/v0/item/" + str(item_id) + ".json?print=pretty"
        payload_2 = "{}"
        response_2 = requests.request("GET", url_2, data=payload_2)
        info = response_2.text
        data_2 = json.loads(info)

        id = data_2.get("id")
        exists = Items.query.filter(Items.id == id).count()
        if exists == 0:
            by = data_2.get("by")
            type = data_2.get("type")
            text = data_2.get("text")
            time_epoch = data_2.get("time")
            times = datetime.datetime.fromtimestamp(time_epoch)
            url = data_2.get("url")
            title = data_2.get("title")
            if title is None:
                title = data_2.get("type")
            item = Items(id=id, by=by, type=type, text=text, times=times,
                         url=url, title=title)
            db.session.add(item)
        else:
            continue
    db.session.commit()


@app.route('/api/latestnews', methods = ['GET', 'POST'])
def view_latest_news():
    sync_data_at_intervals()

    if request.method == 'GET':
        x = datetime.datetime.now()
        items = Items.query.filter(Items.times > datetime.datetime(x.year, x.month, x.day))
        return render_template('all_news.html', items=items)
    else:
        id = request.form.get('id')
        by = request.form.get('by')
        type = request.form.get('type')
        text = request.form.get('text')
        times = datetime.datetime.now()
        url = request.form.get('url')
        title = request.form.get('title')

        new_item = Items(id=id, by=by, type=type, text=text, times=times,
                 url=url, title=title)
    db.session.add(new_item)
    db.session.commit()
    return redirect(url_for('each_news', id=new_item.id))

    schedule.every(5).minutes.do(sync_data_at_intervals)
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/api/news/<id>', methods = ['GET', 'POST'])
def each_news(id):
    item = Items.query.filter(Items.id == id).first()
    return render_template('each_news.html', item=item)

@app.route('/api/latestnews/<type>', methods =['GET', 'POST'])
def filter_type(type):
    items = Items.query.filter(Items.type == type).all()
    return render_template('all_news.html', items=items)

@app.route('/api/latestnews/', methods =['GET', 'POST'])
def filter_text():
    text = request.form.get('text')
    items = Items.query.filter(Items.text == text).all()
    return render_template('all_news.html', items=items)


if __name__ == '__main__':
    app.run(debug=True)