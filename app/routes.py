import os, json, time
from flask import render_template, send_from_directory
from app import app
from app.logs import process_predicate_names, process_logs


# HISTORY_FOLDER = '/Users/kevinwang/Desktop/test_histories/'
# HISTORY_FOLDER = '/Users/kevinwang/Desktop/tiger_history/'
# HISTORY_FOLDER = '/Users/kevinwang/Desktop/new_histories/'

HISTORY_FOLDER = 'app/static/'

@app.route('/replay/<int:sess_num>')
def replay(sess_num):
    sess_dir = os.path.join(HISTORY_FOLDER, str(sess_num))
    logs = process_logs(sess_dir)
    print(logs.keys())
    return render_template('replay.html', imgs=logs['img_data'], sess_num=sess_num)


@app.route('/download/<int:sess_num>/<string:sess_type>')
def download(sess_num, sess_type):
    path = "%d/%s.hyperfindsearch" % (sess_num, sess_type)
    return send_from_directory(HISTORY_FOLDER, path)

@app.route('/')
def index():
    rows = []
    for sess_num in os.listdir(HISTORY_FOLDER):
        sess_dir = os.path.join(HISTORY_FOLDER, sess_num)
        # junk files that aren't session directories
        if not sess_num.isdigit(): 
            print("Ignoring %s" % sess_dir)
            continue

        row = dict()
        row['sess_num'] = int(sess_num)

        logs = process_logs(sess_dir)
        secs_since_epoch = logs['start_time(ms)'] / 1000
        row['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(secs_since_epoch))

        row['type'] = logs['type']

        predicate_path = os.path.join(sess_dir, '%s.hyperfindsearch' % row['type'])
        row['predicates'] = process_predicate_names(predicate_path)

        rows.append(row)

    return render_template('index.html', rows=rows)
