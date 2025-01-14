# SETUP
import matplotlib.pyplot as plt
from sklearn.metrics import PrecisionRecallDisplay
import numpy as np
import json
import requests
import pandas as pd
from sys import argv


def relevant_results(results, relevant, idx):
    return [doc for doc in results[:idx] if doc['id'] in relevant]


# METRICS TABLE
# Define custom decorator to automatically calculate metric based on key
metrics = {}
def metric(f): return metrics.setdefault(f.__name__, f)


@metric
def ap(results, relevant):
    """Average Precision"""
    precision_values = [
        len(relevant_results(results, relevant, (idx+1))) / (idx+1)
        for idx in range(len(results)) if results[idx]['id'] in relevant
    ]
    try:
        return sum(precision_values)/len(precision_values)
    except:
        return 0


@metric
def p10(results, relevant, n=10):
    """Precision at N"""
    return len(relevant_results(results, relevant, n))/n


def calculate_metric(key, results, relevant):
    return metrics[key](results, relevant)


params = len(argv) - 1
number_queries = 7
save_file_prefix = 'm3/simple_schema'
qrels_file_infix = ''
if params >= 1:
    number_queries = int(argv[1])
    if params >= 2:
        save_file_prefix = argv[2]

        if params >= 3:
            qrels_file_infix = argv[3]

for query_n in range(1, number_queries+1):
    QRELS_FILE = 'solr/qrels/q' + \
        str(query_n) + '_' + qrels_file_infix + 'qrel.txt'
    QUERY_URL_FILE = 'solr/queries/q'+str(query_n)+'_query.txt'

    # Read qrels to extract relevant documents
    relevant = list(map(lambda el: el.strip(), open(QRELS_FILE).readlines()))
    # Get query results from Solr instance
    results = requests.get(open(QUERY_URL_FILE).readline()).json()[
        'response']['docs']

    # print(results)
    # print('\n\n\n\n\n')
    # print(relevant)

    # Define metrics to be calculated
    evaluation_metrics = {
        'ap': 'Average Precision',
        'p10': 'Precision at 10 (P@10)'
    }

    # Calculate all metrics and export results as LaTeX table
    df = pd.DataFrame([[evaluation_metrics[m] for m in evaluation_metrics]] +
                      [[calculate_metric(m, results, relevant)
                        for m in evaluation_metrics]]
                      )
    df.to_csv(f"solr/results/{save_file_prefix}metrics_results_" +
              str(query_n)+'.csv', index=False, header=False)

    # Relevance Table
    df = pd.DataFrame([['Document', 'Relevance']] +
                      [[i+1, results[i]['id'] in relevant]
                          for i in range(len(results))]
                      )
    df.to_csv(f"solr/results/{save_file_prefix}relevance_results_" +
              str(query_n)+'.csv', index=False, header=False)

    # PRECISION-RECALL CURVE
    # Calculate precision and recall values as we move down the ranked list
    precision_values = [
        len(relevant_results(results, relevant, idx)) / idx
        for idx, _ in enumerate(results, start=1)
    ]

    recall_values = [
        len(relevant_results(results, relevant, idx)) / len(relevant)
        for idx, _ in enumerate(results, start=1)
    ]

    precision_recall_match = [(k, v)
                              for k, v in zip(recall_values, precision_values)]
    recall_precision_interpolated = []
    for i in np.arange(0.0, 1.1, 0.1):
        try:
            recall_precision_interpolated.append(
                (i, max([v for k, v in precision_recall_match if k >= i])))
        except:
            recall_precision_interpolated.append((i, 0))

    # Acctually I didn't what this was doing, but it was messing up the curve the way the teacher wanted it
    """
    # Extend recall_values to include traditional steps for a better curve (0.1, 0.2 ...)
    recall_values.extend([step for step in np.arange(0.1, 1.1, 0.1) if step not in recall_values])
    recall_values = sorted(set(recall_values))

    # Extend matching dict to include these new intermediate steps
    for idx, step in enumerate(recall_values):
        if step not in precision_recall_match:
            if recall_values[idx-1] in precision_recall_match:
                precision_recall_match[step] = precision_recall_match[recall_values[idx-1]]
            else:
                precision_recall_match[step] = precision_recall_match[recall_values[idx+1]]
    """

    disp = PrecisionRecallDisplay(precision=np.array(
        [v for k, v in recall_precision_interpolated]), recall=np.array([k for k, v in recall_precision_interpolated]))
    disp.plot()
    plt.ylim(0, 1.05)
    plt.title('Precision-Recall Curve for query '+str(query_n))
    plt.savefig(
        f"solr/results/{save_file_prefix}precision_recall_"+str(query_n)+'.svg')
