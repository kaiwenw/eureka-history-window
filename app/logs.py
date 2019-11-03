import pandas, pprint
import os, json
from collections import OrderedDict

# given folder with files of form int.*, return a numerically
# sorted version of listdir.
def get_sorted_num_files(folder):
    filtered_folder = filter(lambda p: p.split(".")[0].isdigit(), os.listdir(folder))
    return sorted(filtered_folder, key=lambda item: int(item.split(".")[0]))

# really is stats + metadata
def stats_time_series(root_dir):
    stats = []
    for sess_num in get_sorted_num_files(root_dir):
        stat_dir = os.path.join(root_dir, sess_num, 'stats')
        meta_dir = os.path.join(root_dir, sess_num, 'metadata')
        for num in get_sorted_num_files(stat_dir):
            stat_p = os.path.join(stat_dir, num)
            meta_p = os.path.join(meta_dir, num)
            stat = OrderedDict()
            with open(stat_p, 'r') as f:
                stat.update(json.load(f))
            with open(meta_p, 'r') as f:
                stat.update(json.load(f))
            stats.append(stat)
        zero_stat = stats[-1].copy()
        for k in zero_stat:
            if (k == 'arrival_time'):
                continue
            zero_stat[k] = 0;
        stats.append(zero_stat)
    return stats


# this processes all the information in a session
def process_logs(sess_dir):
    result = OrderedDict()
    info_file = os.path.join(sess_dir, 'info.json')
    # unpack info
    with open(info_file, 'r') as f:
        result.update(json.load(f))

    # unpack img metadata
    img_data = OrderedDict()
    meta_dir = os.path.join(sess_dir, 'metadata')
    for p in os.listdir(meta_dir):
        num = int(p.split('.')[0])
        with open(os.path.join(meta_dir, p), 'r') as f:
            img_data[num] = json.load(f)
    result['img_data'] = img_data

    # unpack feedbacks (map of id to feedback struct)
    feedbacks = OrderedDict()
    feedback_file = os.path.join(sess_dir, 'feedback.csv')
    for index, row in pandas.read_csv(feedback_file).iterrows():
        if (row['feedback_label'] == 'Ignore'):
            feedbacks.pop(row['id'])
        else:
            start_time = int(result['start_time(ms)'])
            feedback_time = int(row['absolute time(ms)'])
            feedbacks[row['id']] = {
                'elapsed_ms': feedback_time-start_time,
                'label': row['feedback_label'],
            }
    result['feedbacks'] = feedbacks

    print(result)

    return result

