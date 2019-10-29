import pandas, pprint
import os, json

def process_predicate_names(path):
    predicates = []
    with open(path, 'r') as f:
        for pred in json.load(f):
            predicates.append(pred['instanceName'])
    return predicates

# this processes all the information in a session
def process_logs(sess_dir):
    result = dict()
    info_file = os.path.join(sess_dir, 'info.txt')
    # unpack info
    with open(info_file, 'r') as f:
        # start time
        row = f.readline().split(":")
        assert(len(row) == 2)
        result['start_time(ms)'] = int(row[1][1:])

        # type
        row = f.readline().split(":")
        assert(len(row) == 2)
        result['type'] = row[1].strip()

    # unpack img metadata
    result['img_data'] = dict()
    meta_dir = os.path.join(sess_dir, 'metadata')
    for p in os.listdir(meta_dir):
        num = int(p.split('.')[0])
        with open(os.path.join(meta_dir, p), 'r') as f:
            result['img_data'][num] = json.load(f)

    # maps id to a struct containing metadata about feedback
    feedbacks = dict()
    feedback_file = os.path.join(sess_dir, 'feedback.csv')
    for index, row in pandas.read_csv(feedback_file).iterrows():
        if (row['feedback_label'] == 'Ignore'):
            feedbacks.pop(row['id'])
        else:
            feedbacks[row['id']] = {
                'elapsed_ms': row['absolute time(ms)']-result['start_time(ms)'],
                'label': row['feedback_label'],
            }
    result['feedbacks'] = feedbacks
    return result

