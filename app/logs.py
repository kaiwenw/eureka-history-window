import pandas, pprint
import os, json, time
from collections import OrderedDict

# given folder with files of form int.*, return a numerically
# sorted version of listdir.
def get_sorted_num_files(folder):
    if not os.path.isdir(folder):
        return []
    filtered_folder = filter(lambda p: p.split(".")[0].isdigit(), os.listdir(folder))
    mapped_folder = map(lambda x: int(x.split(".")[0]), filtered_folder)
    return sorted(mapped_folder)


def get_sorted_subfolders(folder):
    assert os.path.isdir(folder)
    filtered_folder = filter(lambda p: p.isdigit(), os.listdir(folder))
    mapped_folder = map(lambda x: int(x), filtered_folder)
    return sorted(mapped_folder)


# very preliminary search for some potentially viable paths
def get_all_files(root_folder, search_from_path, depth=2):
    assert depth >= 0
    if not os.path.isdir(search_from_path):
        return []
    res = []
    for file in os.listdir(search_from_path):
        new_path = os.path.join(search_from_path, file)
        if not os.path.isdir(new_path):
            continue
        # it is a candidate if it has a direct subfolder of 0, 1, 2...
        sorted_subfolders = get_sorted_subfolders(new_path)
        if len(sorted_subfolders) > 0:
            good = True
            for i in range(len(sorted_subfolders)):
                if not (i in sorted_subfolders):
                    good = False
                    print(i, "not in", sorted_subfolders)
                    break
            if good:
                assert new_path[: len(root_folder)] == root_folder
                rest = new_path[len(root_folder) :]
                print(sorted_subfolders, "good", new_path, rest)
                res.append(rest)

        if depth >= 1:
            res.extend(get_all_files(root_folder, new_path, depth - 1))
    return res


"""
Return a mapping of absolute time (ms) to an OrderedDict of
- id
- label
while verifying that the times are indeed sequential
"""


def load_feedbacks_csv(csv_path):
    result = OrderedDict()
    if os.path.isfile(csv_path):
        last_time = None
        for idx, row in pandas.read_csv(csv_path).iterrows():
            entry = OrderedDict()
            entry["id"] = row["id"]
            entry["label"] = row["feedback_label"]
            cur_time = int(row["absolute time(ms)"])
            result[cur_time] = entry
            if last_time is None:
                last_time = cur_time
            else:
                assert last_time < cur_time
                last_time = cur_time
    return result


def float_div(num, denom):
    if int(denom) == 0:
        return 0.0
    return float(num) / float(denom)


"""
Get all the metadata given the root_dir.
Expects the following directory tree with S sessions
root_dir
    |
    |----0
    |----1
    .
    .
    |----i/
    |    |
    |    |----pred.hyperfindsearch
    |    |----start_info.json
    |    |----end_info.json
    |    |----feedback.csv
    |    |----metadata/
    |    |       |
    |    |       |----0.json, 1.json,...
    |    |----stats/
    |    |       |----0.json, 1.json,...
    |    |----thumbnail/
    |    |       |----0.jpeg, 1.jpeg,...
    .
    .
    |----S-1/

The result will be an array A where A[i] is an OrderedDict for the ith session.
A[i] will contain:
- 'predicates' is a list of dictionaries representing the predicates
- 'predicate_path' is the path to the predicate
- 'start_info' is path to the info logged at start of session
- 'end_info' is path to info logged at end of session
- 'derived_info' is an OrderedDict representing derived information from info
    - involving start_time and end_time formatted
- 'feedback' an OrderedDict representing feedbacks.csv
- 'per_img' an array B where B[j] is an OrderedDict for the jth image.
    B[j] will contain:
    - 'metadata' field contains an OrderedDict of metadata jsons
    - 'stats' field contains an OrderedDict of stat jsons
    - 'img_path' field contains the path to this image
    - 'derived_stats' field contains an OrderedDict of derived statistics. This
    is for plotting as well as the table. Some are just renamings of 'stats' to
    be consistent.
        - 'items_processed' = 'Searched'
        - 'items_shown' = 'Passed'
        - 'new_hits' field contains number of positive feedbacks so far
        - 'pass_rate' = 'items_shown' / 'items_processed' * 100%
        - 'precision' = 'new_hits' / 'items_shown' * 100%
        - 'elapsed_time(s)' field contains elapsed time sense beginning of start time
        - 'productivity' = 'new_hits' / 'elapsed_time(s)' * 60
There is one more entry for the end, where it only has the derived_stats field.

The implementation will try to be as faithful to the order as possible.
On error, will return None
"""


def process_data(root_dir):
    print("Processing data from %s" % root_dir)
    try:
        rows = []
        for sess_num in get_sorted_subfolders(root_dir):
            sess_dir = os.path.join(root_dir, str(sess_num))

            row = OrderedDict()
            # predicate path
            pred_path = os.path.join(sess_dir, "pred.hyperfindsearch")
            row["predicate_path"] = pred_path
            with open(pred_path, "r") as f:
                row["predicates"] = json.load(f)

            # read the info.json file
            start_info_path = os.path.join(sess_dir, "start_info.json")
            with open(start_info_path, "r") as f:
                row["start_info"] = OrderedDict(json.load(f))

            sess_start_time = int(row["start_info"]["start_time(ms)"])

            row["derived_info"] = OrderedDict()
            row["derived_info"]["start_time"] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(sess_start_time / 1000)
            )

            # temporary feedback mapping of time -> label + id
            feedback_path = os.path.join(sess_dir, "feedback.csv")
            time2feedback = load_feedbacks_csv(feedback_path)
            cur_feedback_idx = 0

            # set of positive and negative at a given time
            pos_feedback_set = set()
            neg_feedback_set = set()
            # helper function for calculating derived stats
            def calc_derived_stats(stats, cur_img_time):
                nonlocal cur_feedback_idx, time2feedback
                nonlocal pos_feedback_set, neg_feedback_set
                feedback_keys = list(time2feedback.keys())
                # first, move the feedback statistics forward to the current time
                while (
                    cur_feedback_idx < len(feedback_keys)
                    and feedback_keys[cur_feedback_idx] <= cur_img_time
                ):
                    cur_feedback = time2feedback[feedback_keys[cur_feedback_idx]]
                    if cur_feedback["label"] == "Positive":
                        pos_feedback_set = pos_feedback_set | {cur_feedback["id"]}
                        neg_feedback_set = neg_feedback_set - {cur_feedback["id"]}
                    elif cur_feedback["label"] == "Negative":
                        pos_feedback_set = pos_feedback_set - {cur_feedback["id"]}
                        neg_feedback_set = neg_feedback_set | {cur_feedback["id"]}
                    else:
                        assert cur_feedback["label"] == "Ignore"
                        pos_feedback_set = pos_feedback_set - {cur_feedback["id"]}
                        neg_feedback_set = neg_feedback_set - {cur_feedback["id"]}
                    cur_feedback_idx += 1

                # second calculate the derived stats
                derived = OrderedDict()
                derived["items_processed"] = int(stats["Searched"])
                derived["items_shown"] = int(stats["Passed"])
                derived["new_hits"] = len(pos_feedback_set)
                derived["pass_rate(%)"] = (
                    float_div(derived["items_shown"], derived["items_processed"])
                    * 100.0
                )
                derived["precision(%)"] = (
                    float_div(derived["new_hits"], derived["items_shown"]) * 100.0
                )
                derived["elapsed_time(min)"] = (
                    float(cur_img_time - sess_start_time) / 1000.0 / 60.0
                )
                derived["productivity"] = float_div(
                    derived["new_hits"], derived["elapsed_time(min)"]
                )
                return derived

            meta_dir = os.path.join(sess_dir, "metadata")
            stat_dir = os.path.join(sess_dir, "stats")
            img_dir = os.path.join(sess_dir, "thumbnail")

            per_img = []
            for img_num in get_sorted_num_files(stat_dir):
                cur_img = OrderedDict()

                # first load in metadata, stats and img path
                meta_path = os.path.join(meta_dir, "%d.json" % img_num)
                with open(meta_path, "r") as f:
                    cur_img["metadata"] = OrderedDict(json.load(f))

                stat_path = os.path.join(stat_dir, "%d.json" % img_num)
                with open(stat_path, "r") as f:
                    cur_img["stats"] = OrderedDict(json.load(f))

                # relative image page
                cur_img["img_path"] = "%d/thumbnail/%d.jpeg" % (sess_num, img_num)

                cur_img["derived_stats"] = calc_derived_stats(
                    cur_img["stats"], int(cur_img["metadata"]["arrival_time(ms)"])
                )
                per_img.append(cur_img)

            end_info_path = os.path.join(sess_dir, "end_info.json")
            assert cur_feedback_idx <= len(time2feedback)
            if os.path.isfile(end_info_path):
                with open(end_info_path, "r") as f:
                    row["end_info"] = OrderedDict(json.load(f))
                sess_end_time = int(row["end_info"]["end_time(ms)"])
                row["derived_info"]["end_time"] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(sess_end_time / 1000)
                )

                # there may be feedbacks in this session despite having seen the last image
                # the last data point is using info from info.json
                last_elem = OrderedDict()
                last_elem["metadata"] = OrderedDict()
                # emulate the last arrival
                last_elem["metadata"]["arrival_time(ms)"] = sess_end_time
                last_elem["derived_stats"] = calc_derived_stats(
                    row["end_info"], sess_end_time
                )
                per_img.append(last_elem)

                assert cur_feedback_idx == len(time2feedback)
            row["positive_ids"] = pos_feedback_set
            row["negative_ids"] = neg_feedback_set
            row["per_img"] = per_img
            rows.append(row)
        return rows

    except OSError as e:
        print(e)
        return None
    except KeyError as e:
        print("Key not found: ", e)
        return None
    except json.decoder.JSONDecodeError as e:
        print("Json failed to decode", e)
        return None
