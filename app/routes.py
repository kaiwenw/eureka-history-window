import os, json
from collections import OrderedDict
from flask import redirect, request, render_template, send_from_directory, jsonify
from app import app
from app.logs import *

app.config['LOG_FOLDER'] = None
app.config['CURRENT_SESSION_NAME'] = None
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

'''
For loading the replay page
'''
@app.route('/replay/<int:sess_num>')
def replay(sess_num):
    if (app.config["LOG_FOLDER"] is None):
        print("No log folder, defaulting to index");
        return index()

    rows = process_data(app.config["LOG_FOLDER"])
    # ignore last one since that's only metadata
    per_img = rows[sess_num]['per_img'][:-1]
    pos_ids = rows[sess_num]['positive_ids']
    neg_ids = rows[sess_num]['negative_ids']
    # print(pos_ids);
    return render_template('replay.html', per_img=per_img, pos_ids=pos_ids, neg_ids=neg_ids)

'''
For serving images!
'''
@app.route('/replay_img/<path:filename>')
def replay_img(filename):
    return send_from_directory(app.config['LOG_FOLDER'], filename)


@app.route('/download/<int:sess_num>')
def download(sess_num):
    path = "%d/pred.hyperfindsearch" % sess_num
    return send_from_directory(app.config["LOG_FOLDER"], path)


def get_stat_series(rows):
    stat_series = []
    # at the end of each row, add a zero point
    for row in rows:
        if (len(row['per_img']) > 0):
            stat_series.extend(row['per_img'])
            zero_entry = OrderedDict()
            zero_entry['metadata'] = OrderedDict()
            zero_entry['metadata']['arrival_time(ms)'] = row['per_img'][-1]['metadata']['arrival_time(ms)']
            zero_entry['derived_stats'] = OrderedDict()
            for k in row['per_img'][-1]['derived_stats']:
                zero_entry['derived_stats'][k] = 0;
            stat_series.append(zero_entry)
    return stat_series

@app.route('/refresh_plot')
def refresh_plot():
    stat_series = {}
    if (app.config["LOG_FOLDER"] and os.path.isdir(app.config["LOG_FOLDER"])):
        rows = process_data(app.config["LOG_FOLDER"])
        if (rows is None):
            print(app.config["LOG_FOLDER"], "resulted in none rows")
            return jsonify({})
        stat_series = get_stat_series(rows)
        print("Refreshing plots with " + str(len(stat_series)))
    return jsonify(stat_series)


# just update
@app.route('/update_log_folder/<path:session_name>')
def update_log_folder(session_name):
    print("Updated with ", session_name)
    app.config["CURRENT_SESSION_NAME"] = session_name
    app.config["LOG_FOLDER"] = os.path.join(app.config['ROOT_FOLDER'], session_name)
    return index()

def reset_states():
    app.config['LOG_FOLDER'] = None
    app.config['CURRENT_SESSION_NAME'] = None

def invalid_session():
    return app.config['LOG_FOLDER'] is None or app.config['CURRENT_SESSION_NAME'] is None

@app.route('/')
def index():
    candidates = get_all_files(app.config["ROOT_FOLDER"], app.config["ROOT_FOLDER"])
    if len(candidates) == 0:
        return render_template('index.html')

    print("candidates: ", candidates)
    if invalid_session() or app.config['CURRENT_SESSION_NAME'] not in candidates:
        update_log_folder(candidates[0])

    rows = None
    stat_keys = None
    if (app.config["LOG_FOLDER"] and os.path.isdir(app.config["LOG_FOLDER"])):
        rows = process_data(app.config["LOG_FOLDER"])

    if rows is not None and len(rows) > 0 and len(rows[0]['per_img']) > 0:
        stat_keys = rows[0]['per_img'][0]['derived_stats'].keys()

    return render_template('index.html', session_name=app.config["CURRENT_SESSION_NAME"], rows=rows, candidate_logs=candidates, stat_keys=stat_keys)
