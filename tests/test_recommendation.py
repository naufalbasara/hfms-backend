import requests, pandas as pd, numpy as np, os, matplotlib.pyplot as plt
import re, time, json
from collections import Counter

from pprint import pprint

def get_rootdir() -> str:
    cwd = os.path.abspath(os.getcwd())
    end = re.search(r'hfms-backend', cwd).end()
    rootdir = cwd[:end]

    return rootdir

def statistics_test(case='positive'):
    fetching_result = {}
    pv_path = os.path.join(base_path, f'flaskr/optimization_model/metadata/v{version}/v{version}_variable_discrete_value.json')
    with open(pv_path,'r') as json_file:
        possible_values = json.load(json_file)
    data = pd.read_csv(os.path.join(data_path, 'positive_case.csv' if case=='positive' else 'negative_case.csv'))

    try:
        data = data.set_index('SEQN', drop=True)
        data['Quest16_MCQ160B'] = data['Quest16_MCQ160B'].astype(int)
    except Exception as error:
        print("Error", error)

    ### for positive cases ###
    for index in range(25):
        lifestyle = data.iloc[index, :22].to_dict()
        characteristic = data.iloc[index, 22:].to_dict()
        
        data_json = {**lifestyle, **characteristic}
        res = requests.post(endpoint, json=data_json)

        ls_res = res.json()['recommendationResult']['lifestyle']
        for col, ls in ls_res.items():
            code = ls['codeValue']
            code = float(code) if code in possible_values[col] else int(code)
            if not ls['changeStatus']:
                continue

            if col not in fetching_result:
                fetching_result[col] = []

            fetching_result[col].append(ls['recommendedValueInterval'])

    # plot the result
    for col in fetching_result.keys():
        # bins = [int(el[0]) for el in sorted([*possible_values[col].items()], key=lambda x: x[0])]
        # bins_str = [el[1] for el in sorted([*possible_values[col].items()], key=lambda x: x[0])]
        # print(bins)
        # print(bins_str)
        labels, counts = np.unique(fetching_result[col], return_counts=True)

        plt.figure()
        plt.bar(labels, counts, align='center')
        plt.xlabel('Recommendation Interval')
        plt.ylabel('Frequency')
        plt.title(f'{ls_res[col]["description"]} Recommendation Frequency')
        plt.tight_layout()
        plt.savefig(os.path.join(base_path, f'tests/test_result/{case}_{col}.png'))
        plt.close()

    return

def parameter_test():
    return

if __name__ == '__main__':
    # get all the characteristic and lifestyle data of 30-50 patients from dataset
    start_all_process = time.time()
    version = 3
    base_path = get_rootdir()
    data_path = os.path.join(base_path, 'tests/test_data/')
    
    # loop through all the data and recommend lifestyle
    # request to endpoint http://127.0.0.1:5000/{version}/recommendations/
    endpoint = f'http://127.0.0.1:5000/v{version}/recommendations/'
    stats_start = time.time()
    print("Start Statistics Testing")
    statistics_test(case='positive')
    statistics_test(case='negative')
    print(f"Start Statistics Testing, done in {time.time() - stats_start} s")

    # parameter_test()
    
    print(f"Recommendation testing done in {time.time() - start_all_process} s")