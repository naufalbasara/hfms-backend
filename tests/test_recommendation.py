import requests, pandas as pd, numpy as np, os, matplotlib.pyplot as plt
import re, time, json
from collections import Counter
from scipy import stats

import psutil
import os
import time

from pprint import pprint

def get_rootdir() -> str:
    cwd = os.path.abspath(os.getcwd())
    end = re.search(r'hfms-backend', cwd).end()
    rootdir = cwd[:end]

    return rootdir

def statistics_test(case='positive'):
    # fetching_result = {'riskReduction': [],'currentRisk': [], 'riskAfterRecommendation': []}
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
    for index in range(50):
        lifestyle = data.iloc[index, :22].to_dict()
        characteristic = data.iloc[index, 22:].to_dict()
        
        data_json = {**lifestyle, **characteristic}
        res = requests.post(endpoint, json=data_json).json()

        ls_res = res['recommendationResult']['lifestyle']
        currentRisk = res['recommendationResult']['currentRisk']
        riskReduction = res['recommendationResult']['riskReduction']
        riskAfter = res['recommendationResult']['riskAfterRecommendation']
        for col, ls in ls_res.items():
            code = ls['codeValue']
            code = float(code) if code in possible_values[col] else int(code)
            if not ls['changeStatus']:
                continue

            if col not in fetching_result:
                fetching_result[col] = []

            fetching_result[col].append(code)
    pd.DataFrame(fetching_result).to_csv('test_result3/recommendation_result.csv')

    # plot the result
    for col in fetching_result.keys():
        labels, counts = np.unique(sorted(fetching_result[col]), return_counts=True)
        print(col)
        print(labels, counts)

        plt.figure(figsize=(10,6))
        plt.bar(labels, counts, align='center')
        plt.xlabel('Recommendation Interval')
        plt.ylabel('Frequency')
        plt.title(f'{ls_res[col]["description"]}')
        plt.tight_layout()
        plt.savefig(os.path.join(base_path, f'tests/test_result3/{case}_{col}.png'))
        plt.close()

    return

def statistics():
    version = 3
    base_path = get_rootdir()
    data_path = os.path.join(base_path, 'tests/test_data/')

    ls_path = os.path.join(base_path, f'flaskr/optimization_model/metadata/v{version}/v{version}_lifestyle_description.json')
    with open(ls_path,'r') as json_file:
        ls_res = json.load(json_file)

    pv_path = os.path.join(base_path, f'flaskr/optimization_model/metadata/v{version}/v{version}_variable_discrete_value.json')
    with open(pv_path,'r') as json_file:
        possible_values = json.load(json_file)

    fetching_result = pd.read_csv(os.path.join(data_path, 'recommendation_result.csv'))

    try:
        fetching_result = fetching_result.drop(columns='Unnamed: 0')
    except:
        pass

    # plot the result
    for col in fetching_result.columns:
        labels, counts = np.unique(sorted(fetching_result[col].to_list()), return_counts=True)
        print(col, labels)
        try:
            labels = [*map(lambda x: possible_values[col][str(int(x))], labels)]
        except:
            labels = [*map(lambda x: possible_values[col][str(float(x))], labels)]
        print(labels, counts)

        plt.figure(figsize=(8,6))
        plt.bar(labels, counts, align='center')
        plt.xlabel('Recommendation Interval')
        plt.ylabel('Frequency')
        plt.title(f'{ls_res[col]}')
        plt.tight_layout()
        plt.savefig(os.path.join(base_path, f'tests/test_result/{col}.png'))
        plt.close()

    return


def significance_test():
    pv_path = os.path.join(base_path, f'flaskr/optimization_model/metadata/v{version}/v{version}_variable_discrete_value.json')
    with open(pv_path,'r') as json_file:
        possible_values = json.load(json_file)
    data = pd.read_csv(os.path.join(data_path, 'recommendation_result2.csv'))
    risk_changes = data['riskReduction'].to_numpy()
    data.to_excel(os.path.join(data_path, 'res.xlsx'))

    data['currentRisk'].plot(kind='hist')
    plt.show()

    # Perform paired t-test
    t_statistic, p_value = stats.ttest_1samp(risk_changes, 0)
    wt_statistic, wp_value = stats.wilcoxon(data['currentRisk'], data['riskAfterRecommendation'])

    # Significance level
    alpha = 0.05

    print(f'Paired T-Test => T-statistic: {t_statistic}, P-value: {p_value}')
    if p_value < alpha:
        print("The change in risk is statistically significant.")
    else:
        print("The change in risk is not statistically significant.")

    print(f'WILCOXON => T-statistic: {wt_statistic}, P-value: {wp_value}')
    if p_value < alpha:
        print("The change in risk is statistically significant.")
    else:
        print("The change in risk is not statistically significant.")
    
    return

if __name__ == '__main__':
    # get all the characteristic and lifestyle data of 30-50 patients from dataset
    start_all_process = time.time()
    version = 3
    base_path = get_rootdir()
    data_path = os.path.join(base_path, 'tests/test_data/')
    result_path = os.path.join(base_path, 'tests/test_result/')
    
    # loop through all the data and recommend lifestyle
    # request to endpoint http://127.0.0.1:5000/{version}/recommendations/
    endpoint = f'http://127.0.0.1:5000/v{version}/recommendations/'
    stats_start = time.time()
    print("Start Statistics Testing")
    # statistics_test(case='positive')
    # statistics_test(case='negative')
    # significance_test()
    statistics()

    # pv_path = os.path.join(base_path, f'flaskr/optimization_model/metadata/v{version}/v{version}_variable_discrete_value.json')
    # ls_path = os.path.join(base_path, f'flaskr/optimization_model/metadata/v{version}/v{version}_lifestyle_description.json')
    # with open(pv_path,'r') as json_file:
    #     possible_values = json.load(json_file)

    # with open(ls_path,'r') as json_file:
    #     ls_desc = json.load(json_file)

    # res = pd.read_csv(os.path.join(result_path, 'recommendation_result.csv'))
    # res = res.drop(columns=['Unnamed: 0'])
    
    # print(res.head())
    # for col in res.columns.tolist():
    #     labels, counts = np.unique(sorted(res[col].tolist()), return_counts=True)
    #     labels.astype(int)
    #     # int(value) if str(int(value)) in self.__genes[ls_component] else float(value)
    #     labels = [*map(lambda x: possible_values[col][str(int(x)) if str(int(x)) in possible_values[col] else str(float(x))], labels)]
    #     print(labels, counts)
    #     plt.figure(figsize=(12,8))
    #     plt.bar(labels, counts, align='center')
    #     plt.xlabel('Recommendation Interval')
    #     plt.ylabel('Frequency')
    #     plt.title(f'{ls_desc[col]}')
    #     plt.tight_layout()
    #     plt.savefig(os.path.join(base_path, f'tests/test_result4/_{col}.png'))
    #     plt.close()
    
    print(f"Recommendation testing done in {time.time() - start_all_process} s")