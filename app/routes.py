import os, json, time
from collections import OrderedDict
from flask import render_template, send_from_directory
from app import app
from app.logs import *

HISTORY_FOLDER = 'app/static/'

@app.route('/replay/<int:sess_num>')
def replay(sess_num):
    sess_dir = os.path.join(app.static_folder, str(sess_num))
    logs = process_logs(sess_dir)
    print(logs['img_data'][0].keys())
    print(logs['img_data'][0]['Display-Name'])
    print(logs['img_data'][0]['_ObjectID'])
    print(logs['img_data'][0])
    print(logs['feedbacks'])
    return render_template('replay.html', 
                    imgs=logs['img_data'], 
                    sess_num=sess_num,
                    feedbacks=logs['feedbacks'])


@app.route('/download/<int:sess_num>')
def download(sess_num):
    path = "%d/%d.hyperfindsearch" % (sess_num, sess_num)
    return send_from_directory(app.static_folder, path)

@app.route('/')
def index():
    rows = OrderedDict()
    # process a single session
    for sess_num in get_sorted_num_files(app.static_folder):
        sess_dir = os.path.join(app.static_folder, sess_num)

        row = OrderedDict()
        logs = process_logs(sess_dir)

        # parse the times
        start_ms_since_epoch = int(logs['start_time(ms)'])
        end_ms_since_epoch = int(logs['end_time(ms)'])
        secs_since_epoch = int(logs['start_time(ms)']) / 1000
        row['start_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_ms_since_epoch/1000))
        row['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_ms_since_epoch/1000))


        row['type'] = logs['type']
        predicate_path = os.path.join(sess_dir, '%s.hyperfindsearch' % sess_num)
        with open(predicate_path, 'r') as f:
            row['predicates'] = json.load(f)

        # determine number of true positives (not through cocktail)
        num_true_positives = 0
        for img_id, feedback in logs['feedbacks'].items():
            print(feedback)
            if (feedback['label'] == 'Positive'):
                num_true_positives += 1

        # make all the stats for table
        stats = OrderedDict()
        stats['Items Processed'] = int(logs['Searched'])
        stats['Items Shown'] = int(logs['Passed'])
        stats['New Hits'] = num_true_positives
        stats['Pass Rate (%)'] = float(stats['Items Shown']) / stats['Items Processed'] * 100
        stats['Precision (%)'] = float(stats['New Hits']) / stats['Items Shown']
        elapsed_sec = float(end_ms_since_epoch - start_ms_since_epoch) / 1000.
        stats['Elapsed Time'] = elapsed_sec / 60.
        stats['Productivity'] = float(stats['New Hits']) / stats['Elapsed Time']
        # round the floating point stats
        for stat in stats:
            if isinstance(stats[stat], float):
                stats[stat] = round(stats[stat], 3)
        row['stats'] = stats

        # add to rows
        rows[sess_num] = row

    stat_series = stats_time_series(app.static_folder)
    return render_template('index.html', rows=rows, stat_series=stat_series)
