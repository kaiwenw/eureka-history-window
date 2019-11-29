import os, json
from collections import OrderedDict
from flask import redirect, request, render_template, send_from_directory, jsonify
from app import app
from app.logs import *


@app.route('/', methods=['GET', 'POST'])
def new_folder():
    print(request)
    if request.method == 'POST':
        print("post", request.url);
        print(dir(request))
        print(request.form)
        print(request.form['new_root_path'])
        # return redirect(request.url)
    return index()

'''
For loading the replay page
'''
@app.route('/replay/<int:sess_num>')
def replay(sess_num):
    rows = process_data(app.config["LOG_FOLDER"])
    # ignore last one since that's only metadata
    per_img = rows[sess_num]['per_img'][:-1]
    return render_template('replay.html', per_img=per_img)

'''
For serving images!
'''
@app.route('/replay_img/<path:filename>')
def replay_img(filename):
    return send_from_directory(app.config['LOG_FOLDER'], filename)


@app.route('/download/<int:sess_num>')
def download(sess_num):
    path = "%d/%d.hyperfindsearch" % (sess_num, sess_num)
    return send_from_directory(app.config["LOG_FOLDER"], path)


def get_stat_series(rows):
    stat_series = []
    # at the end of each row, add a zero point
    for row in rows:
        stat_series.extend(row['per_img'])
        zero_entry = OrderedDict()
        zero_entry['metadata'] = OrderedDict()
        zero_entry['metadata']['arrival_time'] = row['per_img'][-1]['metadata']['arrival_time']
        zero_entry['derived_stats'] = OrderedDict()
        for k in row['per_img'][-1]['derived_stats']:
            zero_entry['derived_stats'][k] = 0;
        stat_series.append(zero_entry)
    return stat_series

@app.route('/refresh_plot')
def refresh_plot():
    rows = process_data(app.config["LOG_FOLDER"])
    stat_series = get_stat_series(rows)
    print("Refreshing plots with " + str(len(stat_series)))
    return jsonify(stat_series)

@app.route('/')
def index():
    rows = process_data(app.config["LOG_FOLDER"])
    return render_template('index.html', rows=rows) # , stat_series=stat_series)
