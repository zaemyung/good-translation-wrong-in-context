#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Lena Voita

import numpy as np
import json
import argparse

parser = argparse.ArgumentParser(description='Evaluate accuracy on consistency test sets')
parser.add_argument('--repo-dir', type=str, required=True,
                    help='Path to your local "good-translation-wrong-in-context"')
parser.add_argument('--test', type=str,required=True,
                    choices=['deixis_test', 'deixis_dev', 'lex_cohesion_test', 'lex_cohesion_dev', 'ellipsis_vp', 'ellipsis_infl', 'deixis', 'lex_cohesion'],
                   help="""Test set name.""")
parser.add_argument('--scores', type=str, required=True,
                    help="Loss of your model on the test set examples, one score per line")
parser.add_argument('--maximize', action='store_true')


def get_scores(json_data, scores, is_maximize):
    group_lens = [len(elem['dst']) for elem in json_data]
    group_inds = [0] + list(np.cumsum(group_lens))
    true_inds = [elem['true_ind'] for elem in json_data]

    score_groups = [scores[group_inds[k]: group_inds[k + 1]] for k in range(len(group_inds) - 1)]
    if is_maximize:
        res = [1 if np.argmax(score_groups[k]) == true_inds[k] else 0 for k in range(len(score_groups))]
    else:
        res = [1 if np.argmin(score_groups[k]) == true_inds[k] else 0 for k in range(len(score_groups))]

    return res

def evaluate(repo_dir, testset_name, scores_fname, is_maximize):
    if testset_name == 'deixis':
        test_data = json.load(open("{}/consistency_testsets/{}.json".format(repo_dir, 'deixis_test')))
        dev_data = json.load(open("{}/consistency_testsets/{}.json".format(repo_dir, 'deixis_dev')))
        json_data = test_data + dev_data
    elif testset_name == 'lex_cohesion':
        test_data = json.load(open("{}/consistency_testsets/{}.json".format(repo_dir, 'lex_cohesion_test')))
        dev_data = json.load(open("{}/consistency_testsets/{}.json".format(repo_dir, 'lex_cohesion_dev')))
        json_data = test_data + dev_data
    else:
        json_data = json.load(open("{}/consistency_testsets/{}.json".format(repo_dir, testset_name)))
    scores = list(map(lambda x: float(x.strip()), open(scores_fname)))
    assert sum([len(elem['dst']) for elem in json_data]) == len(scores), "Number of lines in scores does not match number of test examples"

    group_scores = get_scores(json_data, scores, is_maximize)
    result = {'total': np.mean(group_scores)}

    if not testset_name in ['ellipsis_vp', 'ellipsis_infl']:
        scores_by_distance = {}
        for distance in range(1, 4):
            scores_by_distance[distance] = np.mean([el for i, el in enumerate(group_scores)\
                                                    if json_data[i]['ctx_dist'] == distance])
        result['by_distance'] = scores_by_distance
    return result

def print_results(testset_name, result):
    print("Test set: ", testset_name)
    print("Total accuracy: ", result['total'])
    if 'by_distance' in result:
        print('\nAccuracy for different distances between sentences requiring consistency.')
        for distance in range(1, 4):
            print("{}: {}".format(distance, result['by_distance'][distance]))


if __name__ == "__main__":
    args = parser.parse_args()
    result = evaluate(args.repo_dir, args.test, args.scores, args.maximize)
    print_results(args.test, result)


