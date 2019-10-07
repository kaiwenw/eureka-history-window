import os, json
from flask import render_template
from app import app

# HISTORY_FOLDER = '/Users/kevinwang/Desktop/test_histories/'
HISTORY_FOLDER = '/Users/kevinwang/Desktop/tiger_history/'

@app.route('/')
@app.route('/index')
def index():
    '''
    rows should have
    - timestamp
    - type
    - predicates

    should be sorted by timestamp
    '''
    rows = []
    for path in sorted(os.listdir(HISTORY_FOLDER)):
        parts = path.split(".")
        assert(len(parts) == 2)
        _timestamp = parts[0]
        _type = parts[1]
        _predicates = []
        with open(os.path.join(HISTORY_FOLDER, path), 'r') as f:
            data = json.load(f)
            for pred in data:
                _predicates.append({
                    'predicateName': pred['instanceName'],
                    })

        row = {
            'timestamp': _timestamp,
            'type': _type,
            'predicates': _predicates,
        }
        rows.append(row)
    return render_template('index.html', rows=rows)
